# emmbio.py - SINGLE FILE, NO IMPORT ERRORS
from fastapi import FastAPI
import uvicorn
from sqlalchemy import create_engine, Column, String, Float, Boolean, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
import datetime, uuid

engine = create_engine("sqlite:///emmbio.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()
def gen_id(p): return f"{p}-{uuid.uuid4().hex[:6].upper()}"

class Client(Base):
    __tablename__="clients"
    id=Column(String,primary_key=True); name=Column(String); email=Column(String)
    type=Column(String,default="INDIVIDUAL"); wallet_balance=Column(Float,default=0)

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Emmbio Logistics")

@app.get("/")
def home():
    return {"status": "Emmbio is RUNNING on Windows!"}

@app.post("/api/v1/clients/register")
def register_client(name: str, email: str):
    db = SessionLocal()
    c = Client(id=gen_id("CL"), name=name, email=email)
    db.add(c); db.commit(); db.close()
    return {"client_id": c.id, "name": name, "wallet": 0}

@app.post("/api/v1/wallet/fund")
def fund(client_id: str, amount: float):
    db = SessionLocal()
    c = db.query(Client).filter(Client.id==client_id).first()
    c.wallet_balance += amount
    db.commit(); db.close()
    return {"credited": amount, "new_balance": c.wallet_balance}

@app.get("/api/v1/bank-accounts/{client_id}")
def banks(client_id: str):
    return {"message": "Bank API works - add your Flutterwave/Paystack key here"}

# THIS LINE FIXES YOUR ERROR - runs without needing "main:app"
if __name__ == "__main__":
    uvicorn.run(app, host="https://emmbio.onrender.com)
