"""Idempotent fictional records for a useful first run."""

from datetime import datetime, timezone

from botocore.exceptions import ClientError

from api.main import HOTEL, table

samples = [
    ("seed-001", "María López", "Airport transfer", "2026-11-04", "Window seat requested", "new"),
    ("seed-002", "Oliver Grant", "Sunset dinner", "2026-11-08", "Vegetarian menu", "contacted"),
    ("seed-003", "Ana Morales", "Spa appointment", "2026-11-12", "Two guests", "confirmed"),
    ("seed-004", "Sofia Rivera", "Private excursion", "2026-11-15", "Morning departure", "new"),
    ("seed-005", "James Miller", "Late checkout", "2026-11-18", "Departure at 15:00", "closed"),
]


def seed():
    db = table()
    for index, (request_id, guest, service, arrival, note, status) in enumerate(samples):
        try:
            db.put_item(
                Item={
                    "hotel_id": HOTEL, "request_id": request_id, "guest": guest,
                    "service": service, "arrival": arrival, "note": note,
                    "status": status, "hotel_status": f"{HOTEL}#{status}",
                    "created_at": datetime(2026, 10, 1 + index, 12, 0, tzinfo=timezone.utc).isoformat(),
                    "version": 1,
                },
                ConditionExpression="attribute_not_exists(request_id)",
            )
        except ClientError as exc:
            if exc.response["Error"]["Code"] != "ConditionalCheckFailedException":
                raise


if __name__ == "__main__":
    seed()
    print("Fictional requests ready")
