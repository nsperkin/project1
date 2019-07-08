import os
import requests

from flask import Flask, session, render_template, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "7BlWqLEVO1nBlVDLGsl4Aw", "isbns": "9781632168146"})

# class for book objects
class book:
	def __init__(self, title, author, pub_year, isbn, reviews, rating, num_ratings):
		self.title = title
		self.author = author
		self.pub_year = pub_year
		self.isbn = isbn
		self.reviews = reviews
		self.rating = rating
		self.num_ratings = num_ratings


# Try 
@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/register")
def register():
	return render_template("register.html")

@app.route("/user", methods=["POST"])
def user():
	password = request.form.get("password")
	confirm = request.form.get("confirm")
	username = request.form.get("username")

	if(password != confirm):
		return render_template("register.html", message="Passwords do not match.")
	if db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).rowcount == 0:
		db.execute("INSERT INTO users (username, password) VALUES (:username, :password)",
              {"username": username, "password": password})
		db.commit()
		return render_template("login.html")
	else:
		return render_template("register.html", message="Username is already taken")
