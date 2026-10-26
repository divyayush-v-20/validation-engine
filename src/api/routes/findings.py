from fastapi import APIRouter, Query
from typing import Optional
from src.db.dynamo import DynamoDBClient

router = APIRouter()
db = DynamoDBClient()


@router.get("/findings/{batch_id}")
def get_findings(
    batch_id: str,
    field: Optional[str] = Query(None, description="Filter by field: title, genre, duration, etc."),
    severity: Optional[str] = Query(None, description="Filter by severity: high, medium, low"),
):
    """Get all validation findings for a batch, with optional filters."""
    # Get the status row which has aggregated failures
    status = db.get_record_status(batch_id)
    if not status:
        return {"batchId": batch_id, "findings": {}, "total": 0}

    failure_data = status.get("failure", {})
    total_count = failure_data.get("totalCount", 0)

    # Build findings by field
    findings = {}
    skip_keys = {"totalCount"}
    for key, value in failure_data.items():
        if key in skip_keys:
            continue
        if isinstance(value, list) and value:
            if field and key != field:
                continue
            findings[key] = value

    # Count total issues across all fields
    total_issues = sum(len(v) for v in findings.values())

    return {
        "batchId": batch_id,
        "totalFailedRecords": total_count,
        "totalIssues": total_issues,
        "findings": findings,
    }


@router.get("/findings/{batch_id}/record/{tms_id}")
def get_record_findings(batch_id: str, tms_id: str):
    """Get validation findings for a specific record."""
    item = db.get_program(batch_id, tms_id)
    if not item:
        return {"error": "Record not found"}

    validation = item.get("validationResults")
    if not validation:
        return {"tmsId": tms_id, "validated": False, "message": "Not yet validated"}

    return validation
