import logging
from src.db.dynamo import DynamoDBClient
from src.rules.engine import ValidationEngine

logger = logging.getLogger(__name__)


class BatchProcessor:
    """Fetches unvalidated programs from a batch, runs rules, updates DB."""

    def __init__(self, db: DynamoDBClient = None, engine: ValidationEngine = None):
        self.db = db or DynamoDBClient()
        self.engine = engine or ValidationEngine()

    def process_batch(self, batch_id: str) -> dict:
        """Process all unvalidated programs in a batch.

        Returns summary: {total, success_count, failure_count, results: [...]}
        """
        # Ensure status row exists
        try:
            self.db.init_record_status(batch_id)
        except Exception:
            pass  # Already exists (ConditionalCheckFailedException)

        # Fetch unvalidated programs
        unvalidated = self.db.get_unvalidated_programs(batch_id)
        logger.info(f"Batch {batch_id}: found {len(unvalidated)} unvalidated programs")

        if not unvalidated:
            return {
                "batchId": batch_id,
                "total": 0,
                "successCount": 0,
                "failureCount": 0,
                "results": [],
            }

        results = []
        success_count = 0
        failure_count = 0

        for item in unvalidated:
            program_data = item.get("data", {})
            tms_id = program_data.get("tmsId", "unknown")

            # Run validation
            result = self.engine.validate_record(program_data)
            results.append(result)

            # Update the program row with validation results
            self.db.update_program_validation(batch_id, tms_id, result)

            # Update the status row
            if result["success"]:
                self.db.add_success(batch_id, tms_id)
                success_count += 1
            else:
                # Build field-wise issues dict for the status row
                issues_for_status = {}
                for field_name, field_issues in result.get("issues", {}).items():
                    if field_issues:
                        issues_for_status[field_name] = field_issues
                self.db.add_failure(batch_id, issues_for_status)
                failure_count += 1

        logger.info(
            f"Batch {batch_id}: processed {len(results)} programs — "
            f"{success_count} success, {failure_count} failures"
        )

        return {
            "batchId": batch_id,
            "total": len(results),
            "successCount": success_count,
            "failureCount": failure_count,
            "results": results,
        }
