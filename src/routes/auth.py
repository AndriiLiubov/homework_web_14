from typing import List

from fastapi import APIRouter, HTTPException, Depends, status, Security, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.schemas import UserModel, UserResponse, TokenModel, RequestEmail
from src.repository import users as repository_users
from src.services.auth import auth_service
from src.services.email import send_email

router = APIRouter(prefix='/auth', tags=["auth"])
security = HTTPBearer()


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: UserModel, background_tasks: BackgroundTasks, request: Request, db: Session = Depends(get_db)):
    """
    The signup function creates a new user in the database.
        It takes in a UserSchema object, which is validated by pydantic.
        If the email already exists, it raises an HTTPException with status code 409 (Conflict).
        Otherwise, it hashes the password and creates a new user using create_user from repositories/users.py.

    :param body: UserSchema: Validate the request body
    :param background_tasks: BackgroundTasks: Add a task to the background tasks queue
    :param request: Request: Get the base url of the application
    :param db: AsyncSession: Get the database session
    :return: A user object
    """
    exist_user = await repository_users.get_user_by_email(body.email, db)
    if exist_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account already exists")
    body.password = auth_service.get_password_hash(body.password)
    new_user = await repository_users.create_user(body, db)
    background_tasks.add_task(send_email, new_user.email, new_user.username, request.base_url)
    return {"user": new_user, "detail": "User successfully created. Check your email for confirmation."}



@router.post("/login", response_model=TokenModel)
async def login(body: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Authenticates a user and returns JWT tokens.
        This function verifies the user's credentials and returns access and refresh tokens if the
        credentials are valid. If the user's email is not confirmed or the credentials are invalid,
        it raises an HTTP 401 Unauthorized error.

    :param body: OAuth2PasswordRequestForm: Contains the user's login credentials (username and password)
    :param db: Session: Database session dependency
    :return: A dictionary containing access token, refresh token, and token type
    :raises HTTPException: If the email is invalid, not confirmed, or the password is incorrect
    """
    user = await repository_users.get_user_by_email(body.username, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email")
    if not user.confirmed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not confirmed")
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")
    # Generate JWT
    access_token = await auth_service.create_access_token(data={"sub": user.email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": user.email})
    await repository_users.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}



@router.get('/refresh_token', response_model=TokenModel)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Security(security), db: Session = Depends(get_db)):
    """
    Refreshes the user's JWT tokens.

     This function takes a refresh token, verifies it, and generates new access and refresh tokens.
     If the refresh token is invalid, it raises an HTTP 401 Unauthorized error.

    :param credentials: HTTPAuthorizationCredentials: Contains the refresh token from the Authorization header
    :param db: Session: Database session dependency
    :return: A dictionary containing new access token, refresh token, and token type
    :raises HTTPException: If the refresh token is invalid
    """
    token = credentials.credentials
    email = await auth_service.decode_refresh_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user.refresh_token != token:
        await repository_users.update_token(user, None, db)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    access_token = await auth_service.create_access_token(data={"sub": email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": email})
    await repository_users.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}



@router.get('/confirmed_email/{token}')
async def confirmed_email(token: str, db: Session = Depends(get_db)):
    """
    Confirms the user's email address.

     This function takes a token, verifies it, and confirms the user's email address if the token is valid.
     If the token is invalid or the user is not found, it raises an HTTP 400 Bad Request error.

    :param token: str: The token sent to the user's email for verification
    :param db: Session: Database session dependency
    :return: A message indicating whether the email was confirmed or already confirmed
    :raises HTTPException: If the token is invalid or the user is not found
    """
    email = await auth_service.get_email_from_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error")
    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    await repository_users.confirmed_email(email, db)
    return {"message": "Email confirmed"}


@router.post('/request_email')
async def request_email(body: RequestEmail, background_tasks: BackgroundTasks, request: Request,
                        db: Session = Depends(get_db)):
    """
    Sends an email confirmation request.

        This function takes an email address, checks if the user exists and if their email is not already confirmed,
        and sends a confirmation email. If the email is already confirmed, it returns a message indicating so.

    :param body: RequestEmail: Contains the email address to send the confirmation to
    :param background_tasks: BackgroundTasks: Adds the email sending task to the background tasks queue
    :param request: Request: Provides the base URL for constructing the confirmation link
    :param db: Session: Database session dependency
    :return: A message indicating that the confirmation email was sent or the email is already confirmed
    """
    user = await repository_users.get_user_by_email(body.email, db)

    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    if user:
        background_tasks.add_task(send_email, user.email, user.username, request.base_url)
    return {"message": "Check your email for confirmation."}

