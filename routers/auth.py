from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from models.database import get_db, HR
from models.schemas import HRRegister, HRLogin, HRResponse, Token
from utils.auth import hash_password, verify_password, create_access_token, decode_access_token, get_token_from_header
from typing import Optional

router = APIRouter()


def get_current_hr(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)) -> HR:
    token = get_token_from_header(authorization or "")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    hr = db.query(HR).filter(HR.id == payload.get("sub")).first()
    if not hr or not hr.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return hr


@router.post("/register", response_model=Token)
def register(data: HRRegister, db: Session = Depends(get_db)):
    if db.query(HR).filter(HR.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(HR).filter(HR.username == data.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    hr = HR(
        name=data.name,
        email=data.email,
        username=data.username,
        password_hash=hash_password(data.password),
        company=data.company,
        role=data.role or "HR Manager",
    )
    db.add(hr)
    db.commit()
    db.refresh(hr)

    token = create_access_token({"sub": hr.id, "username": hr.username})
    return {"access_token": token, "token_type": "bearer", "hr": hr}


@router.post("/login", response_model=Token)
def login(data: HRLogin, db: Session = Depends(get_db)):
    hr = db.query(HR).filter(
        (HR.username == data.username) | (HR.email == data.username)
    ).first()

    if not hr or not verify_password(data.password, hr.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not hr.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    token = create_access_token({"sub": hr.id, "username": hr.username})
    return {"access_token": token, "token_type": "bearer", "hr": hr}


@router.get("/me", response_model=HRResponse)
def get_me(current_hr: HR = Depends(get_current_hr)):
    return current_hr


@router.post("/logout")
def logout():
    return {"message": "Logged out successfully"}
