import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    review = db.relationship("Reviews", backref="user", lazy=True)

class Books(db.Model):
    __tablename__ = "books"
    isbn=db.Column(db.VARCHAR, primary_key=True, nullable=False)
    title = db.Column(db.String, nullable=False)
    author = db.Column(db.String, nullable=False)
    year=db.Column(db.Integer, nullable=False)
    review = db.relationship("Reviews", backref="books", lazy=True)
    def add_review(self, score, text , book , userid):
        p = Reviews(score=score,text=text, book=book, userid=userid)
        db.session.add(p)
        db.session.commit()

class Reviews(db.Model):
    __tablename__ = "reviews"
    id=db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Integer, nullable=False)
    text= db.Column(db.String, nullable=False)
    book = db.Column(db.VARCHAR, db.ForeignKey("books.isbn"), nullable=False)
    userid = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
