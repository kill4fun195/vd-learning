from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.services import user_service

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create user (email + password)",
)
def create_user(user_in: UserCreate, db: Session = Depends(get_db)) -> User:
    if user_service.get_user_by_email(db, user_in.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    return user_service.create_user(db, user_in)


@router.get("/me", response_model=UserResponse, summary="Get current user detail")
def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.get("/{user_id}", response_model=UserResponse, summary="Get user detail by ID")
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> User:
    user = user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user
