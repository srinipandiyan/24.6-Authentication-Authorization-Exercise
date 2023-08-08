"""Flask app exercise--Authorization/Authentication with Bcrypt."""

from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension

from models import connect_db, db, User, Feedback
from forms import RegisterForm, LoginForm, FeedbackForm, DeleteForm

app = Flask(__name__)
app.app_context().push()

app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///hashing_login"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "abc123"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

toolbar = DebugToolbarExtension(app)

connect_db(app)
db.create_all()

### APPLICATION ROUTES

@app.route("/")
def homepage():
    """Homepage redirect to register"""

    return redirect("/register")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user: produce form & handle form submission."""

    if "username" in session:
        return redirect(f"/users/{session['username']}")
    
    form = RegisterForm()

    if form.validate_on_submit():

        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data
       
        user = User.register(username, password, email, first_name, last_name)
        
        db.session.add(user)
        db.session.commit()

        session["username"] = user.username

        # on successful login, redirect to user page
        return redirect(f"/users/{session['username']}")

    else:
        return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Produce login form or handle login."""

    if "username" in session:
        return redirect(f"/users/{session['username']}")
    
    form = LoginForm()

    if form.validate_on_submit():
        name = form.username.data
        password = form.password.data

        # authenticate will return a user or False
        user = User.authenticate(name, password)

        if user:
            session["username"] = user.username # keep logged in
            return redirect(f"/users/{session['username']}")

        else:
            form.username.errors = ["Invalid username/password combo"]

    return render_template("login.html", form=form)
# end-login


@app.route("/users/<username>")
def secret(username):
    """Example hidden page for logged-in users only."""

    if "username" not in session or username != session['username']:
        flash("You must be logged in to view!")
        return redirect("/")

        # alternatively, can return HTTP Unauthorized status:
        #
        # from werkzeug.exceptions import Unauthorized
        # raise Unauthorized()

    else:
        user = User.query.get(username)
        form = DeleteForm()
        return render_template("show.html", user=user, form=form)
    

@app.route("/users/<username>/delete", methods=["POST"])
def delete_auth_user(username):
    """Remove authorized user from db and redirect to login page."""

    if "username" not in session or username != session['username']:
        flash("You must be logged in to view!")
        return redirect("/")

    user = User.query.get(username)
    
    db.session.delete(user)
    db.session.commit()
    
    session.pop("username")

    return redirect("/login")


@app.route("/users/<username>/feedback/new", methods=["GET", "POST"])
def add_feedback(username):
    """Show and handle add-feedback form."""

    if "username" not in session or username != session['username']:
        flash("You must be logged in to view!")
        return redirect("/")

    form = FeedbackForm()

    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data

        feedback = Feedback(
            title=title,
            content=content,
            username=username,
        )

        db.session.add(feedback)
        db.session.commit()

        return redirect(f"/users/{feedback.username}")

    else:
        return render_template("new_feedback.html", form=form)

@app.route("/feedback/<int:feedback_id>/update", methods=["GET", "POST"])
def update_feedback(feedback_id):
    """Show and handle update-feedback form."""

    feedback = Feedback.query.get(feedback_id)

    if "username" not in session or feedback.username != session['username']:
        flash("You must be logged in to view!")
        return redirect("/")

    form = FeedbackForm(obj=feedback)
    #obj keyword argument in WTForms enables input validation of FeedbackForm
    
    if form.validate_on_submit():
        
        feedback.title = form.title.data
        feedback.content = form.content.data

        db.session.commit()

        return redirect(f"/users/{feedback.username}")

    return render_template("edit_feedback.html", form=form, feedback=feedback)


@app.route("/feedback/<int:feedback_id>/delete", methods=["POST"])
def delete_feedback(feedback_id):
    """Delete feedback."""

    feedback = Feedback.query.get(feedback_id)

    if "username" not in session or feedback.username != session['username']:
        flash("You must be logged in to view!")
        return redirect("/")

    form = DeleteForm()

    if form.validate_on_submit():
        db.session.delete(feedback)
        db.session.commit()

    return redirect(f"/users/{feedback.username}")


@app.route("/logout")
def logout():
    """Logs user out and redirects to homepage."""

    session.pop("username")

    return redirect("/login")