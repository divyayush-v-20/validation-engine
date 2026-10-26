import boto3
from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime, timezone
from typing import Optional
import logging

from src.config import settings

logger = logging.getLogger(__name__)


class DynamoDBClient:
    """Single-table DynamoDB client for the validation engine."""

    def __init__(self, table_name: Optional[str] = None):
        self.dynamodb = boto3.resource("dynamodb", region_name=settings.AWS_REGION)
        self.table = self.dynamodb.Table(table_name or settings.DYNAMODB_TABLE_NAME)

    # ---- Key helpers ----

    @staticmethod
    def batch_pk(batch_id: str) -> str:
        return f"BATCH#{batch_id}"

    @staticmethod
    def program_sk(tms_id: str) -> str:
        return f"PROGRAM#{tms_id}"

    STATUS_SK = "STATUS"

    # ---- Program rows ----

    def put_program(self, batch_id: str, program: dict) -> None:
        """Insert/overwrite a single program record."""
        item = {
            "PK": self.batch_pk(batch_id),
            "SK": self.program_sk(program["tmsId"]),
            "recordType": "PROGRAM",
            "data": program,
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }
        self.table.put_item(Item=item)

    def put_programs_batch(self, batch_id: str, programs: list[dict]) -> int:
        """Batch write multiple program records. Returns count written."""
        count = 0
        with self.table.batch_writer() as writer:
            for program in programs:
                item = {
                    "PK": self.batch_pk(batch_id),
                    "SK": self.program_sk(program["tmsId"]),
                    "recordType": "PROGRAM",
                    "data": program,
                    "createdAt": datetime.now(timezone.utc).isoformat(),
                }
                writer.put_item(Item=item)
                count += 1
        return count

    def get_program(self, batch_id: str, tms_id: str) -> Optional[dict]:
        """Fetch a single program by batch + tmsId."""
        response = self.table.get_item(
            Key={"PK": self.batch_pk(batch_id), "SK": self.program_sk(tms_id)}
        )
        return response.get("Item")

    def get_all_programs(self, batch_id: str) -> list[dict]:
        """Fetch all program rows in a batch."""
        response = self.table.query(
            KeyConditionExpression=Key("PK").eq(self.batch_pk(batch_id))
            & Key("SK").begins_with("PROGRAM#")
        )
        return response.get("Items", [])

    def get_unvalidated_programs(self, batch_id: str) -> list[dict]:
        """Fetch programs that don't have validation_results yet."""
        response = self.table.query(
            KeyConditionExpression=Key("PK").eq(self.batch_pk(batch_id))
            & Key("SK").begins_with("PROGRAM#"),
            FilterExpression=Attr("validationResults").not_exists()
            | Attr("validationResults").eq(None),
        )
        return response.get("Items", [])

    def update_program_validation(self, batch_id: str, tms_id: str, validation_result: dict) -> None:
        """Stamp validation results onto a program row."""
        self.table.update_item(
            Key={"PK": self.batch_pk(batch_id), "SK": self.program_sk(tms_id)},
            UpdateExpression="SET validationResults = :vr, validatedAt = :va",
            ExpressionAttributeValues={
                ":vr": validation_result,
                ":va": datetime.now(timezone.utc).isoformat(),
            },
        )

    # ---- Status row ----

    def get_record_status(self, batch_id: str) -> Optional[dict]:
        """Fetch the STATUS row for a batch."""
        response = self.table.get_item(
            Key={"PK": self.batch_pk(batch_id), "SK": self.STATUS_SK}
        )
        return response.get("Item")

    def init_record_status(self, batch_id: str) -> None:
        """Create an empty status row if it doesn't exist."""
        self.table.put_item(
            Item={
                "PK": self.batch_pk(batch_id),
                "SK": self.STATUS_SK,
                "recordType": "STATUS",
                "success": {"tmsIds": []},
                "failure": {"totalCount": 0},
                "updatedAt": datetime.now(timezone.utc).isoformat(),
            },
            ConditionExpression="attribute_not_exists(PK)",
        )

    def add_success(self, batch_id: str, tms_id: str) -> None:
        """Append a tmsId to the success list in the status row."""
        self.table.update_item(
            Key={"PK": self.batch_pk(batch_id), "SK": self.STATUS_SK},
            UpdateExpression="SET success.tmsIds = list_append(if_not_exists(success.tmsIds, :empty), :tid), updatedAt = :ua",
            ExpressionAttributeValues={
                ":tid": [tms_id],
                ":empty": [],
                ":ua": datetime.now(timezone.utc).isoformat(),
            },
        )

    def add_failure(self, batch_id: str, issues_by_field: dict) -> None:
        """Increment failure totalCount and append field-wise issues to the status row.

        issues_by_field looks like:
        {
            "title": [{"tmsId": "...", "failedRule": "...", "correctionSuggestion": "..."}],
            "genre": [...],
            ...
        }
        """
        # Build the update expression dynamically based on which fields have issues
        update_parts = [
            "SET failure.totalCount = if_not_exists(failure.totalCount, :zero) + :one",
            "updatedAt = :ua",
        ]
        attr_values = {
            ":zero": 0,
            ":one": 1,
            ":ua": datetime.now(timezone.utc).isoformat(),
            ":empty": [],
        }

        for field_name, issues in issues_by_field.items():
            if issues:
                safe_name = field_name.replace(".", "_")
                placeholder = f":f_{safe_name}"
                update_parts.append(
                    f"failure.{field_name} = list_append(if_not_exists(failure.{field_name}, :empty), {placeholder})"
                )
                attr_values[placeholder] = issues

        self.table.update_item(
            Key={"PK": self.batch_pk(batch_id), "SK": self.STATUS_SK},
            UpdateExpression=update_parts[0] + ", " + ", ".join(update_parts[1:]),
            ExpressionAttributeValues=attr_values,
        )

    # ---- Table management ----

    def create_table_if_not_exists(self) -> None:
        """Create the DynamoDB table for local dev / first-time setup."""
        existing = [t.name for t in self.dynamodb.tables.all()]
        if self.table.name in existing:
            logger.info(f"Table {self.table.name} already exists")
            return

        self.dynamodb.create_table(
            TableName=self.table.name,
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        self.table.wait_until_exists()
        logger.info(f"Created table {self.table.name}")
