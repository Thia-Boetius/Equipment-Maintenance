from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, url_for, session, redirect, request, flash
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()  # leest je .env bestand

app = Flask(__name__)

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_ANON_KEY")
)

app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
app.secret_key = "my_secret_key"

# Configureer SQLAlchemy voor de database verbinding
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///user.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# ── Routes ──────────────────────────────────────────

# Homepagina: als de gebruiker al ingelogd is, stuur hem naar het dashboard
# anders stuur hem naar de loginpagina

@app.route("/")
def home():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

# Loginpagina: hier voert de gebruiker zijn email en wachtwoord in
# Bij GET: laad de loginpagina
# Bij POST: haal email en wachtwoord op uit het formulier en
# probeer in te loggen via Supabase. Als het lukt, sla de gebruiker
# op in de sessie en stuur hem naar het dashboard.
# Als het mislukt, toon een foutmelding en stuur hem terug naar de loginpagina.
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
            # Sla gebruikersinfo op in de Flask sessie
            session["user"] = {
                "id":    response.user.id,
                "email": response.user.email,
            }
            return redirect(url_for("dashboard"))

        except Exception as e:
            print("LOGIN ERROR:", e)
            flash("Ongeldig e-mailadres of wachtwoord.")
            return redirect(url_for("login"))

    return render_template("login.html")


# Uitloggen: verwijder de gebruiker uit de sessie en
# log hem uit via Supabase, stuur hem daarna naar de loginpagina

@app.route("/logout")
def logout():
    supabase.auth.sign_out()
    session.clear()
    return redirect(url_for("login"))


# Dashboard: alleen toegankelijk als de gebruiker ingelogd is
# Als de gebruiker niet ingelogd is, stuur hem naar de loginpagina
# Geef de gebruikersinfo mee aan de template zodat je die kan gebruiken

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    user_id = session["user"]["id"]

    print("Logged in Supabase User ID:", user_id)
    employee = (
        supabase.table("Employee")
        .select("*")
        .eq("user_UID", user_id)
        .execute()
    )

    print("Employee Query Result:")
    print(employee.data)
    return str(employee.data)

if __name__ == "__main__":
    app.run(debug=True)