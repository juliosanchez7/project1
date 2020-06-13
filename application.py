import os
import requests
from flask import Flask, session
from flask_session import Session
from flask import Flask, render_template, request, jsonify, redirect, url_for
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from models import *


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config.update(SECRET_KEY=os.urandom(24))
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
db.init_app(app)
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))



@app.route("/")
def index():

    return render_template("index.html")

@app.route("/register", methods=["POST"])
def register():
    #####REGISTER NEW USER ON THE DB######
    # Get form information.
    username = request.form.get("username")
    password = request.form.get("password")
    #Search if username exists
    user=db.execute('SELECT * FROM Users WHERE username = :username', {"username": username}).fetchone()
    if not user:
        #Create new username
        db.execute('INSERT INTO Users( username,password) values (:username,:password);' , {"username": username , "password": password})
        db.commit()
        return render_template("success.html", message="user created")
    else:
        return render_template("error.html", message="Username aready exists")
@app.route("/log", methods=["POST"])
def log():
    ######Log old usernames####

    # Get form information.
    username = request.form.get("username")
    password = request.form.get("password")
    #Search the username and password on the database
    user= db.execute('SELECT * FROM Users WHERE username = :username and password = :password', {"username": username, "password": password   }).fetchone()
    if not user :
        return render_template("error.html", message="Username does not exists")
    else:
    #input session information
        session['loggedin'] = True
        session['username'] = username
        session['userid']=int(user.id)
        return render_template("welcome.html", username=username)

@app.route("/search", methods = ['GET', 'POST'])

def search():
    ####SHOWS LIST OF BOOKS

    #Make shure if log in
    if 'loggedin' not in session:
        return render_template("error.html", message="Log in first.")
    elif session['loggedin'] == True:
        books = db.execute("SELECT * FROM books").fetchall()
        return render_template('search.html', books=books)


@app.route("/books/<string:isbn>")
#BOOK INFORMATION: REVIEWS FROM GOODREADS AND INSERT A NEW REVIEW AND COMMENT
def book(isbn):
    #Make shure if log in
    if 'loggedin' not in session:
        return render_template("error.html", message="Log in first.")

    elif session['loggedin'] == True:
        #Select corresponding book
        books = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
        oldusername = session['username']
        reviews = db.execute("SELECT * FROM reviews WHERE book = :book",
                                {"book": isbn}).fetchall()
        #Import goodreads reviews
        res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "nRwun03z90nYQoCkaN5jEg", "isbns": isbn})
        if res.status_code != 200:
            #If not review on goodreads
            average_rating=[]
            work_ratings_count=[]
            return render_template('review.html', oldusername=oldusername, books=books, reviews=reviews, average_rating=average_rating,work_ratings_count=work_ratings_count)
        else:
            #If a review on gooreads is find
            data = res.json()
            print(data)
            average_rating = data['books'][0]['average_rating']
            work_ratings_count = data['books'][0]['work_ratings_count']
            return render_template('review.html', oldusername=oldusername, books=books, reviews=reviews,average_rating=average_rating,work_ratings_count=work_ratings_count)
@app.route("/logout")
def logout():
    #LEAVE SESSION
    session.pop('loggedin', False)
    session.pop('username', None)
    session.pop('userid', None)
    session.pop('loggedin', False)
    return render_template('index.html')

@app.route("/reviewpost", methods=["POST"])
#SAVE REVIEW ON THE DB
def reviewpost():
    score = int(request.form.get("score"))
    text = str(request.form.get("comment"))
    book_id = request.form.get("books")
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": book_id}).fetchone()
    userid = int(session['userid'])
    #Make sure that user only post one review for book
    review= db.execute('SELECT * FROM reviews WHERE userid = :userid and book = :book', {"userid": userid, "book": book_id   }).fetchone()
    if not review:
        print("REVIEW", review)
        db.execute('INSERT INTO reviews( score,text,book,userid) values (:score,:text,:book,:userid);' , {"score": score , "text": text, "book": book_id,"userid": userid })
        db.commit()
        return render_template("success.html",message="Review summited!")
    else:
        return render_template("error.html", message="You have already summit a review for this book")
@app.route("/api/<string:isbn>")
#API
def api(isbn):
    #getting book info from my db
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
    if book is None:
        #error 404, bad isbn
        return jsonify({"error": "Isbn not found"}), 404
    #get iformation from goodreads
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={'key': 'n8mHOUl5fgaj7uEiG5A2kA', 'isbns': book.isbn})
    if res.status_code != 200:
        #if does not exist goodreads review: average_rating and work_ratings_count is clear
        average_rating = ''
        work_ratings_count = ''
    else:
        #safe data from goodreads
        data = res.json()
        average_rating = data['books'][0]['average_rating']
        work_ratings_count = data['books'][0]['work_ratings_count']
        #Create json
    return jsonify({
            "title": book.title,
            "author": book.author,
            "year": book.year,
            "isbn": book.isbn,
            "review_count": work_ratings_count,
            "average_score": average_rating,
        })
