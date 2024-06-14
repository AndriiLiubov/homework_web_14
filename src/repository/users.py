from libgravatar import Gravatar # type: ignore
from sqlalchemy.orm import Session

from src.database.models import User
from src.schemas import UserModel


async def get_user_by_email(email: str, db: Session) -> User:
    """
    Retrieves a user by their email address.

    This function queries the database to find a user with the specified email address.

    :param email: str: The email address of the user to retrieve
    :param db: Session: Database session dependency
    :return: User object representing the user with the specified email, or None if not found
    """
    return db.query(User).filter(User.email == email).first()


async def create_user(body: UserModel, db: Session) -> User:
    """
    Creates a new user in the database.

    This function creates a new user in the database using the data provided in the `UserModel`. It also attempts
    to fetch an avatar image using the Gravatar service based on the user's email address.

    :param body: UserModel: Data for creating the user
    :param db: Session: Database session dependency
    :return: User object representing the newly created user
    """
    avatar = None
    try:
        g = Gravatar(body.email)
        avatar = g.get_image()
    except Exception as e:
        print(e)
    new_user = User(**body.model_dump(), avatar=avatar)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


async def update_token(user: User, token: str | None, db: Session) -> None:
    """
    Updates the user's refresh token.

    This function updates the refresh token for the specified user in the database.

    :param user: User: The user whose refresh token is to be updated
    :param token: str | None: The new refresh token, or None to remove the token
    :param db: Session: Database session dependency
    :return: None
    """
    user.refresh_token = token
    db.commit()


async def confirmed_email(email: str, db: Session) -> None:
    """
    Confirms the user's email address.

    This function sets the user's `confirmed` status to True in the database.

    :param email: str: The email address of the user to confirm
    :param db: Session: Database session dependency
    :return: None
    """
    user = await get_user_by_email(email, db)
    user.confirmed = True
    db.commit()


async def update_avatar(email, url: str, db: Session) -> User:
    """
    Updates the user's avatar URL.

    This function updates the avatar URL for the user with the specified email address.

    :param email: str: The email address of the user whose avatar is to be updated
    :param url: str: The new avatar URL
    :param db: Session: Database session dependency
    :return: User object representing the updated user
    """
    user = await get_user_by_email(email, db)
    user.avatar = url
    db.commit()
    return user

