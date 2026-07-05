import os
from datetime import date

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///cloud_costs.db")

CATEGORIES = ["Compute", "Storage", "Network", "Database"]


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username:
            return apology("must provide username", 400)
        elif not password:
            return apology("must provide password", 400)
        elif not confirmation:
            return apology("must confirm password", 400)
        elif password != confirmation:
            return apology("passwords do not match", 400)

        hash_senha = generate_password_hash(password)

        try:
            new_user_id = db.execute(
                "INSERT INTO users (username, hash) VALUES (?, ?)", username, hash_senha
            )
        except ValueError:
            return apology("username already exists", 400)

        session["user_id"] = new_user_id
        return redirect("/")

    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()

    if request.method == "POST":
        if not request.form.get("username"):
            return apology("must provide username", 403)
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        session["user_id"] = rows[0]["id"]
        return redirect("/")

    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/")
@login_required
def index():
    user_id = session["user_id"]

    total_row = db.execute(
        """
        SELECT SUM(amount) AS total FROM expenses
        WHERE user_id = ? AND strftime('%Y-%m', expense_date) = strftime('%Y-%m', 'now')
        """,
        user_id,
    )
    total_mes = total_row[0]["total"] or 0

    por_provedor = db.execute(
        """
        SELECT providers.name AS name, SUM(expenses.amount) AS total
        FROM expenses
        JOIN providers ON expenses.provider_id = providers.id
        WHERE expenses.user_id = ? AND strftime('%Y-%m', expenses.expense_date) = strftime('%Y-%m', 'now')
        GROUP BY providers.name
        """,
        user_id,
    )

    por_categoria = db.execute(
        """
        SELECT category, SUM(amount) AS total
        FROM expenses
        WHERE user_id = ? AND strftime('%Y-%m', expense_date) = strftime('%Y-%m', 'now')
        GROUP BY category
        """,
        user_id,
    )

    orcamentos = db.execute(
        "SELECT category, monthly_limit FROM budgets WHERE user_id = ?", user_id
    )

    gastos_por_categoria = {row["category"]: row["total"] for row in por_categoria}

    alertas = []
    for orcamento in orcamentos:
        gasto = gastos_por_categoria.get(orcamento["category"], 0)
        if gasto > orcamento["monthly_limit"]:
            alertas.append(
                {
                    "category": orcamento["category"],
                    "gasto": gasto,
                    "limite": orcamento["monthly_limit"],
                }
            )

    return render_template(
        "index.html",
        total_mes=total_mes,
        por_provedor=por_provedor,
        por_categoria=por_categoria,
        alertas=alertas,
    )


@app.route("/expenses", methods=["GET", "POST"])
@login_required
def expenses():
    user_id = session["user_id"]

    if request.method == "POST":
        provider_id = request.form.get("provider_id")
        category = request.form.get("category")
        amount = request.form.get("amount")
        expense_date = request.form.get("expense_date")

        if not provider_id:
            return apology("must select a provider", 400)

        if category not in CATEGORIES:
            return apology("invalid category", 400)

        try:
            amount = float(amount)
        except (TypeError, ValueError):
            return apology("amount must be a number", 400)

        if amount <= 0:
            return apology("amount must be positive", 400)

        if not expense_date:
            return apology("must provide a date", 400)

        db.execute(
            """
            INSERT INTO expenses (user_id, provider_id, category, amount, expense_date)
            VALUES (?, ?, ?, ?, ?)
            """,
            user_id, provider_id, category, amount, expense_date,
        )

        return redirect("/expenses")

    else:
        providers = db.execute("SELECT * FROM providers")

        lista = db.execute(
            """
            SELECT expenses.id, providers.name AS provider, expenses.category,
                   expenses.amount, expenses.expense_date
            FROM expenses
            JOIN providers ON expenses.provider_id = providers.id
            WHERE expenses.user_id = ?
            ORDER BY expenses.expense_date DESC
            """,
            user_id,
        )

        return render_template(
            "expenses.html",
            providers=providers,
            categories=CATEGORIES,
            lista=lista,
            hoje=date.today().isoformat(),
        )


@app.route("/expenses/delete/<int:expense_id>")
@login_required
def delete_expense(expense_id):
    user_id = session["user_id"]
    db.execute(
        "DELETE FROM expenses WHERE id = ? AND user_id = ?", expense_id, user_id
    )
    return redirect("/expenses")


@app.route("/budgets", methods=["GET", "POST"])
@login_required
def budgets():
    user_id = session["user_id"]

    if request.method == "POST":
        category = request.form.get("category")
        monthly_limit = request.form.get("monthly_limit")

        if category not in CATEGORIES:
            return apology("invalid category", 400)

        try:
            monthly_limit = float(monthly_limit)
        except (TypeError, ValueError):
            return apology("limit must be a number", 400)

        if monthly_limit <= 0:
            return apology("limit must be positive", 400)

        db.execute(
            """
            INSERT INTO budgets (user_id, category, monthly_limit)
            VALUES (?, ?, ?)
            ON CONFLICT (user_id, category) DO UPDATE SET monthly_limit = excluded.monthly_limit
            """,
            user_id, category, monthly_limit,
        )

        return redirect("/budgets")

    else:
        lista = db.execute(
            "SELECT category, monthly_limit FROM budgets WHERE user_id = ?", user_id
        )
        return render_template("budgets.html", categories=CATEGORIES, lista=lista)
