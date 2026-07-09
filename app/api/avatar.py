from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse
from app.services import s3_service, user_service

router = APIRouter(prefix="/users", tags=["Avatar"])


@router.post(
    "/me/avatar",
    response_model=UserResponse,
    summary="Upload avatar for current user",
)
async def upload_my_avatar(
    file: UploadFile = File(..., description="Avatar image (jpeg/png/webp/gif, max 5MB)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    avatar_url = await s3_service.upload_avatar(file, current_user.id)
    return user_service.update_avatar_url(db, current_user, avatar_url)
