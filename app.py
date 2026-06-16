from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, url_for, session, redirect, request, flash
from supabase import create_client
from dotenv import load_dotenv
import os
import json
from groq import Groq

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

ALLOWED_TABLES = [
    "Machine", "Category", "Status", "Brand",
    "Maintenance_task", "Department", "Position", "Employee",
]

# ── Shared helpers ───────────────────────────────────────────────────────────

def _authed_client(access_token):
    c = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY"))
    c.auth.set_session(access_token, "")
    return c

def _lookup_maps(client):
    brands     = client.table("Brand").select("*").execute().data or []
    statuses   = client.table("Status").select("*").execute().data or []
    categories = client.table("Category").select("*").execute().data or []
    employees  = client.table("Employee").select("*").execute().data or []
    return (
        {b["Brand_ID"]:    b["Name"]        for b in brands},
        {s["Status_ID"]:   s["Description"] for s in statuses},
        {c["Category_ID"]: c["Name"]        for c in categories},
        {e["Employee_ID"]: f"{e['First_name']} {e['Last_name']}" for e in employees},
        statuses,
        categories,
    )

def _enrich_machines(machines, brand_map, status_map, category_map):
    return [{**m,
        "brand":    brand_map.get(m.get("Brand_ID"), "—"),
        "status":   status_map.get(m.get("Status_ID"), "—"),
        "category": category_map.get(m.get("Category_ID"), "—"),
    } for m in machines]

def _enrich_tasks(tasks, machines, brand_map, status_map, category_map, employee_map):
    machine_map = {m["Machine_ID"]: m for m in machines}
    result = []
    for t in tasks:
        m = machine_map.get(t.get("Machine_ID"), {})
        result.append({**t,
            "machine_number": m.get("Machine_number", "—"),
            "model":          m.get("Model") or "—",
            "brand":          brand_map.get(m.get("Brand_ID"), "—"),
            "type":           category_map.get(t.get("Type_ID"), "—"),
            "task_status":    status_map.get(t.get("Status_ID"), "—"),
            "assigned_to":    employee_map.get(t.get("Assigned_to"), "Unassigned"),
        })
    return result

# ── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def home():
    if "user" in session:
        return redirect(url_for("dashboard_home"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email    = request.form["email"]
        password = request.form["password"]
        try:
            response = supabase.auth.sign_in_with_password({
                "email": email, "password": password
            })
            session["user"] = {
                "id":           response.user.id,
                "email":        response.user.email,
                "access_token": response.session.access_token,
            }
            return redirect(url_for("dashboard_home"))
        except Exception as e:
            print("LOGIN ERROR:", str(e))
            flash("Ongeldig e-mailadres of wachtwoord.")
            return redirect(url_for("login"))
    return render_template("login.html")


@app.route("/logout")
def logout():
    supabase.auth.sign_out()
    session.clear()
    return redirect(url_for("login"))


# ── Dashboard Home ───────────────────────────────────────────────────────────

@app.route("/home")
def dashboard_home():
    if "user" not in session:
        return redirect(url_for("login"))

    user_id      = session["user"]["id"]
    access_token = session["user"]["access_token"]
    client       = _authed_client(access_token)

    employee = client.table("Employee").select("*").eq("User_UID", user_id).execute()
    if not employee.data:
        return "No employee record found for this user"

    brand_map, status_map, category_map, employee_map, statuses, categories = _lookup_maps(client)
    machines = client.table("Machine").select("*").execute().data or []
    tasks    = client.table("Maintenance_task").select("*").order("Date", desc=True).execute().data or []

    enriched_tasks = _enrich_tasks(tasks, machines, brand_map, status_map, category_map, employee_map)

    machines_by_status = {}
    for m in _enrich_machines(machines, brand_map, status_map, category_map):
        s = m["status"]
        machines_by_status[s] = machines_by_status.get(s, 0) + 1

    tasks_by_status = {}
    for t in enriched_tasks:
        s = t["task_status"]
        tasks_by_status[s] = tasks_by_status.get(s, 0) + 1

    return render_template(
        "dashboard_home.html",
        employee=employee.data[0],
        active_page="dashboard",
        total_machines=len(machines),
        total_tasks=len(tasks),
        machines_by_status=machines_by_status,
        tasks_by_status=tasks_by_status,
        recent_tasks=enriched_tasks[:10],
    )


# ── Maintenance ──────────────────────────────────────────────────────────────

@app.route("/maintenance")
def maintenance():
    if "user" not in session:
        return redirect(url_for("login"))

    user_id      = session["user"]["id"]
    access_token = session["user"]["access_token"]
    client       = _authed_client(access_token)

    employee = client.table("Employee").select("*").eq("User_UID", user_id).execute()
    if not employee.data:
        return "No employee record found for this user"

    brand_map, status_map, category_map, employee_map, statuses, categories = _lookup_maps(client)
    machines = client.table("Machine").select("*").execute().data or []
    tasks    = client.table("Maintenance_task").select("*").order("Date", desc=True).execute().data or []

    enriched_tasks = _enrich_tasks(tasks, machines, brand_map, status_map, category_map, employee_map)

    return render_template(
        "maintenance.html",
        employee=employee.data[0],
        active_page="maintenance",
        tasks=enriched_tasks,
        total=len(enriched_tasks),
    )


# ── Checklist ────────────────────────────────────────────────────────────────

@app.route("/checklist")
def checklist():
    if "user" not in session:
        return redirect(url_for("login"))

    user_id      = session["user"]["id"]
    access_token = session["user"]["access_token"]
    client       = _authed_client(access_token)

    employee = client.table("Employee").select("*").eq("User_UID", user_id).execute()
    if not employee.data:
        return "No employee record found for this user"

    brand_map, status_map, category_map, employee_map, statuses, categories = _lookup_maps(client)
    machines = client.table("Machine").select("*").execute().data or []
    tasks    = client.table("Maintenance_task").select("*").order("Date", desc=True).execute().data or []

    enriched_tasks = _enrich_tasks(tasks, machines, brand_map, status_map, category_map, employee_map)

    grouped = {}
    for t in enriched_tasks:
        key = t.get("Machine_ID") or 0
        if key not in grouped:
            grouped[key] = {
                "machine_number": t["machine_number"],
                "model":          t["model"],
                "brand":          t["brand"],
                "tasks":          [],
            }
        grouped[key]["tasks"].append(t)

    return render_template(
        "checklist.html",
        employee=employee.data[0],
        active_page="checklist",
        groups=list(grouped.values()),
        total=len(tasks),
    )


# ── Reports ──────────────────────────────────────────────────────────────────

@app.route("/reports")
def reports():
    if "user" not in session:
        return redirect(url_for("login"))

    user_id      = session["user"]["id"]
    access_token = session["user"]["access_token"]
    client       = _authed_client(access_token)

    employee = client.table("Employee").select("*").eq("User_UID", user_id).execute()
    if not employee.data:
        return "No employee record found for this user"

    brand_map, status_map, category_map, employee_map, statuses, categories = _lookup_maps(client)
    machines = client.table("Machine").select("*").execute().data or []
    tasks    = client.table("Maintenance_task").select("*").execute().data or []

    return render_template(
        "reports.html",
        employee=employee.data[0],
        assets=machines,
        tasks=tasks,
        statuses=statuses,
    )


# ── Analytics ────────────────────────────────────────────────────────────────

@app.route("/analytics")
def analytics():
    if "user" not in session:
        return redirect(url_for("login"))

    user_id      = session["user"]["id"]
    access_token = session["user"]["access_token"]
    client       = _authed_client(access_token)

    employee = client.table("Employee").select("*").eq("User_UID", user_id).execute()
    if not employee.data:
        return "No employee record found for this user"

    brand_map, status_map, category_map, employee_map, statuses, categories = _lookup_maps(client)
    machines    = client.table("Machine").select("*").execute().data or []
    tasks       = client.table("Maintenance_task").select("*").execute().data or []
    departments = client.table("Department").select("*").execute().data or []

    machines_by_status = {}
    for m in machines:
        label = status_map.get(m.get("Status_ID"), "Unknown")
        machines_by_status[label] = machines_by_status.get(label, 0) + 1

    tasks_by_type = {}
    for t in tasks:
        label = category_map.get(t.get("Type_ID"), "Unknown")
        tasks_by_type[label] = tasks_by_type.get(label, 0) + 1

    data_summary = json.dumps({
        "total_machines":     len(machines),
        "total_tasks":        len(tasks),
        "departments":        [d.get("Name") for d in departments],
        "statuses":           [s.get("Description") for s in statuses],
        "categories":         [c.get("Name") for c in categories],
        "machines_by_status": machines_by_status,
        "tasks_by_type":      tasks_by_type,
        "sample_machines":    machines[:5],
        "sample_tasks":       tasks[:5],
    }, default=str)

    ai_analyses = []
    try:
        groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=1024,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an equipment maintenance analyst. "
                        "Analyze the JSON data and return ONLY a JSON array of exactly 5 insight objects. "
                        "Each object must have these fields: "
                        "\"title\" (short heading), \"insight\" (2-3 sentence finding), "
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
        assets=machines,
        tasks=tasks,
        statuses=statuses,
        departments=departments,
        ai_analyses=ai_analyses,
    )


# ── Generic table browser (Settings, Log History, etc.) ─────────────────────

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    user_id      = session["user"]["id"]
    access_token = session["user"]["access_token"]

    active_table = request.args.get("table", "Machine")
    if active_table not in ALLOWED_TABLES:
        active_table = "Machine"

    client = _authed_client(access_token)

    employee = client.table("Employee").select("*").eq("User_UID", user_id).execute()
    if not employee.data:
        return "No employee record found for this user"

    table_data = client.table(active_table).select("*").execute()

    return render_template(
        "dashboard.html",
        tasks=table_data.data,
        employee=employee.data[0],
        tables=ALLOWED_TABLES,
        active_table=active_table,
    )


# ── Register machine ─────────────────────────────────────────────────────────

@app.route("/register-asset", methods=["GET", "POST"])
def register_asset():
    if "user" not in session:
        return redirect(url_for("login"))

    user_id      = session["user"]["id"]
    access_token = session["user"]["access_token"]
    client       = _authed_client(access_token)

    employee = client.table("Employee").select("*").eq("User_UID", user_id).execute()
    if not employee.data:
        return "No employee record found for this user"

    brands     = client.table("Brand").select("*").execute().data or []
    statuses   = client.table("Status").select("*").execute().data or []
    categories = client.table("Category").select("*").execute().data or []

    if request.method == "POST":
        new_machine = {
            "Machine_number": request.form.get("machine_number"),
            "Year":           request.form.get("year") or None,
            "Model":          request.form.get("model") or None,
            "Chasis_number":  request.form.get("chasis_number") or None,
            "Plate_number":   request.form.get("plate_number") or None,
            "Mileage":        request.form.get("mileage") or None,
            "Brand_ID":       request.form.get("brand_id") or None,
            "Status_ID":      request.form.get("status_id") or None,
            "Category_ID":    request.form.get("category_id") or None,
        }
        new_machine = {k: v for k, v in new_machine.items() if v not in (None, "")}
        try:
            client.table("Machine").insert(new_machine).execute()
            flash("Machine succesvol geregistreerd.")
            return redirect(url_for("dashboard", table="Machine"))
        except Exception as e:
            flash(f"Fout bij registreren: {str(e)}")

    return render_template(
        "register_asset.html",
        employee=employee.data[0],
        active_page="register_asset",
        brands=brands,
        statuses=statuses,
        categories=categories,
    )


# ── Plan maintenance ─────────────────────────────────────────────────────────

@app.route("/plan-maintenance", methods=["GET", "POST"])
def plan_maintenance():
    if "user" not in session:
        return redirect(url_for("login"))

    user_id      = session["user"]["id"]
    access_token = session["user"]["access_token"]
    client       = _authed_client(access_token)

    employee = client.table("Employee").select("*").eq("User_UID", user_id).execute()
    if not employee.data:
        return "No employee record found for this user"

    machines   = client.table("Machine").select("Machine_ID, Machine_number, Model").execute().data or []
    categories = client.table("Category").select("*").execute().data or []
    statuses   = client.table("Status").select("*").execute().data or []
    employees  = client.table("Employee").select("*").execute().data or []

    if request.method == "POST":
        new_task = {
            "Machine_ID":  request.form.get("machine_id"),
            "Type_ID":     request.form.get("type_id") or None,
            "Status_ID":   request.form.get("status_id") or None,
            "Date":        request.form.get("date"),
            "Remark":      request.form.get("remark") or None,
            "Price":       request.form.get("price") or None,
            "Assigned_to": request.form.get("assigned_to") or None,
        }
        new_task = {k: v for k, v in new_task.items() if v not in (None, "")}
        try:
            client.table("Maintenance_task").insert(new_task).execute()
            flash("Onderhoud succesvol gepland.")
            return redirect(url_for("maintenance"))
        except Exception as e:
            flash(f"Fout bij plannen: {str(e)}")

    tasks = client.table("Maintenance_task").select("*").order("Date", desc=True).execute().data or []

    return render_template(
        "plan_maintenance.html",
        employee=employee.data[0],
        active_page="plan_maintenance",
        machines=machines,
        categories=categories,
        statuses=statuses,
        employees=employees,
        schedules=tasks,
    )


if __name__ == "__main__":
    app.run(debug=True)
