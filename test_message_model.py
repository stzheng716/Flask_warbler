""" Message model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follow
from sqlalchemy.exc import IntegrityError, DataError


# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# Now we can import app

from app import app

app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

db.drop_all()
db.create_all()


class MessageModelTestCase(TestCase):
    def setUp(self):
        User.query.delete()
        Message.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)

        m1 = Message(text="test mesage")
        u1.messages.append(m1)

        db.session.add(m1)
        db.session.commit()

        self.u1_id = u1.id
        self.m1_id = m1.id

        self.client = app.test_client()

    def tearDown(self):
        db.session.rollback()

    def test_message_creation(self):
        """ create a message for a user and verify its creation"""

        # u1 = User.query.get(self.u1_id)
        # msg = Message(text="suh suh suhhh")
        # u1.messages.append(msg)

        u1 = User.query.get(self.u1_id)

        self.assertEqual(u1.messages[0], Message.query.get(1))
        self.assertEqual(u1.messages[0].text, "test mesage")

        #failing version
        self.assertEqual(False, u1.messages[0].text == "sup")

    def test_no_message_input(self):
        """tests that a an empty string added as a message is not saved as a message"""

        u1 = User.query.get(self.u1_id)
        message = Message(text=None)
        u1.messages.append(message)

        self.assertRaises(IntegrityError, db.session.commit)

    def  test_message_liked(self):
        """testing """

        u1 = User.query.get(self.u1_id)
        u2 = User.signup("u2", "u2@email.com", "password", None)
        m1 = Message.query.get(self.m1_id)
        u2.liked_messages.append(m1)
        db.session.commit()

        self.assertEqual(len(u1.messages[0].user_liked), 1)

        u2.liked_messages.remove(m1)
        db.session.commit()

        self.assertEqual(len(u1.messages[0].user_liked), 0)








