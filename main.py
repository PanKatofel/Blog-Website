from flask import Flask, render_template, request, redirect, url_for, abort, flash, get_flashed_messages
from flask_bootstrap import Bootstrap5
from database import Database
from forms import PostForm, RegisterForm, LoginForm, CommentForm
from flask_ckeditor import CKEditor
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, current_user, logout_user
from functools import wraps
from bs4 import BeautifulSoup
from env import load_env
import os


# ----------------------------------------------
load_env()

app = Flask(__name__)
app.config["CKEDITOR_CONFIG"] = {"versionCheck": False}
app.config["CKEDITOR_PKG_TYPE"] = 'standart'
app.config["CKEDITOR_SERVE_LOCAL"] = True
app.secret_key = os.environ["APP_KEY"]
ckeditor = CKEditor(app)
login_manager = LoginManager()
login_manager.init_app(app)
db = Database(app)
Bootstrap5(app)

# ------------------------------------------------------
@login_manager.user_loader
def load_user(user_id):
    return db.get_user_by_id(user_id)

@app.context_processor
def inject_user():
    admin_logged = False
    if current_user.is_authenticated and current_user.id == 1:
        admin_logged = True
    return dict(logged_in=current_user.is_authenticated,
                admin_logged=admin_logged)

def admin_only(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated and current_user.id == 1:
            return func(*args, **kwargs)
        return abort(403)
    return decorated_function

def remove_white_paragraphs(html):
    soup = BeautifulSoup(html, "html.parser")
    for paragraph in soup.find_all("p"):
        if len(paragraph.getText(strip=True)) == 0:
            paragraph.extract()
    for enter in soup.find_all("br"):
        enter.extract()
    return str(soup)


# --------------------------------------------------------
@app.route('/')
def home():
    posts = db.get_all_posts()
    return render_template("index.html", all_posts=posts)


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = db.create_user(name=request.form["name"], email=request.form["email"],
                              password=generate_password_hash(request.form["password"], method="pbkdf2", salt_length=8))
        if not user:
            return render_template("login.html", form=LoginForm(), message="This email is already in use, log in instead!")
        login_user(user)
        return redirect(url_for("home"))

    return render_template("register.html", form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    try:
        message = get_flashed_messages(with_categories=True)[0][1]
    except IndexError:
        message = None

    if form.validate_on_submit():
        password = request.form["password"]
        email = request.form["email"]
        user = db.get_user_by_email(email)
        if user:
            if check_password_hash(pwhash=user.password, password=password):
                login_user(user)
                return redirect(url_for('home'))
            return render_template('login.html', message="Incorrect password. Try again!", form=form)
        return render_template('login.html', message="User with this email does not exist!", form=form)

    return render_template('login.html', form=form, message=message)


@app.route('/log-out')
def log_out():
    logout_user()
    return redirect(url_for('home'))


@app.route('/read/<int:post_id>', methods=["GET", "POST"])
def show_post(post_id):
    requested_post = db.get_post_by_id(post_id)
    form = CommentForm()

    if form.validate_on_submit():
        if current_user.is_authenticated:
            text = remove_white_paragraphs(request.form["text"])
            db.create_comment(text=text,
                              author_id=current_user.id,
                              blog_id=post_id)
            return redirect(url_for("show_post", post_id=post_id))
        flash(message="Login before posting a comment")
        return redirect(url_for("login"))

    return render_template("post.html", post=requested_post, form=form)


@app.route('/make-post', methods=["GET", "POST"])
@admin_only
def make_post():
    form = PostForm()
    if form.validate_on_submit():
        db.add_post(
            title=request.form["title"], subtitle=request.form["subtitle"],
            body=request.form["body"], author_id=current_user.id,
            img_url=request.form["img_url"]
        )
        return redirect(url_for("home"))

    return render_template("make-post.html", form=form, page="make")


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post = db.get_post_by_id(post_id)
    form = PostForm(title=post.title, subtitle=post.subtitle,
                    author=post.author, img_url=post.img_url,
                    body=post.body)

    if form.validate_on_submit():
        db.patch_post(id=post_id, title=request.form["title"], subtitle=request.form["subtitle"],
            body=request.form["body"], author=request.form["author"],
            img_url=request.form["img_url"])
        return redirect(url_for("show_post", post_id=post_id))

    return render_template("make-post.html", form=form, page="edit")


@app.route("/delete/<int:post_id>")
@admin_only
def delete(post_id):
    db.delete_post(post_id)
    return redirect(url_for("home"))


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


# -------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=False, port=5003)
