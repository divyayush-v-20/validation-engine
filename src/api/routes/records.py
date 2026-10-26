from fastapi import APIRouter, Query
from src.db.dynamo import DynamoDBClient

router = APIRouter()
db = DynamoDBClient()


@router.get("/records/{batch_id}")
def list_records(batch_id: str):
    """List all program records in a batch."""
    programs = db.get_all_programs(batch_id)
    return {
        "batchId": batch_id,
        "total": len(programs),
        "records": [item.get("data", {}) for item in programs],
    }


@router.get("/records/{batch_id}/{tms_id}")
def get_record(batch_id: str, tms_id: str):
    """Get a single program record."""
    item = db.get_program(batch_id, tms_id)
    if not item:
        return {"error": "Record not found"}
    return {
        "record": item.get("data", {}),
        "validationResults": item.get("validationResults"),
        "validatedAt": item.get("validatedAt"),
    }
