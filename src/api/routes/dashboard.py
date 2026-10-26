from fastapi import APIRouter
from src.db.dynamo import DynamoDBClient

router = APIRouter()
db = DynamoDBClient()


@router.get("/dashboard/{batch_id}")
def get_dashboard(batch_id: str):
    """Dashboard summary for a batch."""
    # Get all programs
    programs = db.get_all_programs(batch_id)
    total_records = len(programs)

    # Count validated vs unvalidated
    validated = [p for p in programs if p.get("validationResults")]
    unvalidated = total_records - len(validated)

    # Get status row
    status = db.get_record_status(batch_id)
    success_count = 0
    failure_count = 0
    findings_by_field = {}
    findings_by_severity = {"high": 0, "medium": 0, "low": 0}

    if status:
        success_ids = status.get("success", {}).get("tmsIds", [])
        success_count = len(success_ids)
        failure_data = status.get("failure", {})
        failure_count = failure_data.get("totalCount", 0)

        # Count findings by field
        skip_keys = {"totalCount"}
        for key, value in failure_data.items():
            if key in skip_keys:
                continue
            if isinstance(value, list):
                findings_by_field[key] = len(value)
                # Approximate severity from field name mapping
                for issue in value:
                    sev = issue.get("severity", "high") if isinstance(issue, dict) else "high"
                    if sev in findings_by_severity:
                        findings_by_severity[sev] += 1
                    else:
                        findings_by_severity["high"] += 1

    return {
        "batchId": batch_id,
        "totalRecords": total_records,
        "validated": len(validated),
        "unvalidated": unvalidated,
        "successCount": success_count,
        "failureCount": failure_count,
        "findingsByField": findings_by_field,
        "findingsBySeverity": findings_by_severity,
    }


@router.get("/dashboard/{batch_id}/status")
def get_batch_status(batch_id: str):
    """Get the raw record_status row."""
    status = db.get_record_status(batch_id)
    if not status:
        return {"error": "No status found for this batch"}

    # Remove DynamoDB keys for cleaner output
    return {
        "success": status.get("success", {}),
        "failure": status.get("failure", {}),
    }
