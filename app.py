import os
from dotenv import load_dotenv

from flask import Flask, render_template, request, flash, redirect, session, g, abort
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from flask_cors import CORS

from forms import UserAddForm, LoginForm, MessageForm, CSRFProtectForm, UserEditform
from models import db, connect_db, User, Message

load_dotenv()

CURR_USER_KEY_WARBLER = "curr_user_warbler"

app = Flask(__name__)
CORS(app)

database_url = os.environ['DATABASE_URL']
database_url = database_url.replace('postgres://', 'postgresql://')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
toolbar = DebugToolbarExtension(app)

connect_db(app)


##############################################################################
# User signup/login/logout


@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY_WARBLER in session:
        g.user = User.query.get(session[CURR_USER_KEY_WARBLER])
    else:
        g.user = None


@app.before_request
def provide_CSRF_protection():
    """Adding CSRF protection to Flask global object."""

    g.csrf_form = CSRFProtectForm()


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY_WARBLER] = user.id


def do_logout():
    """Log out user."""

    if CURR_USER_KEY_WARBLER in session:
        del session[CURR_USER_KEY_WARBLER]
        flash("Logged out")


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """

    do_logout()

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login and redirect to homepage on success."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(
            form.username.data,
            form.password.data,
        )

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)


@app.post('/logout')
def logout():
    """Handle logout of user and redirect to homepage."""

    form = g.csrf_form

    if not g.user or not form.validate_on_submit():

        flash("You were not logged in")
        return redirect("/")

    do_logout()

    flash("You have successfully logged out.", 'success')
    return redirect("/login")


##############################################################################
# General user routes:

@app.get('/users')
def list_users():
    """Page with listing of users.

    Can take a 'q' param in querystring to search by that username.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    search = request.args.get('q')

    if not search:
        users = User.query.all()
    else:
        users = User.query.filter(User.username.like(f"%{search}%")).all()

    return render_template('users/index.html', users=users)


@app.get('/users/<int:user_id>')
def show_user(user_id):
    """Show user profile."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)

    return render_template('users/show.html', user=user)


@app.get('/users/<int:user_id>/following')
def show_following(user_id):
    """Show list of people this user is following."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/following.html', user=user)


@app.get('/users/<int:user_id>/followers')
def show_followers(user_id):
    """Show list of followers of this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/followers.html', user=user)


@app.post('/users/follow/<int:follow_id>')
def start_following(follow_id):
    """Add a follow for the currently-logged-in user.

    Redirect to following page for the current for the current user.
    """

    form = g.csrf_form

    if not g.user or not form.validate_on_submit():

        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get_or_404(follow_id)
    g.user.following.append(followed_user)
    db.session.commit()

    return_url = request.form['url']

    return redirect(f"{return_url}")


@app.post('/users/stop-following/<int:follow_id>')
def stop_following(follow_id):
    """Have currently-logged-in-user stop following this user.

    Redirect to following page for the current for the current user.
    """

    form = g.csrf_form

    if not g.user or not form.validate_on_submit():

        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get_or_404(follow_id)
    g.user.following.remove(followed_user)
    db.session.commit()

    return_url = request.form['url']

    return redirect(f"{return_url}")


@app.route('/users/profile', methods=["GET", "POST"])
def profile():
    """Update profile for current user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = UserEditform(obj=g.user)

    if form.validate_on_submit():
        result = g.user.authenticate(g.user.username, form.password.data)

        if result:
            g.user.username = form.username.data
            g.user.email = form.email.data
            g.user.bio = form.bio.data
            g.user.header_image_url = form.header_image_url.data
            g.user.image_url = form.image_url.data

            db.session.commit()

            return redirect(f'/users/{g.user.id}')

        flash("Please enter correct password to submit updates.", "danger")

    return render_template("users/edit.html", form=form, user_id=g.user.id)


@app.post('/users/delete')
def delete_user():
    """Delete user.
    Redirect to signup page.
    """
    form = g.csrf_form

    if not g.user or not form.validate_on_submit():

        flash("Access unauthorized.", "danger")
        return redirect("/")

    Message.query.filter(Message.user_id == g.user.id).delete()

    db.session.delete(g.user)
    db.session.commit()

    do_logout()
    return redirect("/signup")


##############################################################################
# Messages routes:

@app.route('/messages/new', methods=["GET", "POST"])
def add_message():
    """Add a message:
    Show form if GET. If valid, update message and redirect to user page.
    """

    if not g.user:

        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = MessageForm()

    if form.validate_on_submit():
        msg = Message(text=form.text.data)
        g.user.messages.append(msg)
        db.session.commit()

        return redirect(f"/users/{g.user.id}")

    return render_template('messages/create.html', form=form)


@app.get('/messages/<int:message_id>')
def show_message(message_id):
    """Show a message."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    msg = Message.query.get_or_404(message_id)
    return render_template('messages/show.html', message=msg)


@app.post('/messages/<int:message_id>/delete')
def delete_message(message_id):
    """Delete a message.

    Check that this message was written by the current user.
    Redirect to user page on success.
    """

    form = g.csrf_form
    msg = Message.query.get_or_404(message_id)

    if not g.user or not form.validate_on_submit() or g.user.id != msg.user_id:

        flash("Access unauthorized.", "danger")
        return redirect("/")

    db.session.delete(msg)
    db.session.commit()

    return redirect(f"/users/{g.user.id}")


##############################################################################
# Homepage and error pages


@app.get('/')
def homepage():
    """Show homepage:
    - anon users: no messages
    - logged in: 100 most recent messages of self & followed_users
    """

    if g.user:
        list_of_following_id = [
            user.id for user in g.user.following] + [g.user.id]

        messages = (Message
                    .query
                    .order_by(Message.timestamp.desc())
                    .filter(Message.user_id.in_(list_of_following_id))
                    .limit(100)
                    .all())

        return render_template('home.html', messages=messages)

    else:
        return render_template('home-anon.html')

##############################################################################
# like messages


@app.post("/message/<int:message_id>/like")
def toggle_like(message_id):
    """Get current message based on message.id and append to liked_messages
     depending on current user """

    form = g.csrf_form

    if not g.user or not form.validate_on_submit():
        flash("Access unauthorized.", "danger")
        return redirect("/")

    message = Message.query.get_or_404(message_id)

    if message.user_id == g.user.id:
        return abort(403)

    if message in g.user.liked_messages:
        g.user.liked_messages.remove(message)
    else:
        g.user.liked_messages.append(message)

    db.session.commit()

    return_url = request.form['url']

    return redirect(f"{return_url}")


@app.get('/users/<int:user_id>/liked_messages')
def show_liked_messages(user_id):
    """Show list of liked messages of this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/liked_messages.html', user=user)

@app.errorhandler(404)
def page_not_found(e):
    """404 NOT FOUND page."""

    return render_template('404.html'), 404


@app.after_request
def add_header(response):
    """Add non-caching headers on every request."""

    # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control
    response.cache_control.no_store = True
    return response
