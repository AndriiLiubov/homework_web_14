from typing import List, Optional
from datetime import date, timedelta

from sqlalchemy import extract
from sqlalchemy.orm import Session

from src.database.models import Contact, User
from src.schemas import ContactBase


async def get_contacts(
    skip: int, 
    limit: int, 
    db: Session,
    user: User,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    email: Optional[str] = None,
    
) -> List[Contact]:
    """
    Retrieves a list of contacts for the specified user based on optional filters.

    This function retrieves a paginated list of contacts from the database. It supports optional filters
    for first name, last name, and email. The contacts are filtered to include only those belonging to the
    specified user.

    :param skip: int: Number of records to skip (for pagination)
    :param limit: int: Maximum number of records to return per page
    :param db: Session: Database session dependency
    :param user: User: The currently authenticated user
    :param first_name: Optional[str]: Filter by first name
    :param last_name: Optional[str]: Filter by last name
    :param email: Optional[str]: Filter by email
    :return: List of Contact objects
    """
    query = db.query(Contact).filter(Contact.user_id == user.id)
    
    if first_name:
        query = query.filter(Contact.first_name.ilike(f"%{first_name}%"))
    if last_name:
        query = query.filter(Contact.last_name.ilike(f"%{last_name}%"))
    if email:
        query = query.filter(Contact.email.ilike(f"%{email}%"))
    
    return query.offset(skip).limit(limit).all()


async def get_contact(contact_id: int, user: User, db: Session) -> Contact | None:
    """
    Retrieves a single contact by ID for the specified user.

    This function retrieves a contact from the database by its unique identifier. The contact is filtered
    to ensure it belongs to the specified user.

    :param contact_id: int: The unique identifier of the contact
    :param user: User: The currently authenticated user
    :param db: Session: Database session dependency
    :return: A Contact object representing the requested contact, or None if not found
    """
    return db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == user.id).first()


async def create_contact(body: ContactBase, user: User, db: Session) -> Contact:
    """
    Creates a new contact for the specified user.

    This function creates a new contact in the database using the provided data. The contact is associated
    with the specified user.

    :param body: ContactBase: Data for creating the contact
    :param user: User: The currently authenticated user
    :param db: Session: Database session dependency
    :return: A Contact object representing the newly created contact
    """
    contact = Contact(**body.model_dump(exclude_unset=True), user_id=user.id)
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


async def update_contact(contact_id: int, body: ContactBase, user: User, db: Session) -> Contact | None:
    """
    Updates an existing contact for the specified user.

    This function updates an existing contact in the database with the provided data. The contact is filtered
    to ensure it belongs to the specified user.

    :param contact_id: int: The unique identifier of the contact to update
    :param body: ContactBase: Updated data for the contact
    :param user: User: The currently authenticated user
    :param db: Session: Database session dependency
    :return: A Contact object representing the updated contact, or None if not found
    """
    contact = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == user.id).first()
    if contact:
        contact.first_name = body.first_name
        contact.last_name = body.last_name
        contact.email = body.email
        contact.phone_number = body.phone_number
        contact.birth_date = body.birth_date
        contact.additional_info = body.additional_info
        db.commit()
        db.refresh(contact)  # Added this to ensure the contact object is up-to-date
    return contact



async def remove_contact(contact_id: int, user: User, db: Session) -> Contact | None:
    """
    Deletes a contact for the specified user.

    This function deletes a contact from the database. The contact is filtered to ensure it belongs to the
    specified user.

    :param contact_id: int: The unique identifier of the contact to delete
    :param user: User: The currently authenticated user
    :param db: Session: Database session dependency
    :return: A Contact object representing the deleted contact, or None if not found
    """
    contact = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == user.id).first()
    if contact:
        db.delete(contact)
        db.commit()
    return contact


async def get_upcoming_birthdays(user: User, db: Session) -> List[Contact]:
    """
    Retrieves contacts with upcoming birthdays for the specified user.

    This function retrieves a list of contacts with upcoming birthdays from the database. The contacts are
    filtered to include only those belonging to the specified user, with birthdays in the next 7 days.

    :param user: User: The currently authenticated user
    :param db: Session: Database session dependency
    :return: List of Contact objects with upcoming birthdays
    """
    today = date.today()
    next_week = today + timedelta(days=7)
    
    today_month = today.month
    today_day = today.day
    next_week_month = next_week.month
    next_week_day = next_week.day
    
    if today_month == next_week_month:
        query = db.query(Contact).filter(
            Contact.user_id == user.id,
            extract('month', Contact.birth_date) == today_month,
            extract('day', Contact.birth_date).between(today_day, next_week_day)
        )
    else:
        query = db.query(Contact).filter(
            Contact.user_id == user.id,
            (extract('month', Contact.birth_date) == today_month) & (extract('day', Contact.birth_date) >= today_day) |
            (extract('month', Contact.birth_date) == next_week_month) & (extract('day', Contact.birth_date) <= next_week_day)
        )
    
    return query.all()

