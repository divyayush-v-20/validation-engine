"""Load seed records into DynamoDB."""
import json
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db.dynamo import DynamoDBClient


def load(batch_id: str = "seed-001", records_file: str = "seed_data/records.json"):
    db = DynamoDBClient()

    # Create table if needed (for local dev)
    try:
        db.create_table_if_not_exists()
    except Exception as e:
        print(f"Table setup: {e}")

    # Load records
    with open(records_file) as f:
        records = json.load(f)

    print(f"Loading {len(records)} records into batch '{batch_id}'...")
    count = db.put_programs_batch(batch_id, records)
    print(f"Loaded {count} program records.")

    # Initialize status row
    try:
        db.init_record_status(batch_id)
        print("Initialized status row.")
    except Exception:
        print("Status row already exists.")

    print("Done!")


if __name__ == "__main__":
    batch = sys.argv[1] if len(sys.argv) > 1 else "seed-001"
    load(batch)
