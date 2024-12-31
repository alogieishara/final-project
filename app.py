import os, re


from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from collections import defaultdict


from helpers import login_required, brl, is_brazilian_numeric, generate_month_range

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
    despesas_total_variavel = db.execute("SELECT strftime('%Y-%m', time) AS year_month, SUM(CASE WHEN escopo = 'pessoal' THEN valor ELSE 0 END) AS despesa_pessoal, SUM(CASE WHEN escopo = 'empresa' THEN valor ELSE 0 END) AS despesa_empresa FROM despesas WHERE user_id = ? AND tipo = 'variavel' GROUP BY year_month ORDER BY year_month", session["user_id"])

    despesas_total_fixas = db.execute("SELECT strftime('%Y-%m', time) AS year_month, SUM(CASE WHEN escopo = 'pessoal' THEN valor ELSE 0 END) AS despesa_pessoal, SUM(CASE WHEN escopo = 'empresa' THEN valor ELSE 0 END) AS despesa_empresa FROM despesas WHERE user_id = ? AND tipo = 'fixo' GROUP BY year_month ORDER BY year_month", session["user_id"])

     # List of month names in Portuguese
    months_pt = [
        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ]

        # Convert year_month to a more readable format (e.g., "Dezembro 2024")
    for item in despesas_total_variavel:
        month_number = int(item['year_month'][5:7]) - 1  # Get the 0-indexed month number
        year = item['year_month'][:4]
        formatted_month = f"{months_pt[month_number]} {year}"
        item['formatted_month'] = formatted_month

    despesas_total_fixas = sorted(despesas_total_fixas, key=lambda x: x['year_month'])

    
    x_pessoal = 0
    x_empresa = 0

    for item in despesas_total_fixas:
        item['despesa_pessoal'] = item['despesa_pessoal'] + x_pessoal
        x_pessoal = item['despesa_pessoal']

        item['despesa_empresa'] = item['despesa_empresa'] + x_empresa
        x_empresa = item['despesa_empresa']


    
    
    # Gather all year_month keys
    all_months = sorted(set(item['year_month'] for item in despesas_total_fixas + despesas_total_variavel))

    # Generate the full range of months
    start_month, end_month = all_months[0], all_months[-1]
    month_range = generate_month_range(start_month, end_month)

    # Dictionary to store combined totals by month
    combined_totals = defaultdict(lambda: {'despesa_pessoal': 0, 'despesa_empresa': 0})

    # Fill missing fixed expenses for each month
    fixed_totals = defaultdict(lambda: {'despesa_pessoal': 0, 'despesa_empresa': 0})
    last_fixed = None  # Keeps track of the most recent fixed expenses

    for month in month_range:
        # Check for despesas_total_fixas data
        fixed_item = next((item for item in despesas_total_fixas if item['year_month'] == month), None)
        if fixed_item:
            last_fixed = fixed_item
        # Propagate forward only if a fixed item has been encountered
        if last_fixed:
            fixed_totals[month] = {'despesa_pessoal': last_fixed['despesa_pessoal'], 'despesa_empresa': last_fixed['despesa_empresa']}

    # Add variable expenses
    for item in despesas_total_variavel:
        combined_totals[item['year_month']]['despesa_pessoal'] += item['despesa_pessoal']
        combined_totals[item['year_month']]['despesa_empresa'] += item['despesa_empresa']

    # Add fixed expenses to each month
    for month in month_range:
        combined_totals[month]['despesa_pessoal'] += fixed_totals[month]['despesa_pessoal']
        combined_totals[month]['despesa_empresa'] += fixed_totals[month]['despesa_empresa']

    # Convert the dictionary to a sorted list of results
    result = [
        {'year_month': month, 
        'despesa_pessoal': combined_totals[month]['despesa_pessoal'], 
        'despesa_empresa': combined_totals[month]['despesa_empresa']} 
        for month in month_range
    ]

    

    for item in result:
        month_number = int(item['year_month'][5:7]) - 1  # Get the 0-indexed month number
        year = item['year_month'][:4]
        formatted_month = f"{months_pt[month_number]} {year}"
        item['formatted_month'] = formatted_month

    return render_template("index.html", active_page="geral", combined_data=result)





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

    despesa_fixa = db.execute("SELECT SUM(valor) AS valor FROM despesas WHERE user_id = ? AND tipo = 'fixo' AND escopo = 'pessoal'", session["user_id"])
    despesa_fixa_anterior = db.execute("SELECT SUM(valor) AS valor FROM despesas WHERE user_id = ? AND tipo = 'fixo' AND escopo = 'pessoal' AND strftime('%Y-%m', time) != strftime('%Y-%m', 'now')", session["user_id"])
    print(despesa_fixa_anterior)
    if despesa_fixa[0]["valor"] == None:
        despesa_fixa[0]["valor"] = 0
    despesa_variavel = db.execute("SELECT SUM(valor) AS valor FROM despesas WHERE user_id = ? AND tipo = 'variavel' AND escopo = 'pessoal' AND strftime('%Y', time) = strftime('%Y', 'now') AND strftime('%m', time) = strftime('%m', 'now')", session["user_id"])
    despesa_variavel_anterior = db.execute(
                            "SELECT SUM(valor) AS valor FROM despesas WHERE user_id = ? AND tipo = 'variavel' AND escopo = 'pessoal' AND time BETWEEN date('now', 'start of month', '-1 month') AND date('now', 'start of month', '-1 day')", session["user_id"]
                            )
    if despesa_variavel[0]["valor"] == None:
        despesa_variavel[0]["valor"] = 0

    lista_fixo = db.execute("SELECT strftime('%Y-%m-%d', time) AS formatted_date, categoria, valor, id FROM despesas WHERE user_id = ? AND escopo = 'pessoal' AND tipo = 'fixo'", session["user_id"])
    lista_variavel = db.execute("SELECT strftime('%Y-%m-%d', time) AS formatted_date, categoria, valor, id FROM despesas WHERE user_id = ? AND escopo = 'pessoal' AND tipo = 'variavel'", session["user_id"])
    
    return render_template("pessoal.html", cFixo=cFixo, cVariavel=cVariavel, active_page="pessoal", despesa_fixa=despesa_fixa[0]["valor"], despesa_fixa_anterior=despesa_fixa_anterior[0]["valor"], despesa_variavel=despesa_variavel[0]["valor"], despesa_variavel_anterior=despesa_variavel_anterior[0]["valor"], lista_fixo=lista_fixo, lista_variavel=lista_variavel)


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
        session["user_id"], "pessoal", "fixo", request.form.get("selectfx"), value_float
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
    
    elif is_brazilian_numeric(request.form.get("inputvr")) == False:
        flash("Valor pode conter apenas números.", "error")
        return redirect("/pessoal")
    
    value = request.form.get("inputvr")
    value_float = float(value.replace(',', '.'))

    db.execute(
        "INSERT INTO despesas (user_id, escopo, tipo, categoria, valor) VALUES (?, ?, ?, ?, ?)", 
        session["user_id"], "pessoal", "variavel", request.form.get("selectvr"), value_float
        )
    
    return redirect("/pessoal")


@app.route("/empresa")
@login_required
def empresa():
    """Gastos da Empresa"""

    cFixo = db.execute("SELECT categoria FROM categorias WHERE escopo = 'empresa' AND tipo = 'fixo'")
    cVariavel = db.execute("SELECT categoria FROM categorias WHERE escopo = 'empresa' AND tipo = 'variavel'")

    despesa_fixa = db.execute("SELECT SUM(valor) AS valor FROM despesas WHERE user_id = ? AND tipo = 'fixo' AND escopo = 'empresa'", session["user_id"])
    despesa_fixa_anterior = db.execute("SELECT SUM(valor) AS valor FROM despesas WHERE user_id = ? AND tipo = 'fixo' AND escopo = 'empresa' AND strftime('%Y-%m', time) != strftime('%Y-%m', 'now')", session["user_id"])
    if despesa_fixa[0]["valor"] == None:
        despesa_fixa[0]["valor"] = 0
    despesa_variavel = db.execute("SELECT SUM(valor) AS valor FROM despesas WHERE user_id = ? AND tipo = 'variavel' AND escopo = 'empresa' AND strftime('%Y', time) = strftime('%Y', 'now') AND strftime('%m', time) = strftime('%m', 'now')", session["user_id"])
    despesa_variavel_anterior = db.execute(
                            "SELECT SUM(valor) AS valor FROM despesas WHERE user_id = ? AND tipo = 'variavel' AND escopo = 'empresa' AND time BETWEEN date('now', 'start of month', '-1 month') AND date('now', 'start of month', '-1 day')", session["user_id"]
                            )
    if despesa_variavel[0]["valor"] == None:
        despesa_variavel[0]["valor"] = 0

    lista_fixo = db.execute("SELECT strftime('%Y-%m-%d', time) AS formatted_date, categoria, valor, id FROM despesas WHERE user_id = ? AND escopo = 'empresa' AND tipo = 'fixo'", session["user_id"])
    lista_variavel = db.execute("SELECT strftime('%Y-%m-%d', time) AS formatted_date, categoria, valor, id FROM despesas WHERE user_id = ? AND escopo = 'empresa' AND tipo = 'variavel'", session["user_id"])
    


    return render_template("empresa.html", cFixo=cFixo, cVariavel=cVariavel, active_page="empresa", despesa_fixa=despesa_fixa[0]["valor"], despesa_fixa_anterior=despesa_fixa_anterior[0]["valor"], despesa_variavel=despesa_variavel[0]["valor"], despesa_variavel_anterior=despesa_variavel_anterior[0]["valor"], lista_fixo=lista_fixo, lista_variavel=lista_variavel)


@app.route("/empresa_fixa", methods=["POST"])
@login_required
def empresa_fixa():
    if not request.form.get("selectfx"):
        flash("Favor selecionar categoria da despesa.", "error")
        return redirect("/empresa")
        
    elif not request.form.get("inputfx"):
        flash("Favor digitar o valor da despesa.", "error")
        return redirect("/empresa")
    
    elif is_brazilian_numeric(request.form.get("inputfx")) == False:
        flash("Valor pode conter apenas números.", "error")
        return redirect("/empresa")
    
    value = request.form.get("inputfx")
    value_float = float(value.replace(',', '.'))

    db.execute(
        "INSERT INTO despesas (user_id, escopo, tipo, categoria, valor) VALUES (?, ?, ?, ?, ?)", 
        session["user_id"], "empresa", "fixo", request.form.get("selectfx"), value_float
        )

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
    
    elif is_brazilian_numeric(request.form.get("inputvr")) == False:
        flash("Valor pode conter apenas números.", "error")
        return redirect("/empresa")
    
    value = request.form.get("inputvr")
    value_float = float(value.replace(',', '.'))

    db.execute(
        "INSERT INTO despesas (user_id, escopo, tipo, categoria, valor) VALUES (?, ?, ?, ?, ?)", 
        session["user_id"], "empresa", "variavel", request.form.get("selectvr"), value_float
        )
    
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
    

@app.route("/delete", methods=["POST"])
def delete():
    """Deletes row from table"""
    id = request.form.get("id")
    if id:
        db.execute("DELETE FROM despesas WHERE id = ?", id)
    return redirect(request.referrer)

    
@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

if __name__ == '__main__':
    app.run(host='0.0.0.0')
