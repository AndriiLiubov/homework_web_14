import os
from dotenv import load_dotenv

from fastapi import APIRouter, Depends, status, UploadFile, File
from sqlalchemy.orm import Session
import cloudinary
import cloudinary.uploader

from src.database.db import get_db
from src.database.models import User
from src.repository import users as repository_users
from src.services.auth import auth_service
from src.schemas import UserDb

load_dotenv()

cloudinary_name = os.environ.get('CLOUDINARY_NAME')
cloudinary_api_key = os.environ.get('CLOUDINARY_API_KEY')
cloudinary_api_secret = os.environ.get('CLOUDINARY_API_SECRET')

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me/", response_model=UserDb)
async def read_users_me(current_user: User = Depends(auth_service.get_current_user)):
    """
    Retrieves the current user's details.

        This function retrieves the details of the currently authenticated user. It is typically used to fetch
        information about the logged-in user, such as their username, email, and other profile details.

    :param current_user: User: The currently authenticated user
    :return: UserDb: Details of the current user
    """
    return current_user


@router.patch('/avatar', response_model=UserDb)
async def update_avatar_user(file: UploadFile = File(), current_user: User = Depends(auth_service.get_current_user),
                             db: Session = Depends(get_db)):
    """
    Updates the user's avatar.

        This function allows the current user to update their avatar image. It uploads the provided file to a cloud
        storage service (in this case, Cloudinary), updates the user's avatar URL in the database, and returns the
        updated user object.

    :param file: UploadFile: The avatar image file to be uploaded
    :param current_user: User: The currently authenticated user
    :param db: Session: Database session dependency
    :return: UserDb: The updated user object with the new avatar URL
    """
    cloudinary.config(
        cloud_name=cloudinary_name,
        api_key=cloudinary_api_key,
        api_secret=cloudinary_api_secret,
        secure=True
    )

    r = cloudinary.uploader.upload(file.file, public_id=f'NotesApp/{current_user.username}', overwrite=True)
    src_url = cloudinary.CloudinaryImage(f'NotesApp/{current_user.username}')\
                        .build_url(width=250, height=250, crop='fill', version=r.get('version'))
    user = await repository_users.update_avatar(current_user.email, src_url, db)
    return user
