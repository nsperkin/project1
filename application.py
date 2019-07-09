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

		print(result)
		for i in result:
			print(i)

		if not result:
			return render_template("search.html", message="No results found!")
		else:
			return render_template("search.html", result=result)
	else:
		return render_template("home.html", message="Error: User not authenticated")