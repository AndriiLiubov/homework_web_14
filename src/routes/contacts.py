from typing import List, Optional
from datetime import date, timedelta

from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from fastapi_limiter.depends import RateLimiter

from src.database.models import User
from src.database.db import get_db
from src.schemas import ContactBase, ContactResponse
from src.repository import contacts as repository_contacts

from src.services.auth import auth_service

router = APIRouter(prefix='/contacts', tags=["contacts"])


@router.get("/", response_model=List[ContactResponse], description='No more than 10 requests per minute',
            dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def read_contacts(
    skip: int = 0, 
    limit: int = 100, 
    first_name: Optional[str] = Query(None, max_length=50),
    last_name: Optional[str] = Query(None, max_length=50),
    email: Optional[str] = Query(None, max_length=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Retrieves a list of contacts based on specified criteria.

        This function retrieves a paginated list of contacts from the database. It supports optional filters
        for first name, last name, and email. Additionally, it implements rate limiting to ensure no more than
        10 requests per minute per client.

    :param skip: int: Number of records to skip (for pagination)
    :param limit: int: Maximum number of records to return per page
    :param first_name: Optional[str]: Filter by first name
    :param last_name: Optional[str]: Filter by last name
    :param email: Optional[str]: Filter by email
    :param db: Session: Database session dependency
    :param current_user: User: Current authenticated user
    :return: List of ContactResponse objects
    """
    contacts = await repository_contacts.get_contacts(skip, limit, db, current_user, first_name, last_name, email)
    return contacts


@router.get("/{contact_id}", response_model=ContactResponse, description='No more than 10 requests per minute',
            dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def read_contacts(contact_id: int, db: Session = Depends(get_db),current_user: User = Depends(auth_service.get_current_user)):
    """
    Retrieves a single contact by ID.

        This function retrieves a contact from the database by its unique identifier. It implements rate limiting
        to ensure no more than 10 requests per minute per client.

    :param contact_id: int: The unique identifier of the contact
    :param db: Session: Database session dependency
    :param current_user: User: Current authenticated user
    :return: A ContactResponse object representing the requested contact
    :raises HTTPException: If the contact with the given ID is not found
    """
    contact = await repository_contacts.get_contact(contact_id, current_user, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED, description='No more than 10 requests per minute',
            dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def create_contact(body: ContactBase, db: Session = Depends(get_db),
                         current_user: User = Depends(auth_service.get_current_user)):
    """
    Creates a new contact.

        This function creates a new contact in the database using the provided data. It implements rate limiting
        to ensure no more than 10 requests per minute per client.

    :param body: ContactBase: Data for creating the contact
    :param db: Session: Database session dependency
    :param current_user: User: Current authenticated user
    :return: A ContactResponse object representing the newly created contact
    """
    return await repository_contacts.create_contact(body, current_user, db)


@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(body: ContactBase, contact_id: int, db: Session = Depends(get_db),
                         current_user: User = Depends(auth_service.get_current_user)):
    """
    Updates an existing contact.

        This function updates an existing contact in the database with the provided data. It implements rate limiting
        to ensure no more than 10 requests per minute per client.

    :param body: ContactBase: Updated data for the contact
    :param contact_id: int: The unique identifier of the contact to update
    :param db: Session: Database session dependency
    :param current_user: User: Current authenticated user
    :return: A ContactResponse object representing the updated contact
    :raises HTTPException: If the contact with the given ID is not found
    """
    contact = await repository_contacts.update_contact(contact_id, body, current_user, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.delete("/{contact_id}", response_model=ContactResponse)
async def remove_contact(contact_id: int, db: Session = Depends(get_db),
                         current_user: User = Depends(auth_service.get_current_user)):
    """
    Deletes a contact.

        This function deletes a contact from the database. It implements rate limiting
        to ensure no more than 10 requests per minute per client.

    :param contact_id: int: The unique identifier of the contact to delete
    :param db: Session: Database session dependency
    :param current_user: User: Current authenticated user
    :return: A ContactResponse object representing the deleted contact
    :raises HTTPException: If the contact with the given ID is not found
    """
    contact = await repository_contacts.remove_contact(contact_id, current_user, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.get("/upcoming_birthdays/", response_model=List[ContactResponse], description='No more than 10 requests per minute',
            dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def get_upcoming_birthdays(db: Session = Depends(get_db),current_user: User = Depends(auth_service.get_current_user)):
    """
    Retrieves contacts with upcoming birthdays.

        This function retrieves a list of contacts with upcoming birthdays from the database. It implements rate limiting
        to ensure no more than 10 requests per minute per client.

    :param db: Session: Database session dependency
    :param current_user: User: Current authenticated user
    :return: List of ContactResponse objects
    """
    contacts = await repository_contacts.get_upcoming_birthdays(current_user, db)
    return contacts