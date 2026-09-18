import os
import uuid
import datetime
from typing import Optional
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from sqlalchemy import (
create_engine,
Column,
String,
Float,
Boolean,
DateTime,
Text
)
from sqlalchemy.orm import declarative_base, sessionmaker
============================================================
1. DATABASE
============================================================
DATABASE_URL = os.getenv(
"DATABASE_URL",
"sqlite:///./emmbio.db"
)
Render/Postgres URLs sometimes begin with postgres://
SQLAlchemy expects postgresql://
if DATABASE_URL.startswith("postgres://"):
DATABASE_URL = DATABASE_URL.replace(
"postgres://",
"postgresql://",
1
)
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
connect_args = {
"check_same_thread": False
}
engine = create_engine(
DATABASE_URL,
connect_args=connect_args,
pool_pre_ping=True
)
SessionLocal = sessionmaker(
autocommit=False,
autoflush=False,
bind=engine,
expire_on_commit=False
)
Base = declarative_base()
def gen_id(prefix):
return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"
============================================================
2. DATABASE MODELS
============================================================
class Client(Base):
__tablename__ = "clients"

id = Column(
    String,
    primary_key=True
)

name = Column(
    String,
    nullable=False
)

email = Column(
    String,
    nullable=False
)

phone = Column(
    String,
    nullable=True
)

date_of_birth = Column(
    String,
    nullable=True
)

address = Column(
    Text,
    nullable=True
)

type = Column(
    String,
    default="INDIVIDUAL"
)

wallet_balance = Column(
    Float,
    default=0.0
)

created_at = Column(
    DateTime,
    default=datetime.datetime.utcnow
)
class Rider(Base):
__tablename__ = "riders"

id = Column(
    String,
    primary_key=True
)

name = Column(
    String,
    nullable=False
)

date_of_birth = Column(
    String,
    nullable=False
)

nin = Column(
    String,
    nullable=False
)

motorcycle_serial_number = Column(
    String,
    nullable=False
)

motorcycle_license = Column(
    String,
    nullable=False
)

phone = Column(
    String,
    nullable=False
)

address = Column(
    Text,
    nullable=False
)

guarantor_name = Column(
    String,
    nullable=False
)

guarantor_phone = Column(
    String,
    nullable=False
)

verified = Column(
    Boolean,
    default=False
)

available = Column(
    Boolean,
    default=True
)

current_lat = Column(
    Float,
    nullable=True
)

current_lng = Column(
    Float,
    nullable=True
)

created_at = Column(
    DateTime,
    default=datetime.datetime.utcnow
)
class Shipment(Base):
__tablename__ = "shipments"

id = Column(
    String,
    primary_key=True
)

client_id = Column(
    String,
    nullable=False
)

rider_id = Column(
    String,
    nullable=True
)

pickup_address = Column(
    Text,
    nullable=False
)

pickup_lat = Column(
    Float,
    nullable=False
)

pickup_lng = Column(
    Float,
    nullable=False
)

dropoff_address = Column(
    Text,
    nullable=False
)

dropoff_lat = Column(
    Float,
    nullable=False
)

dropoff_lng = Column(
    Float,
    nullable=False
)

price = Column(
    Float,
    default=0.0
)

status = Column(
    String,
    default="NEW"
)

created_at = Column(
    DateTime,
    default=datetime.datetime.utcnow
)

accepted_at = Column(
    DateTime,
    nullable=True
)

completed_at = Column(
    DateTime,
    nullable=True
)
class Transaction(Base):
__tablename__ = "transactions"

id = Column(
    String,
    primary_key=True
)

client_id = Column(
    String,
    nullable=False
)

type = Column(
    String,
    nullable=False
)

amount = Column(
    Float,
    nullable=False
)

request_id = Column(
    String,
    nullable=True
)

created_at = Column(
    DateTime,
    default=datetime.datetime.utcnow
)
Base.metadata.create_all(
bind=engine
)
============================================================
3. FASTAPI
============================================================
app = FastAPI(
title="Emmbio Logistics API",
version="2.0.0"
)
app.add_middleware(
CORSMiddleware,
allow_origins=["*"],

allow_credentials=True,

allow_methods=["*"],

allow_headers=["*"]
)
============================================================
4. PYDANTIC REQUEST MODELS
============================================================
class ClientRegistration(BaseModel):
name: str

email: EmailStr

phone: str

date_of_birth: str

address: str
class RiderRegistration(BaseModel):
name: str

date_of_birth: str

nin: str

motorcycle_serial_number: str

motorcycle_license: str

phone: str

address: str

guarantor_name: str

guarantor_phone: str
class RiderLocation(BaseModel):
rider_id: str

lat: float

lng: float
class AcceptRequest(BaseModel):
rider_id: str

request_id: str
class ShipmentCreate(BaseModel):
client_id: str

pickup_lat: float

pickup_lng: float

dropoff_lat: float

dropoff_lng: float

pickup_address: str

dropoff_address: str
============================================================
5. HOME
============================================================
@app.get("/")
def home():
return {
    "status": "Emmbio Logistics API is RUNNING",
    "version": "2.0.0"
}
@app.get("/health")
def health():
return {
    "status": "healthy"
}
============================================================
6. CLIENT REGISTRATION
============================================================
@app.post("/api/v1/clients/register")
def register_client(
data: ClientRegistration
):
db = SessionLocal()

try:

    existing = (
        db.query(Client)
        .filter(
            Client.email == data.email
        )
        .first()
    )

    if existing:

        return {
            "client_id": existing.id,
            "name": existing.name,
            "message": "Client already registered",
            "wallet": existing.wallet_balance
        }


    client = Client(

        id=gen_id("CL"),

        name=data.name,

        email=str(data.email),

        phone=data.phone,

        date_of_birth=data.date_of_birth,

        address=data.address,

        type="INDIVIDUAL",

        wallet_balance=0.0
    )


    db.add(client)

    db.commit()

    db.refresh(client)


    return {

        "client_id": client.id,

        "name": client.name,

        "email": client.email,

        "phone": client.phone,

        "wallet": client.wallet_balance,

        "message": "Client registered successfully"
    }

finally:

    db.close()
============================================================
7. GET CLIENT
============================================================
@app.get("/api/v1/clients/{client_id}")
def get_client(client_id: str):
db = SessionLocal()

try:

    client = (
        db.query(Client)
        .filter(Client.id == client_id)
        .first()
    )

    if not client:

        raise HTTPException(
            status_code=404,
            detail="Client not found"
        )


    return {

        "client_id": client.id,

        "name": client.name,

        "email": client.email,

        "phone": client.phone,

        "date_of_birth": client.date_of_birth,

        "address": client.address,

        "wallet": client.wallet_balance
    }

finally:

    db.close()
============================================================
8. RIDER REGISTRATION
============================================================
@app.post("/api/v1/riders/register")
def register_rider(
data: RiderRegistration
):
db = SessionLocal()

try:

    existing = (
        db.query(Rider)
        .filter(
            Rider.nin == data.nin
        )
        .first()
    )

    if existing:

        return {

            "rider_id": existing.id,

            "name": existing.name,

            "message":
                "A rider with this NIN is already registered",

            "verified":
                existing.verified,

            "available":
                existing.available
        }


    rider = Rider(

        id=gen_id("RD"),

        name=data.name,

        date_of_birth=data.date_of_birth,

        nin=data.nin,

        motorcycle_serial_number=
            data.motorcycle_serial_number,

        motorcycle_license=
            data.motorcycle_license,

        phone=data.phone,

        address=data.address,

        guarantor_name=
            data.guarantor_name,

        guarantor_phone=
            data.guarantor_phone,

        verified=False,

        available=True
    )


    db.add(rider)

    db.commit()

    db.refresh(rider)


    return {

        "rider_id": rider.id,

        "name": rider.name,

        "verified": rider.verified,

        "available": rider.available,

        "message":
            "Rider registered successfully. Awaiting verification."
    }

finally:

    db.close()
============================================================
9. GET RIDER
============================================================
@app.get("/api/v1/riders/{rider_id}")
def get_rider(rider_id: str):
db = SessionLocal()

try:

    rider = (
        db.query(Rider)
        .filter(Rider.id == rider_id)
        .first()
    )

    if not rider:

        raise HTTPException(
            status_code=404,
            detail="Rider not found"
        )


    return {

        "rider_id": rider.id,

        "name": rider.name,

        "phone": rider.phone,

        "verified": rider.verified,

        "available": rider.available,

        "current_lat":
            rider.current_lat,

        "current_lng":
            rider.current_lng
    }

finally:

    db.close()
============================================================
10. ADMIN/VERIFICATION ENDPOINT
============================================================
@app.post("/api/v1/riders/{rider_id}/verify")
def verify_rider(rider_id: str):
db = SessionLocal()

try:

    rider = (
        db.query(Rider)
        .filter(Rider.id == rider_id)
        .first()
    )

    if not rider:

        raise HTTPException(
            status_code=404,
            detail="Rider not found"
        )


    rider.verified = True

    db.commit()


    return {

        "rider_id": rider.id,

        "verified": True,

        "message":
            "Rider verified successfully"
    }

finally:

    db.close()
============================================================
11. WALLET FUNDING
============================================================
@app.post("/api/v1/wallet/fund")
def fund(
client_id: str,
amount: float
):
if amount <= 0:

    raise HTTPException(
        status_code=400,
        detail="Amount must be greater than zero"
    )


db = SessionLocal()

try:

    client = (
        db.query(Client)
        .filter(Client.id == client_id)
        .first()
    )

    if not client:

        raise HTTPException(
            status_code=404,
            detail="Client not found"
        )


    client.wallet_balance += amount


    transaction = Transaction(

        id=gen_id("TX"),

        client_id=client_id,

        type="CREDIT",

        amount=amount
    )


    db.add(transaction)

    db.commit()


    return {

        "credited": amount,

        "new_balance":
            client.wallet_balance
    }

finally:

    db.close()
============================================================
12. WALLET CHARGE
============================================================
@app.post("/api/v1/wallet/charge")
def charge(
client_id: str,
amount: float,
request_id: str = "SHIPMENT"
):
if amount <= 0:

    raise HTTPException(
        status_code=400,
        detail="Amount must be greater than zero"
    )


db = SessionLocal()

try:

    client = (
        db.query(Client)
        .filter(Client.id == client_id)
        .first()
    )

    if not client:

        raise HTTPException(
            status_code=404,
            detail="Client not found"
        )


    if client.wallet_balance < amount:

        raise HTTPException(
            status_code=400,
            detail="Insufficient wallet balance"
        )


    client.wallet_balance -= amount


    transaction = Transaction(

        id=gen_id("TX"),

        client_id=client_id,

        type="DEBIT",

        amount=amount,

        request_id=request_id
    )


    db.add(transaction)

    db.commit()


    return {

        "debited": amount,

        "new_balance":
            client.wallet_balance
    }

finally:

    db.close()
============================================================
13. WALLET BALANCE
============================================================
@app.get("/api/v1/wallet/balance/{client_id}")
def balance(client_id: str):
db = SessionLocal()

try:

    client = (
        db.query(Client)
        .filter(Client.id == client_id)
        .first()
    )

    if not client:

        raise HTTPException(
            status_code=404,
            detail="Client not found"
        )


    return {

        "client_id": client.id,

        "balance":
            client.wallet_balance
    }

finally:

    db.close()
============================================================
14. TRANSACTIONS
============================================================
@app.get("/api/v1/transactions/{client_id}")
def transactions(client_id: str):
db = SessionLocal()

try:

    rows = (
        db.query(Transaction)
        .filter(
            Transaction.client_id == client_id
        )
        .order_by(
            Transaction.created_at.desc()
        )
        .all()
    )


    return [

        {

            "id": tx.id,

            "type": tx.type,

            "amount": tx.amount,

            "request_id": tx.request_id,

            "created_at":
                tx.created_at.isoformat()
        }

        for tx in rows
    ]

finally:

    db.close()
============================================================
15. CREATE SHIPMENT
============================================================
@app.post("/api/v1/shipments")
def create_shipment(
data: ShipmentCreate
):
db = SessionLocal()

try:

    client = (
        db.query(Client)
        .filter(
            Client.id == data.client_id
        )
        .first()
    )

    if not client:

        raise HTTPException(
            status_code=404,
            detail="Client not found"
        )


    request_id =
        gen_id("REQ")


    # Simple temporary delivery pricing.
    # Replace with your actual pricing engine.
    price = 1500.0


    shipment = Shipment(

        id=request_id,

        client_id=data.client_id,

        pickup_address=
            data.pickup_address,

        pickup_lat=
            data.pickup_lat,

        pickup_lng=
            data.pickup_lng,

        dropoff_address=
            data.dropoff_address,

        dropoff_lat=
            data.dropoff_lat,

        dropoff_lng=
            data.dropoff_lng,

        price=price,

        status="NEW"
    )


    db.add(shipment)

    db.commit()

    db.refresh(shipment)


    return {

        "request_id":
            shipment.id,

        "client_id":
            shipment.client_id,

        "pickup_address":
            shipment.pickup_address,

        "dropoff_address":
            shipment.dropoff_address,

        "price":
            shipment.price,

        "status":
            shipment.status,

        "message":
            "Delivery request created and made available to riders"
    }

finally:

    db.close()
============================================================
16. RIDER REQUEST NOTIFICATION
============================================================
@app.get("/api/v1/riders/requests")
def rider_requests(
rider_id: str
):
db = SessionLocal()

try:

    rider = (
        db.query(Rider)
        .filter(
            Rider.id == rider_id
        )
        .first()
    )

    if not rider:

        raise HTTPException(
            status_code=404,
            detail="Rider not found"
        )


    if not rider.verified:

        return []


    if not rider.available:

        return []


    requests = (
        db.query(Shipment)
        .filter(
            Shipment.status == "NEW"
        )
        .order_by(
            Shipment.created_at.desc()
        )
        .all()
    )


    return [

        {

            "request_id":
                shipment.id,

            "client_id":
                shipment.client_id,

            "pickup_address":
                shipment.pickup_address,

            "pickup_lat":
                shipment.pickup_lat,

            "pickup_lng":
                shipment.pickup_lng,

            "dropoff_address":
                shipment.dropoff_address,

            "dropoff_lat":
                shipment.dropoff_lat,

            "dropoff_lng":
                shipment.dropoff_lng,

            "price":
                shipment.price,

            "status":
                shipment.status,

            "created_at":
                shipment.created_at.isoformat()
        }

        for shipment in requests
    ]

finally:

    db.close()
============================================================
17. RIDER ACCEPTS REQUEST
============================================================
@app.post("/api/v1/riders/requests/accept")
def accept_request(
data: AcceptRequest
):
db = SessionLocal()

try:

    rider = (
        db.query(Rider)
        .filter(
            Rider.id == data.rider_id
        )
        .first()
    )

    if not rider:

        raise HTTPException(
            status_code=404,
            detail="Rider not found"
        )


    if not rider.verified:

        raise HTTPException(
            status_code=403,
            detail="Rider has not been verified"
        )


    shipment = (
        db.query(Shipment)
        .filter(
            Shipment.id ==
            data.request_id
        )
        .first()
    )


    if not shipment:

        raise HTTPException(
            status_code=404,
            detail="Delivery request not found"
        )


    if shipment.status != "NEW":

        raise HTTPException(
            status_code=409,
            detail=
                "This request has already been accepted"
        )


    shipment.rider_id =
        rider.id

    shipment.status =
        "ACCEPTED"

    shipment.accepted_at =
        datetime.datetime.utcnow()


    rider.available = False


    db.commit()


    return {

        "request_id":
            shipment.id,

        "rider_id":
            rider.id,

        "status":
            shipment.status,

        "message":
            "Delivery request accepted"
    }

finally:

    db.close()
============================================================
18. RIDER LOCATION
============================================================
@app.post("/api/v1/riders/location")
def rider_location(
data: RiderLocation
):
db = SessionLocal()

try:

    rider = (
        db.query(Rider)
        .filter(
            Rider.id == data.rider_id
        )
        .first()
    )

    if not rider:

        raise HTTPException(
            status_code=404,
            detail="Rider not found"
        )


    rider.current_lat =
        data.lat

    rider.current_lng =
        data.lng


    db.commit()


    return {

        "rider_id":
            rider.id,

        "lat":
            rider.current_lat,

        "lng":
            rider.current_lng,

        "message":
            "Rider location updated"
    }

finally:

    db.close()
============================================================
19. GET SHIPMENT
============================================================
@app.get("/api/v1/shipments/{request_id}")
def get_shipment(
request_id: str
):
db = SessionLocal()

try:

    shipment = (
        db.query(Shipment)
        .filter(
            Shipment.id == request_id
        )
        .first()
    )


    if not shipment:

        raise HTTPException(
            status_code=404,
            detail="Shipment not found"
        )


    rider = None

    if shipment.rider_id:

        rider = (
            db.query(Rider)
            .filter(
                Rider.id ==
                shipment.rider_id
            )
            .first()
        )


    response = {

        "request_id":
            shipment.id,

        "client_id":
            shipment.client_id,

        "rider_id":
            shipment.rider_id,

        "pickup_address":
            shipment.pickup_address,

        "pickup_lat":
            shipment.pickup_lat,

        "pickup_lng":
            shipment.pickup_lng,

        "dropoff_address":
            shipment.dropoff_address,

        "dropoff_lat":
            shipment.dropoff_lat,

        "dropoff_lng":
            shipment.dropoff_lng,

        "price":
            shipment.price,

        "status":
            shipment.status
    }


    if rider:

        response["rider"] = {

            "rider_id":
                rider.id,

            "name":
                rider.name,

            "phone":
                rider.phone,

            "lat":
                rider.current_lat,

            "lng":
                rider.current_lng
        }


    return response

finally:

    db.close()
============================================================
20. COMPLETE DELIVERY
============================================================
@app.post("/api/v1/shipments/{request_id}/complete")
def complete_shipment(
request_id: str
):
db = SessionLocal()

try:

    shipment = (
        db.query(Shipment)
        .filter(
            Shipment.id ==
            request_id
        )
        .first()
    )


    if not shipment:

        raise HTTPException(
            status_code=404,
            detail="Shipment not found"
        )


    shipment.status =
        "COMPLETED"

    shipment.completed_at =
        datetime.datetime.utcnow()


    if shipment.rider_id:

        rider = (
            db.query(Rider)
            .filter(
                Rider.id ==
                shipment.rider_id
            )
            .first()
        )

        if rider:

            rider.available = True


    db.commit()


    return {

        "request_id":
            shipment.id,

        "status":
            shipment.status,

        "message":
            "Delivery completed"
    }

finally:

    db.close()
============================================================
21. BANK ACCOUNT PLACEHOLDER
============================================================
@app.get("/api/v1/bank-accounts/{client_id}")
def banks(client_id: str):
return {

    "message":
        "Bank API works - add your Flutterwave or Paystack integration here"
}
============================================================
22. LOCAL / RENDER STARTUP
============================================================
if name == "main":
port = int(
    os.getenv(
        "PORT",
        "8080"
    )
)


uvicorn.run(

    app,

    host="0.0.0.0", port=8080
)
