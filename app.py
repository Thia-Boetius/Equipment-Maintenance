from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, url_for, session, redirect, request, flash
from supabase import create_client
from dotenv import load_dotenv
import os
import json
from groq import Groq

load_dotenv()  # reads your .env file
load_dotenv()  # reads your .env file

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
    "maintenance_overview",
    "employee_overview",
    "asset_maintenance_history",
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
            print("LOGIN ERROR:", str(e))  # 👈 wrap in str()
            flash("Ongeldig e-mailadres of wachtwoord.")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    supabase.auth.sign_out()
    session.clear()
    return redirect(url_for("login"))


@app.route("/reports")
def reports():
    if "user" not in session:
        return redirect(url_for("login"))

    access_token = session["user"]["access_token"]
    user_id      = session["user"]["id"]

    authed_client = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_ANON_KEY")
    )
    authed_client.auth.set_session(access_token, "")

    employee = (
        authed_client.table("Employee")
        .select("*")
        .eq("user_UID", user_id)
        .execute()
    )

    if not employee.data:
        return "No employee record found for this user"

    assets     = authed_client.table("Asset").select("*").execute().data or []
    tasks      = authed_client.table("Maintenance_task").select("*").execute().data or []
    statuses   = authed_client.table("Status").select("*").execute().data or []

    return render_template(
        "reports.html",
        employee=employee.data[0],
        assets=assets,
        tasks=tasks,
        statuses=statuses,
    )


@app.route("/analytics")
def analytics():
    if "user" not in session:
        return redirect(url_for("login"))

    access_token = session["user"]["access_token"]
    user_id      = session["user"]["id"]

    authed_client = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_ANON_KEY")
    )
    authed_client.auth.set_session(access_token, "")

    employee = (
        authed_client.table("Employee")
        .select("*")
        .eq("user_UID", user_id)
        .execute()
    )
    if not employee.data:
        return "No employee record found for this user"

    assets      = authed_client.table("Asset").select("*").execute().data or []
    tasks       = authed_client.table("Maintenance_task").select("*").execute().data or []
    statuses    = authed_client.table("Status").select("*").execute().data or []
    departments = authed_client.table("Department").select("*").execute().data or []
    maint_types = authed_client.table("Maintenance_type").select("*").execute().data or []

    # Count assets per status
    status_map = {s.get("Status_ID") or s.get("id"): s.get("Status_name") or s.get("name", "Unknown")
                  for s in statuses}
    assets_by_status = {}
    for a in assets:
        sid = a.get("Status_ID")
        label = status_map.get(sid, str(sid) if sid else "Unknown")
        assets_by_status[label] = assets_by_status.get(label, 0) + 1

    # Count tasks per maintenance type
    type_map = {t.get("Maintenance_type_ID") or t.get("id"): t.get("Type_name") or t.get("name", "Unknown")
                for t in maint_types}
    tasks_by_type = {}
    for t in tasks:
        tid = t.get("Maintenance_type_ID")
        label = type_map.get(tid, str(tid) if tid else "Unknown")
        tasks_by_type[label] = tasks_by_type.get(label, 0) + 1

    data_summary = json.dumps({
        "total_assets":       len(assets),
        "total_tasks":        len(tasks),
        "departments":        [d.get("Department_name") or d.get("name") for d in departments],
        "statuses":           [s.get("Status_name") or s.get("name") for s in statuses],
        "maintenance_types":  [m.get("Type_name") or m.get("name") for m in maint_types],
        "assets_by_status":   assets_by_status,
        "tasks_by_type":      tasks_by_type,
        "sample_assets":      assets[:5],
        "sample_tasks":       tasks[:5],
    }, default=str)

    ai_analyses = []
    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=1024,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an equipment maintenance analyst. "
                        "Analyze the JSON data and return ONLY a JSON array of exactly 5 insight objects. "
                        "Each object must have these fields: "
                        "\"title\" (short heading), "
                        "\"insight\" (2-3 sentence finding), "
                        "\"recommendation\" (1-2 sentence action), "
                        "\"severity\" (one of: info, warning, critical). "
                        "Return raw JSON only — no markdown, no code fences, no explanation."
                    )
                },
                {
                    "role": "user",
                    "content": f"Analyze this equipment maintenance data:\n{data_summary}"
                }
            ]
        )
        raw = completion.choices[0].message.content
        start, end = raw.find("["), raw.rfind("]") + 1
        if start >= 0 and end > start:
            ai_analyses = json.loads(raw[start:end])
    except Exception as e:
        print(f"AI analysis error: {e}")
        ai_analyses = [{
            "title": "Analysis unavailable",
            "insight": "Could not generate AI analysis. Check that GROQ_API_KEY is set in your .env file.",
            "recommendation": "Add GROQ_API_KEY=<your-key> to .env and restart the server.",
            "severity": "info"
        }]

    return render_template(
        "analytics.html",
        employee=employee.data[0],
        assets=assets,
        tasks=tasks,
        statuses=statuses,
        departments=departments,
        ai_analyses=ai_analyses,
    )


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    user_id      = session["user"]["id"]
    access_token = session["user"]["access_token"]

    active_table = request.args.get("table", "maintenance_overview")

    if active_table not in ALLOWED_TABLES:
        active_table = "maintenance_overview"

    authed_client = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_ANON_KEY")
    )

    try:
        authed_client.auth.set_session(access_token, "")
    except Exception:
        # Token expired — clear session and send back to login
        session.clear()
        return redirect(url_for("login"))

    # Get employee record
    employee = (
        authed_client.table("Employee")
        .select("*")
        .eq("user_UID", user_id)
        .execute()
    )

    if not employee.data:
        return "No employee record found for this user"

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

@app.route("/register-asset", methods=["GET", "POST"])
def register_asset():
    if "user" not in session:
        return redirect(url_for("login"))

    access_token = session["user"]["access_token"]
    user_id      = session["user"]["id"]

    authed_client = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_ANON_KEY")
    )
    authed_client.auth.set_session(access_token, "")

    employee = (
        authed_client.table("Employee")
        .select("*")
        .eq("user_UID", user_id)
        .execute()
    )
    if not employee.data:
        return "No employee record found for this user"

    if request.method == "POST":
        new_asset = {
            "Name":           request.form["name"],
            "Year":           request.form.get("year") or None,
            "Brand":          request.form.get("brand") or None,
            "Model":          request.form.get("model") or None,
            "chasis_number":  request.form.get("chasis_number") or None,
            "plaat_nummer":   request.form.get("plaat_nummer") or None,
            "kilometerstand": request.form.get("kilometerstand") or None,
            "Status":         request.form.get("status") or None,
            "type_id":        request.form.get("type_id") or None,
        }
        # leeg -> None, en lege strings niet meesturen
        new_asset = {k: v for k, v in new_asset.items() if v not in (None, "")}

        try:
            authed_client.table("Asset").insert(new_asset).execute()
            flash("Apparatuur succesvol geregistreerd.")
            return redirect(url_for("dashboard", table="Asset"))
        except Exception as e:
            flash(f"Fout bij registreren van apparatuur: {str(e)}")

    return render_template(
        "register_asset.html",
        employee=employee.data[0],
      
    )


@app.route("/plan-maintenance", methods=["GET", "POST"])
def plan_maintenance():
    if "user" not in session:
        return redirect(url_for("login"))

    access_token = session["user"]["access_token"]
    user_id      = session["user"]["id"]

    authed_client = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_ANON_KEY")
    )
    authed_client.auth.set_session(access_token, "")

    employee = (
        authed_client.table("Employee")
        .select("*")
        .eq("user_UID", user_id)
        .execute()
    )
    if not employee.data:
        return "No employee record found for this user"

    assets = authed_client.table("Asset").select("Asset_ID, Name").execute().data or []

    if request.method == "POST":
        new_schedule = {
            "Asset_id":         request.form.get("asset_id"),
            "maintenance_date": request.form.get("maintenance_date") or None,
            "next_maintenance": request.form.get("next_maintenance") or None,
        }
        new_schedule = {k: v for k, v in new_schedule.items() if v not in (None, "")}

        try:
            authed_client.table("schedule_maintenance").insert(new_schedule).execute()
            flash("Onderhoud succesvol gepland.")
            return redirect(url_for("plan_maintenance"))
        except Exception as e:
            flash(f"Fout bij plannen van onderhoud: {str(e)}")

    schedules = (
        authed_client.table("schedule_maintenance")
        .select("*, Asset(Name)")
        .order("maintenance_id", desc=True)
        .execute()
    ).data or []

    return render_template(
        "plan_maintenance.html",
        employee=employee.data[0],
        assets=assets,
        schedules=schedules,
    )

if __name__ == "__main__":
    app.run(debug=True)