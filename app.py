import os, re

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required, brl

# COMMANDS:
# npx tailwindcss -i ./static/src/input.css -o ./static/dist/css/output.css --watch
# python -m flask run --debug --host=0.0.0.0
# you need to be inside the project folder to submit50

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["brl"] = brl

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///logcash.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@app.route("/index")
@login_required # if you go to this route not logged in, you'll be redirected to /login
def index():
    """Homepage"""
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    error = "none"

    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            error = "username"
            return render_template("login.html", error=error)

        # Ensure password was submitted
        elif not request.form.get("password"):
            error = "password"
            return render_template("login.html", error=error)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            error = "invalid"
            return render_template("login.html", error=error)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html", error=error)
    
@app.route("/pessoal")
@login_required # if you go to this route not logged in, you'll be redirected to /login
def pessoal():
    """Gastos Pessoais"""
    cFixo = db.execute("SELECT categoria FROM categorias WHERE escopo = 'pessoal' AND tipo = 'fixo'")
    cVariavel = db.execute("SELECT categoria FROM categorias WHERE escopo = 'pessoal' AND tipo = 'variavel'")
    return render_template("pessoal.html", cFixo=cFixo, cVariavel=cVariavel)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register new user"""
    error = "none"

    if request.method == "POST":
        # Ensure email was submitted
        if not request.form.get("email"):
            error = "email"
            return render_template("register.html", error=error)
        
        # Ensure email is correctly formatted
        EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")
        
        if not EMAIL_REGEX.match(request.form.get("email")):
            error = "emailincorrect"
            return render_template("register.html", error=error)

        # Ensure username was submitted
        if not request.form.get("username"):
            error = "username"
            return render_template("register.html", error=error)

        # Ensure password was submitted
        elif not request.form.get("password"):
            error = "password"
            return render_template("register.html", error=error)
        
        # Check if password fields match
        elif request.form.get("password") != request.form.get("confirmation"):
            error = "match"
            return render_template("register.html", error=error)

        # Hash the password
        password = request.form.get("password")
        phash = generate_password_hash(password, method='pbkdf2', salt_length=16)

        try:
            db.execute(
                "INSERT INTO users (username, hash, email) VALUES(?, ?, ?)", request.form.get(
                    "username"), phash, request.form.get(
                    "email")
            )
            # tries are executed one by one until an exception happens

        except ValueError:
            error = "invalid"
            return render_template("register.html", error=error)
        
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )
        session["user_id"] = rows[0]["id"]

        return redirect("/")
    
    else:
        return render_template("register.html", error=error)
    
@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

if __name__ == '__main__':
    app.run(host='0.0.0.0')
