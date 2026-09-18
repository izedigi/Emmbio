import datetime
import uuid
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, String, Float, Boolean, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

# 1. Database Setup
engine = create_engine("sqlite:///emmbio.db", connect_args={"check_same_thread": False})

# ADDED: expire_on_commit=False prevents attributes from expiring after a commit/close
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)
Base = declarative_base()

def gen_id(p): 
    return f"{p}-{uuid.uuid4().hex[:6].upper()}"

class Client(Base):
    __tablename__ = "clients"
    id = Column(String, primary_key=True)
    name = Column(String)
    email = Column(String)
    type = Column(String, default="INDIVIDUAL")
    wallet_balance = Column(Float, default=0.0)

Base.metadata.create_all(bind=engine)

# 2. FastAPI Setup (Only declare 'app' once)
app = FastAPI(title="Emmbio Logistics")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Routes
@app.get("/")
def home():
    return {"status": "Emmbio is RUNNING on Windows!"}

@app.get("/register")
def register():
    return {"message": "registered"}

@app.get("/wallet")
def wallet():
    return {"wallet": "0x..."}

@app.post("/api/v1/clients/register")
def register_client(name: str, email: str):
    db = SessionLocal()
    try:
        c = Client(id=gen_id("CL"), name=name, email=email)
        db.add(c)
        db.commit()
        return {"client_id": c.id, "name": name, "wallet": 0}
    finally:
        db.close()

@app.post("/api/v1/wallet/fund")
def fund(client_id: str, amount: float):
    db = SessionLocal()
    try:
        c = db.query(Client).filter(Client.id == client_id).first()
        if not c:
            return {"error": "Client not found"}, 404
            
        c.wallet_balance += amount
        db.commit()
        # This will now safely work because expire_on_commit=False keeps the value cached
        return {"credited": amount, "new_balance": c.wallet_balance}
    finally:
        db.close()  # Handled safely via try/finally block

@app.get("/api/v1/bank-accounts/{client_id}")
def banks(client_id: str):
    return {"message": "Bank API works - add your Flutterwave/Paystack key here"}

# 4. Local Execution Configuration
if __name__ == "__main__":
    # CHANGED: Host must be a local binding IP, not an external URL. 
    # Use 0.0.0.0 for Render deployments so it binds to their dynamic port properly.
    uvicorn.run(app, host="127.0.0.1", port=8080)
