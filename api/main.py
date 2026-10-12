"""Fictional hotel request board backed by DynamoDB Local."""

import os
from datetime import datetime, timezone
from uuid import uuid4

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError, EndpointConnectionError
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

TABLE = "hotel_requests"
HOTEL = "mirador-azul"
STATUSES = ("new", "contacted", "confirmed", "closed")

app = FastAPI(title="Hotel Ops API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5178", "http://localhost:5178"],
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Content-Type"],
)


def table():
    endpoint = os.getenv("DYNAMODB_ENDPOINT", "http://127.0.0.1:8008")
    resource = boto3.resource(
        "dynamodb",
        endpoint_url=endpoint,
        region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "local"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "local"),
    )
    try:
        existing = [item.name for item in resource.tables.all()]
        if TABLE not in existing:
            resource.create_table(
                TableName=TABLE,
                KeySchema=[{"AttributeName": "hotel_id", "KeyType": "HASH"}, {"AttributeName": "request_id", "KeyType": "RANGE"}],
                AttributeDefinitions=[
                    {"AttributeName": "hotel_id", "AttributeType": "S"},
                    {"AttributeName": "request_id", "AttributeType": "S"},
                    {"AttributeName": "hotel_status", "AttributeType": "S"},
                    {"AttributeName": "created_at", "AttributeType": "S"},
                ],
                GlobalSecondaryIndexes=[{
                    "IndexName": "hotel-status-created",
                    "KeySchema": [{"AttributeName": "hotel_status", "KeyType": "HASH"}, {"AttributeName": "created_at", "KeyType": "RANGE"}],
                    "Projection": {"ProjectionType": "ALL"},
                }],
                BillingMode="PAY_PER_REQUEST",
            ).wait_until_exists()
        return resource.Table(TABLE)
    except (EndpointConnectionError, ClientError) as exc:
        raise HTTPException(503, "DynamoDB Local is unavailable; start it on port 8008") from exc


class NewRequest(BaseModel):
    guest: str = Field(min_length=2, max_length=80)
    service: str = Field(min_length=2, max_length=80)
    arrival: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    note: str = Field(default="", max_length=240)


class StatusUpdate(BaseModel):
    status: str
    version: int = Field(ge=1)


@app.get("/api/health")
def health():
    table().load()
    return {"ok": True, "storage": "DynamoDB Local"}


@app.get("/api/requests")
def list_requests(status: str | None = Query(default=None)):
    if status is not None and status not in STATUSES:
        raise HTTPException(422, "Unknown status")
    db = table()
    if status:
        result = db.query(
            IndexName="hotel-status-created",
            KeyConditionExpression=Key("hotel_status").eq(f"{HOTEL}#{status}"),
            ScanIndexForward=False,
            Limit=100,
        )
    else:
        result = db.query(KeyConditionExpression=Key("hotel_id").eq(HOTEL), Limit=100)
    return sorted(result["Items"], key=lambda item: item["created_at"], reverse=True)


@app.post("/api/requests", status_code=201)
def create_request(payload: NewRequest):
    if not payload.guest.strip() or not payload.service.strip():
        raise HTTPException(422, "Guest and service cannot be blank")
    try:
        datetime.strptime(payload.arrival, "%Y-%m-%d")
    except ValueError as exc:
        raise HTTPException(422, "Invalid arrival date") from exc
    item = {
        "hotel_id": HOTEL,
        "request_id": str(uuid4()),
        "guest": payload.guest.strip(),
        "service": payload.service.strip(),
        "arrival": payload.arrival,
        "note": payload.note.strip(),
        "status": "new",
        "hotel_status": f"{HOTEL}#new",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "version": 1,
    }
    table().put_item(Item=item, ConditionExpression="attribute_not_exists(request_id)")
    return item


@app.patch("/api/requests/{request_id}")
def update_status(request_id: str, payload: StatusUpdate):
    if payload.status not in STATUSES:
        raise HTTPException(422, "Unknown status")
    try:
        response = table().update_item(
            Key={"hotel_id": HOTEL, "request_id": request_id},
            UpdateExpression="SET #s = :status, hotel_status = :hotel_status, version = version + :one",
            ConditionExpression="attribute_exists(request_id) AND version = :expected",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={
                ":status": payload.status,
                ":hotel_status": f"{HOTEL}#{payload.status}",
                ":one": 1,
                ":expected": payload.version,
            },
            ReturnValues="ALL_NEW",
        )
        return response["Attributes"]
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise HTTPException(409, "Request changed or does not exist; refresh the board") from exc
        raise
