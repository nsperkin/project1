import os
import requests

from flask import Flask, session, render_template, request, redirect, url_for, jsonify
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

# Try 
@app.route("/")
def login():
	if 'username' in session:
		return render_template("home.html")
	else:
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
		return render_template("login.html", success="Successfully Registered!")
	else:
		return render_template("register.html", message="Username is already taken")

@app.route("/home", methods=["POST", "GET"])
def home():
	if request.method == "GET":
		if 'username' in session:
			return render_template("home.html")
		else:
			return render_template("home.html", message="Error: User not authenticated")

	username = request.form.get("username")
	password = request.form.get("password")

	if(db.execute("SELECT * FROM users WHERE username = :username and password = :password", 
			{"username": username, "password": password}).rowcount==1):
		session['username']=username
		return render_template("home.html")
	else:
		return render_template("login.html", message="Invalid Login Credentials")

@app.route("/logout")
def logout():
	session.pop('username', None)
	return render_template("login.html")

@app.route("/search", methods=["POST", "GET"])
def search():
	if 'username' in session:
		srch = request.form.get("srch")
		srch = "%" + srch + "%"
		result = db.execute("SELECT * FROM books WHERE isbn LIKE :srch OR title LIKE :srch OR author LIKE :srch", 
			{"srch": srch}).fetchall()

		if not result:
			return render_template("search.html", message="No results found!")
		else:
			return render_template("search.html", results=result)
	else:
		return render_template("home.html", message="Error: User not authenticated")

@app.route("/book/<string:isbn>")
def book(isbn):
	if 'username' in session:
		result = db.execute("SELECT * FROM books WHERE isbn=:isbn", {"isbn":isbn}).fetchone()
		res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "7BlWqLEVO1nBlVDLGsl4Aw", "isbns": isbn})
		rating = res.json()['books'][0]['average_rating']
		number = res.json()['books'][0]['ratings_count']
		rev = db.execute("SELECT * FROM reviews WHERE isbn=:isbn", {"isbn":isbn}).fetchall()
		return render_template("book.html", result=result, rating=rating, number=number, rev=rev)
	else:
		return render_template("home.html", message="Error: User not authenticated")

@app.route("/review/<string:isbn>", methods=["POST"])
def review(isbn):
	if 'username' in session:
		username = session['username']
		rating = int(request.form.get("rating"))
		review = request.form.get("review")
		if(db.execute("SELECT * FROM reviews WHERE username = :username and isbn = :isbn",
			{"username": username, "isbn": isbn}).rowcount>0):
			return redirect(url_for('error', isbn=isbn, message="User has already submitted a review!"))
		else:
			db.execute("INSERT INTO reviews (isbn, username, rating, review) VALUES (:isbn, :username, :rating, :review)",
				{"isbn":isbn, "username":username, "rating":rating, "review":review})
			db.commit()
			return redirect(url_for('book', isbn=isbn))
	else:
		return render_template("home.html", message="Error: User not authenticated")

@app.route("/error/<string:isbn>/<string:message>")
def error(isbn, message):
	return render_template("error.html", isbn=isbn, message=message)

@app.route("/api/<string:isbn>")
def book_api(isbn):
	result = db.execute("SELECT * FROM books WHERE isbn=:isbn", {"isbn":isbn}).fetchone()
	if result is None:
		return jsonify({"error": "Invalid isbn"}), 404
	res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "7BlWqLEVO1nBlVDLGsl4Aw", "isbns": isbn})
	rating = res.json()['books'][0]['average_rating']
	number = res.json()['books'][0]['ratings_count']
	return jsonify({
		"title": result.title,
		"author": result.author,
		"year": result.year,
		"isbn": result.isbn,
		"review_count": number,
		"average_score": rating
		})

