"""User View tests."""

# run these tests like:
#
#    FLASK_DEBUG=False python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, Message, User

from app import app, CURR_USER_KEY

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']

db.drop_all()
db.create_all()

app.config['WTF_CSRF_ENABLED'] = False

class UserBaseViewTestCase(TestCase):
    def setUp(self):
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)
        db.session.add(u1,u2)
        db.session.flush()

        db.session.commit()

        self.u1_id = u1.id
        self.u2_id = u2.id

        self.client = app.test_client()

    def tearDown(self):
        db.session.rollback()

    def test_logged_user_views_follower_following(self):
        """test that a logged in user can view both followers and people
        being followed"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

        resp = c.get(f'/users/{self.u2_id}/followers')

        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn("<!-- follower test block -->" ,html)

        resp = c.get(f'/users/{self.u2_id}/following')

        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn("<!-- testing: following page -->" ,html)

    def test_not_logged_user_views_follower_following(self):
        """test that a non logged in user cannot view both followers and people
        being followed"""
        with self.client as c:

            resp = c.get(f'/users/{self.u2_id}/followers', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)
            self.assertIn("<!-- test: user not logged in -->" , html)

            resp = c.get(f'/users/{self.u2_id}/following', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)
            self.assertIn("<!-- test: user not logged in -->" , html)

    def test_user_can_delete_or_add_msg(self):
        """test that a logged in user can create or delete a message"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            msg = Message(text="testing for message creation")
            u1 = User.query.get(self.u1_id)
            u1.messages.append(msg)

            db.session.commit()

            resp = c.post(f"/users/{g.user.id}", )

            resp = c.post(
                f"/users/{self.user_id}/posts/new",
                data={
                    "title": "new_title",
                    "content": "new_content",



