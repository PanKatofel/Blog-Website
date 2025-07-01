import os

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Text, ForeignKey
from sqlalchemy.exc import IntegrityError
from dataclasses import dataclass
from datetime import datetime
from flask_login import UserMixin

class Base(DeclarativeBase):
    pass
db = SQLAlchemy(model_class=Base)


@dataclass
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comment", back_populates="author")

@dataclass
class BlogPost(db.Model):
    __tablename__ = "posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False, default=lambda: datetime.now().strftime("%m/%d/%Y"))
    body: Mapped[str] = mapped_column(Text, nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)
    author = relationship("User", back_populates="posts")
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    comments = relationship("Comment", back_populates="blog")


@dataclass
class Comment(db.Model):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(String, nullable=False)
    author = relationship("User", back_populates="comments")
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    blog = relationship("BlogPost", back_populates="comments")
    blog_id: Mapped[int] = mapped_column(Integer, ForeignKey("posts.id"))


class Database():

    def __init__(self, app):
        self.app = app
        self.app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI", "sqlite:///posts.db")
        db.init_app(self.app)
        with self.app.app_context():
            db.create_all()

    def get_all_posts(self):
        return BlogPost.query.all()

    def get_post_by_id(self, id):
        return BlogPost.query.filter_by(id=id).first()

    def add_post(self, title, subtitle, body, img_url, author_id):
        post_to_add = BlogPost(
            title=title,
            subtitle=subtitle,
            body=body,
            img_url=img_url,
            author_id=author_id
        )
        db.session.add(post_to_add)
        db.session.commit()

    def patch_post(self, id, title, subtitle, body, author, img_url):
        post_to_patch = self.get_post_by_id(id)
        post_to_patch.title = title
        post_to_patch.subtitle = subtitle
        post_to_patch.body = body
        post_to_patch.author = author
        post_to_patch.img_url = img_url
        db.session.commit()

    def delete_post(self, id):
        BlogPost.query.filter_by(id=id).delete()
        db.session.commit()

#-----------------------------------------------------------------

    def create_user(self, name, email, password):
        try:
            new_user = User(
                name=name,
                email=email,
                password=password
            )
            db.session.add(new_user)
            db.session.commit()
            return new_user
        except IntegrityError:
            return False

    def get_user_by_email(self, email):
        user = User.query.filter_by(email=email).first()
        return user

    def get_user_by_id(self, id):
        user = User.query.filter_by(id=id).first()
        return user

#-------------------------------------------------------------------


    def create_comment(self, text, author_id, blog_id):
        comment = Comment(
            text=text,
            author_id=author_id,
            blog_id=blog_id
        )
        db.session.add(comment)
        db.session.commit()
