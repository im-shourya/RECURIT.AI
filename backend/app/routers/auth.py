"""
RECRUIT.AI — Auth Router
POST /auth/register   — Organisation registration
POST /auth/login      — Returns JWT
GET  /auth/me         — Current org profile
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.database import Organisation
from app.models.schemas import (
    OrgRegisterRequest,
    OrgLoginRequest,
    TokenResponse,
    OrgProfileResponse,
)
from app.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_org,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ──────────────────────────────────────────────
# REGISTER
# ──────────────────────────────────────────────
@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: OrgRegisterRequest, db: Session = Depends(get_db)):
    # Check if email already exists
    existing = db.query(Organisation).filter(Organisation.email == body.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    org = Organisation(
        name=body.name,
        email=body.email,
        password_hash=hash_password(body.password),
        description=body.description,
        domain_tags=body.domain_tags,
        logo_url=body.logo_url,
    )
    db.add(org)
    db.commit()
    db.refresh(org)

    token = create_access_token(data={"sub": str(org.id)})
    return TokenResponse(access_token=token)


# ──────────────────────────────────────────────
# LOGIN
# ──────────────────────────────────────────────
@router.post("/login", response_model=TokenResponse)
def login(body: OrgLoginRequest, db: Session = Depends(get_db)):
    org = db.query(Organisation).filter(Organisation.email == body.email).first()
    if not org or not verify_password(body.password, org.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(data={"sub": str(org.id)})
    return TokenResponse(access_token=token)


# ──────────────────────────────────────────────
# ME (current profile)
# ──────────────────────────────────────────────
@router.get("/me", response_model=OrgProfileResponse)
def get_me(org: Organisation = Depends(get_current_org)):
    return org
