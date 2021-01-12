from flask import Flask, render_template, redirect, flash, session
from models import db, db_connect, User, Feedback
from forms import RegisterForm, LoginForm, AddFeedbackForm

app = Flask(__name__)

app.config["SECRET_KEY"] = "12345"
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///feedback"
app.config["SQLALCHEMY_ECHO"] = False
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db_connect(app)
db.create_all()

@app.route("/")
def root():
    if "user" in session:
        return redirect(f"/users/{session['user']}")
    return redirect("/login")

@app.route("/register", methods=["GET", "POST"])
def register_page():
    if "user" in session:
        return redirect(f"/users/{session['user']}")
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        confirm = form.confirm.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        if User.query.filter_by(username=username).one_or_none() != None:
            flash("Username is already taken!")
            return render_template("register.html", form=form)
        if confirm != password:
            flash("Password was not confirmed.")
            return render_template("register.html", form=form)
        if User.query.filter_by(email=email).one_or_none() != None:
            flash("An account with that email already exists! Try a different email.")
            return render_template("register.html", form=form)
        user = User.register(username, password, email, first_name, last_name)
        try:
            db.session.add(user)
            db.session.commit()
        except:
            return render_template("register.html", form=form)
        session["user"] = user.username
        return redirect(f"/users/{session['user']}")

    return render_template("register.html", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user" in session:
        return redirect(f"/users/{session['user']}")
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.login(username, password)
        if user:
            session["user"] = user.username
            return redirect(f"/users/{user.username}")
        else:
            flash("Invalid login. Try again.")
        
    return render_template("login.html", form=form)

@app.route("/logout")
def logout():
    session.pop("user")
    return redirect("/")

@app.route("/users/<string:username>")
def page(username):
    if "user" not in session:
        redirect("/")
    if username != session["user"]:
        print(session["user"])
        return redirect(f"/users/{session['user']}")
    user = User.query.filter_by(username=session["user"]).one()
    feedback = Feedback.query.filter_by(username=session["user"])

    return render_template("user.html", user=user, feedback=feedback)


@app.route("/users/<string:username>/delete", methods=["POST"])
def delete_user(username):
    if "user" not in session:
        redirect("/")
    if username != session["user"]:
        return redirect(f"/users/{session['user']}")
    user = User.query.filter_by(username=session["user"]).one()
    db.session.query(Feedback).filter_by(username=session["user"]).delete()
    db.session.delete(user)
    db.session.commit()
    session.pop("user")
    return redirect("/")

@app.route("/users/<string:username>/feedback/add", methods=["GET", "POST"])
def add_feedback(username):
    if "user" not in session:
        redirect("/")
    if username != session["user"]:
        return redirect(f"/users/{session['user']}")

    form = AddFeedbackForm()
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        feedback = Feedback(title=title, content=content, username=session["user"])
        db.session.add(feedback)
        db.session.commit()
        return redirect(f"/users/{session['user']}")

    return render_template("add-feedback.html", user=username, form=form)

@app.route("/feedback/<int:id>/update", methods=["GET", "POST"])
def update_feedback(id):
    f = Feedback.query.get(id)
    if "user" not in session:
        redirect("/")
    if f.username != session["user"]:
        return redirect(f"/users/{session['user']}")
    
    form = AddFeedbackForm()
    
    if form.validate_on_submit():
        f.title = form.title.data
        f.content = form.content.data
        db.session.commit()
        return redirect(f"/users/{session['user']}")
    
    form.title.data = f.title
    form.content.data = f.content

    return render_template("update-feedback.html", id=id, form=form)

@app.route("/feedback/<int:id>/delete", methods=["POST"])
def delete_feedback(id):
    f = Feedback.query.get(id)
    if "user" not in session:
        redirect("/")
    if f.username != session["user"]:
        return redirect(f"/users/{session['user']}")
    
    db.session.delete(f)
    db.session.commit()
    return redirect(f"/users/{session['user']}")