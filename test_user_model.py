"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy.exc import IntegrityError


from models import db, User, Message, Follow

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()


class UserModelTestCase(TestCase):
    def setUp(self):
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)

        db.session.commit()
        self.u1_id = u1.id
        self.u2_id = u2.id

        self.client = app.test_client()

    def tearDown(self):
        db.session.rollback()

    def test_user_model(self):
        u1 = User.query.get(self.u1_id)

        # User should have no messages & no followers
        self.assertEqual(len(u1.messages), 0)
        self.assertEqual(len(u1.followers), 0)

    def test_is_following(self):
        """test that is_following detects when user1 is following user2
        and also when user1 is not following user2"""

        follower = User.query.get(self.u2_id)
        followed_user = User.query.get(self.u1_id)

        follower.following.append(followed_user)
        db.session.commit()

        self.assertEqual(follower.is_following(followed_user), True)
        self.assertEqual(followed_user.is_following(follower), False)

    def test_is_following(self):
        """test that is_following detects when user2 is following user1 and
        when user2 is not following user1"""

        follower = User.query.get(self.u1_id)
        followed_user = User.query.get(self.u2_id)

        follower.following.append(followed_user)
        db.session.commit()

        self.assertEqual(follower.is_following(followed_user), True)
        self.assertEqual(followed_user.is_following(follower), False)

    def test_User_signup(self):
        """test that User.signup creates user when inputs are valid and doesnt
        when inputs are invalid"""

        u1 = User.query.get(self.u1_id)
        self.assertEqual(u1.username, "u1")

        #create a User with false inputs and test
        def func1():
            try:
                u3 = User.signup("u1", "u1@email.com", "password", None)
                # db.session.commit()
                db.session.commit()
            except IntegrityError:
                return "blah"

        # self.assertIsInstance(IntegrityError, )
            # self.assertEqual(db.session.commit(), IntegrityError)
            self.assertEqual(func1(), "blah")



