from fastapi import APIRouter
from src.processor import BatchProcessor

router = APIRouter()
processor = BatchProcessor()


@router.post("/validate/{batch_id}")
def validate_batch(batch_id: str):
    """Run validation on all unvalidated programs in a batch."""
    result = processor.process_batch(batch_id)
    return result
