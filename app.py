import os, re

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required, brl, is_brazilian_numeric

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
    return render_template("index.html", active_page="geral")

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

    despesa_fixa = db.execute("SELECT SUM(valor) AS valor FROM despesas WHERE user_id = ? AND tipo = 'pessoal' AND escopo = 'fixo' AND strftime('%Y', time) = strftime('%Y', 'now') AND strftime('%m', time) = strftime('%m', 'now')", session["user_id"])
    despesa_fixa_anterior = db.execute(
                            "SELECT SUM(valor) AS valor FROM despesas WHERE user_id = ? AND tipo = 'pessoal' AND escopo = 'fixo' AND time BETWEEN date('now', 'start of month', '-1 month') AND date('now', 'start of month', '-1 day')", session["user_id"]
                            )
    if despesa_fixa[0]["valor"] == None:
        despesa_fixa[0]["valor"] = 0
    despesa_variavel = db.execute("SELECT SUM(valor) AS valor FROM despesas WHERE user_id = ? AND tipo = 'pessoal' AND escopo = 'variavel' AND strftime('%Y', time) = strftime('%Y', 'now') AND strftime('%m', time) = strftime('%m', 'now')", session["user_id"])
    despesa_variavel_anterior = db.execute(
                            "SELECT SUM(valor) AS valor FROM despesas WHERE user_id = ? AND tipo = 'pessoal' AND escopo = 'variavel' AND time BETWEEN date('now', 'start of month', '-1 month') AND date('now', 'start of month', '-1 day')", session["user_id"]
                            )
    if despesa_variavel[0]["valor"] == None:
        despesa_variavel[0]["valor"] = 0
    
    return render_template("pessoal.html", cFixo=cFixo, cVariavel=cVariavel, active_page="pessoal", despesa_fixa=despesa_fixa[0]["valor"], despesa_fixa_anterior=despesa_fixa_anterior[0]["valor"], despesa_variavel=despesa_variavel[0]["valor"], despesa_variavel_anterior=despesa_variavel_anterior[0]["valor"])


@app.route("/pessoal_fixa", methods=["POST"])
@login_required
def pessoal_fixa():
    if not request.form.get("selectfx"):
        flash("Favor selecionar categoria da despesa.", "error")
        return redirect("/pessoal")
        
    elif not request.form.get("inputfx"):
        flash("Favor digitar o valor da despesa.", "error")
        return redirect("/pessoal")
    
    elif is_brazilian_numeric(request.form.get("inputfx")) == False:
        flash("Valor pode conter apenas números.", "error")
        return redirect("/pessoal")
    
    value = request.form.get("inputfx")
    value_float = float(value.replace(',', '.'))

    db.execute(
        "INSERT INTO despesas (user_id, escopo, tipo, categoria, valor) VALUES (?, ?, ?, ?, ?)", 
        session["user_id"], "fixo", "pessoal", request.form.get("selectfx"), value_float
        )

    return redirect("/pessoal")


@app.route("/pessoal_variavel", methods=["POST"])
@login_required
def pessoal_variavel():
    if not request.form.get("selectvr"):
        flash("Favor selecionar categoria da despesa.", "error")
        return redirect("/pessoal")
    
    elif not request.form.get("inputvr"):
        flash("Favor digitar o valor da despesa.", "error")
        return redirect("/pessoal")
    
    elif not request.form.get("inputvr").isnumeric():
        flash("Valor pode conter apenas números.", "error")
        return redirect("/pessoal")
    
    return redirect("/pessoal")


@app.route("/empresa")
@login_required
def empresa():
    """Gastos da Empresa"""

    cFixo = db.execute("SELECT categoria FROM categorias WHERE escopo = 'empresa' AND tipo = 'fixo'")
    cVariavel = db.execute("SELECT categoria FROM categorias WHERE escopo = 'empresa' AND tipo = 'variavel'")


    return render_template("empresa.html", cFixo=cFixo, cVariavel=cVariavel, active_page="empresa")


@app.route("/empresa_fixa", methods=["POST"])
@login_required
def empresa_fixa():
    if not request.form.get("selectfx"):
        flash("Favor selecionar categoria da despesa.", "error")
        return redirect("/empresa")
        
    elif not request.form.get("inputfx"):
        flash("Favor digitar o valor da despesa.", "error")
        return redirect("/empresa")
    
    elif not request.form.get("inputfx").isnumeric():
        flash("Valor pode conter apenas números.", "error")
        return redirect("/empresa")

    return redirect("/empresa")


@app.route("/empresa_variavel", methods=["POST"])
@login_required
def empresa_variavel():
    if not request.form.get("selectvr"):
        flash("Favor selecionar categoria da despesa.", "error")
        return redirect("/empresa")
    
    elif not request.form.get("inputvr"):
        flash("Favor digitar o valor da despesa.", "error")
        return redirect("/empresa")
    
    elif not request.form.get("inputvr").isnumeric():
        flash("Valor pode conter apenas números.", "error")
        return redirect("/empresa")
    
    return redirect("/empresa")


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
