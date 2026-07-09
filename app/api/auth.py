from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token
from app.schemas.user import LoginRequest, Token
from app.services import user_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=Token, summary="Login with email and password")
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> Token:
    user = user_service.authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(subject=user.email)
    return Token(access_token=access_token)
