from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, url_for, session, redirect, request, flash
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_ANON_KEY")
)

app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
app.secret_key = "my_secret_key"

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///user.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Tables the user is allowed to browse
ALLOWED_TABLES = [
    "Maintenance_task",
    "Asset",
    "Maintenance_type",
    "Status",
    "Department",
    "Position",
    "Employee",
]

# ── Routes ──────────────────────────────────────────

@app.route("/")
def home():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email    = request.form["email"]
        password = request.form["password"]

        try:
            response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            session["user"] = {
                "id":           response.user.id,
                "email":        response.user.email,
                "access_token": response.session.access_token,
            }
            return redirect(url_for("dashboard"))

        except Exception as e:
            print("LOGIN ERROR:", e)
            flash("Ongeldig e-mailadres of wachtwoord.")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    supabase.auth.sign_out()
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    user_id      = session["user"]["id"]
    access_token = session["user"]["access_token"]

    # Get requested table, default to Maintenance_task
    active_table = request.args.get("table", "Maintenance_task")

    # Prevent querying tables outside the allowed list
    if active_table not in ALLOWED_TABLES:
        active_table = "Maintenance_task"

    authed_client = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_ANON_KEY")
    )
    authed_client.auth.set_session(access_token, "")

    # Get employee record
    employee = (
        authed_client.table("Employee")
        .select("*")
        .eq("user_UID", user_id)
        .execute()
    )

    if not employee.data:
        return "No employee record found for this user"

    # Fetch the selected table
    table_data = (
        authed_client.table(active_table)
        .select("*")
        .execute()
    )

    return render_template(
        "dashboard.html",
        tasks=table_data.data,
        employee=employee.data[0],
        tables=ALLOWED_TABLES,
        active_table=active_table
    )


if __name__ == "__main__":
    app.run(debug=True)