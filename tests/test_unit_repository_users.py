import unittest
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from src.database.models import Contact, User
from src.schemas import UserModel
from src.repository.users import (
    get_user_by_email,
    create_user,
    update_token,
    confirmed_email,
    update_avatar,
)


class TestUsers(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.session = MagicMock(spec=Session)
        self.user = User(id=1, email="test_email@test.com")

    async def test_get_user_by_email(self):
        user = User()
        self.session.query().filter().first.return_value = user
        result = await get_user_by_email(email="test_email@test.com", db=self.session)
        self.assertEqual(result, user)

    async def test_get_user_by_email_not_found(self):
        self.session.query().filter().first.return_value = None
        result = await get_user_by_email(email="test_email@test.com", db=self.session)
        self.assertIsNone(result)

    async def test_create_user(self):
        body = UserModel(username="test_username",
                         email="test_email@test.com",
                         password="123456789")
        result = await create_user(body=body, db=self.session)
        self.assertEqual(result.username, body.username)
        self.assertEqual(result.email, body.email)
        self.assertEqual(result.password, body.password)
        self.assertTrue(hasattr(result, "id"))

    async def test_update_token(self):
        user = User()
        self.session.query().filter().first.return_value = user
        self.session.commit.return_value = None
        await update_token(user=user, token="abcdefgh", db=self.session)
        self.assertEqual(user.refresh_token, "abcdefgh")
        self.session.commit.assert_called_once()

    async def test_update_token_not_found(self):
        self.session.query().filter().first.return_value = None
        self.session.commit.return_value = None
        result = await update_token(user=self.user, token="abcdefgh", db=self.session)
        self.assertIsNone(result)

    async def test_confirmed_email(self):
        user = User()
        user.confirmed = False
        self.session.query().filter().first.return_value = user
        await confirmed_email(email="test_email@test.com", db=self.session)
        self.assertTrue(user.confirmed)

    async def test_update_avatar(self):
        user = User(email="test_email@test.com", avatar="test_url")
        self.session.query().filter().first.return_value = user
        self.session.commit.return_value = None
        result = await update_avatar(email="test_email@test.com", url="test_url", db=self.session)
        self.assertEqual(result, user)


if __name__ == '__main__':
    unittest.main()
