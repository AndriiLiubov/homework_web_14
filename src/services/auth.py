import pickle
import redis
import os
from dotenv import load_dotenv
from typing import Optional

from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.repository import users as repository_users
from src.conf.config import settings

# load_dotenv()

redis_host = settings.REDIS_DOMAIN
redis_port = settings.REDIS_PORT


class Auth:
    """
    Auth class providing various authentication and authorization functionalities.

    This class handles password hashing, token generation, and token validation using JWT. It includes methods for
    creating access and refresh tokens, verifying passwords, and retrieving the current user based on the JWT token.

    Attributes:
        pwd_context (CryptContext): The password context for hashing and verifying passwords.
        SECRET_KEY (str): The secret key for encoding and decoding JWT tokens.
        ALGORITHM (str): The algorithm used for encoding JWT tokens.
        oauth2_scheme (OAuth2PasswordBearer): The OAuth2 password bearer scheme for token authentication.
        r (redis.Redis): The Redis client instance for caching user data.
    """
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    SECRET_KEY = settings.SECRET_KEY_JWT
    ALGORITHM = settings.ALGORITHM
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
    r = redis.Redis(host=redis_host, port=redis_port, db=0)

    def verify_password(self, plain_password, hashed_password):
        """
        Verify a plain password against a hashed password.

        :param plain_password: str: The plain password to verify
        :param hashed_password: str: The hashed password to compare against
        :return: bool: True if the password matches, False otherwise
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str):
        """
        Hash a plain password.

        :param password: str: The plain password to hash
        :return: str: The hashed password
        """
        return self.pwd_context.hash(password)

    # define a function to generate a new access token
    async def create_access_token(self, data: dict, expires_delta: Optional[float] = None):
        """
        Generate a new access token.

        :param data: dict: The data to include in the token payload
        :param expires_delta: Optional[float]: The expiration time of the token in seconds (default is 15 minutes)
        :return: str: The encoded JWT access token
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire, "scope": "access_token"})
        encoded_access_token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_access_token

    # define a function to generate a new refresh token
    async def create_refresh_token(self, data: dict, expires_delta: Optional[float] = None):
        """
        Generate a new refresh token.

        :param data: dict: The data to include in the token payload
        :param expires_delta: Optional[float]: The expiration time of the token in seconds (default is 7 days)
        :return: str: The encoded JWT refresh token
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire, "scope": "refresh_token"})
        encoded_refresh_token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_refresh_token

    async def decode_refresh_token(self, refresh_token: str):
        """
        Decode and validate a refresh token.

        :param refresh_token: str: The refresh token to decode
        :return: str: The email (subject) from the token payload
        :raises HTTPException: If the token is invalid or the scope is incorrect
        """
        try:
            payload = jwt.decode(refresh_token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload['scope'] == 'refresh_token':
                email = payload['sub']
                return email
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid scope for token')
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate credentials')

    async def get_current_user(self, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
        """
        Retrieve the current user based on the access token.

        :param token: str: The JWT access token
        :param db: Session: The database session dependency
        :return: User: The current user object
        :raises HTTPException: If the token is invalid or user is not found
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            # Decode JWT
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload['scope'] == 'access_token':
                email = payload["sub"]
                if email is None:
                    raise credentials_exception
            else:
                raise credentials_exception
        except JWTError as e:
            raise credentials_exception

        user = self.r.get(f"user:{email}")
        if user is None:
            user = await repository_users.get_user_by_email(email, db)
            if user is None:
                raise credentials_exception
            self.r.set(f"user:{email}", pickle.dumps(user))
            self.r.expire(f"user:{email}", 900)
        else:
            user = pickle.loads(user)
        return user
    
    def create_email_token(self, data: dict):
        """
        Generate a token for email verification.

        :param data: dict: The data to include in the token payload
        :return: str: The encoded JWT email verification token
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire})
        token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return token
    
    async def get_email_from_token(self, token: str):
        """
        Retrieve the email from an email verification token.

        :param token: str: The email verification token
        :return: str: The email from the token payload
        :raises HTTPException: If the token is invalid
        """
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            email = payload["sub"]
            return email
        except JWTError as e:
            print(e)
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail="Invalid token for email verification")



auth_service = Auth()
