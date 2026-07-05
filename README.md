# Cloud Cost Tracker


## Description

Cloud Cost Tracker is a web application built with Flask and SQLite that helps
users monitor and control their spending across cloud providers (AWS, GCP,
and Azure). It was built as my final project, applying everything learned
throughout the course: web programming with Flask, relational database
design with SQL, server-side form validation, and front-end templating with
Jinja and Bootstrap.

The idea came from my own experience studying cloud infrastructure and data
engineering: cloud costs are notoriously easy to lose track of, since charges
come from multiple services, categories, and providers at once. This project
simulates that problem in a simplified, personal-finance-style interface,
inspired by the CS50 Finance project but adapted to a completely different
domain.

## Features

- **User accounts** — Register, log in, and log out securely. Passwords are
  hashed with Werkzeug before being stored; sessions are stored server-side.
- **Dashboard** — Shows the total amount spent in the current month, a bar
  chart of spending by provider, and a pie chart of spending by category,
  both rendered with Chart.js.
- **Expense tracking** — Add a new expense by selecting a provider (AWS,
  GCP, Azure), a category (Compute, Storage, Network, Database), an amount,
  and a date. All expenses are listed in a table and can be deleted.
- **Budgets** — Set a monthly spending limit per category. If the current
  month's spending in a category exceeds its budget, a red alert appears on
  the dashboard.

## Database design

The database (`cloud_costs.db`) has four tables:

- `users` — stores usernames and password hashes.
- `providers` — a small reference table with AWS, GCP, and Azure.
- `expenses` — each row is one expense: which user, which provider, which
  category, the amount, and the date. Foreign keys tie it back to `users`
  and `providers`.
- `budgets` — one row per user per category, storing the monthly limit. A
  unique index on `(user_id, category)` guarantees a user can only have one
  budget per category, and lets the app use `INSERT ... ON CONFLICT DO
  UPDATE` to create-or-update a budget in a single query.

## Files

- `app.py` — all Flask routes: register, login, logout, dashboard (`/`),
  expenses (`/expenses`), and budgets (`/budgets`).
- `helpers.py` — the `apology` error page helper and the `login_required`
  decorator, adapted from the course's Finance problem set.
- `templates/` — Jinja templates for every page, extending a shared
  `layout.html` with a Bootstrap navbar.
- `static/styles.css` — small custom styling on top of Bootstrap.
- `cloud_costs.db` — the SQLite database.

## Design choices

I chose to hard-code the four expense categories (Compute, Storage, Network,
Database) as a dropdown rather than free text, to keep the budget-matching
logic simple and to avoid inconsistent category names (e.g. "compute" vs
"Computing") breaking the alert feature.

I used `ON CONFLICT ... DO UPDATE` for budgets instead of a separate
edit/delete flow, since a monthly budget naturally has "one value per
category" semantics — setting a new value should simply replace the old one.

## How to run

1. Install dependencies: `pip install -r requirements.txt` (Flask,
   Flask-Session, CS50, Werkzeug).
2. Run `flask run`.
3. Visit the URL shown in the terminal, register an account, and start
   tracking expenses.
