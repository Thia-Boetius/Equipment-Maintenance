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

class AuthExpiredError(Exception):
    pass

@app.errorhandler(AuthExpiredError)
def handle_auth_expired(e):
    session.clear()
    return redirect(url_for("login"))

# ── Shared helpers ───────────────────────────────────────────────────────────

def _authed_client(access_token):
    refresh_token = session.get("user", {}).get("refresh_token", "")
    c = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY"))
    try:
        c.auth.set_session(access_token, refresh_token)
    except Exception:
        raise AuthExpiredError()
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
                "id":            response.user.id,
                "email":         response.user.email,
                "access_token":  response.session.access_token,
                "refresh_token": response.session.refresh_token,
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

# ── Checklist: category picker ──────────────────────────────────────────────

INSPECTION_ITEMS = [
    "Backup lights and alarm",
    "Brake condition (dynamic, service, park)",
    "Brake fluid",
    "Cab, mirrors, seat belt and glass",
    "Cooling system fluid",
    "Engine oil",
    "Exhaust system",
    "Fire extinguisher condition",
    "Horn and gauges",
    "Hydraulic oil",
    "Lights",
    "Oil leak / lube",
    "Steering (standard and emergency)",
    "Tires or tracks",
    "Transmission fluid",
    "Wheels / tires",
]

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

    categories = client.table("Category").select("*").execute().data or []

    return render_template(
        "checklist_select.html",
        employee=employee.data[0],
        active_page="checklist",
        categories=categories,
    )


@app.route("/checklist/<int:category_id>", methods=["GET", "POST"])
def checklist_form(category_id):
    if "user" not in session:
        return redirect(url_for("login"))

    user_id      = session["user"]["id"]
    access_token = session["user"]["access_token"]
    client       = _authed_client(access_token)

    employee = client.table("Employee").select("*").eq("User_UID", user_id).execute()
    if not employee.data:
        return "No employee record found for this user"

    category = client.table("Category").select("*").eq("Category_ID", category_id).execute().data[0]
    machines = client.table("Machine").select("Machine_ID, Machine_number, Model") \
                      .eq("Category_ID", category_id).execute().data or []

    if request.method == "POST":
        machine_id  = request.form.get("machine_id")
        usage_today = float(request.form.get("usage_today") or 0)
        hours_today = float(request.form.get("hours_today") or 0)
        defect      = request.form.get("defect") or None
        remark      = request.form.get("remark") or None

        new_task = {
            "Machine_ID":  machine_id,
            "Type_ID":     category_id,
            "Date":        request.form.get("date"),
            "Usage_today": usage_today,
            "Hours_today": hours_today,
            "Defect":      defect,
            "Remark":      remark,
            "Assigned_to": employee.data[0]["Employee_ID"],
            "Seen":        False,
        }
        client.table("Maintenance_task").insert(new_task).execute()

        machine = client.table("Machine").select("Total_km, Total_hours") \
                         .eq("Machine_ID", machine_id).execute().data[0]
        new_total_km    = (machine.get("Total_km") or 0) + usage_today
        new_total_hours = (machine.get("Total_hours") or 0) + hours_today
        needs_service   = new_total_km >= KM_THRESHOLD or new_total_hours >= HOURS_THRESHOLD

        client.table("Machine").update({
            "Total_km":      new_total_km,
            "Total_hours":   new_total_hours,
            "Needs_service": needs_service,
        }).eq("Machine_ID", machine_id).execute()

        flash("Checklist successfully submitted.")
        return redirect(url_for("checklist"))

    return render_template(
        "checklist_form.html",
        employee=employee.data[0],
        active_page="checklist",
        category=category,
        machines=machines,
        inspection_items=INSPECTION_ITEMS,
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

@app.route("/dashboard", methods=["GET", "POST"])
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

    filter_brands   = []
    filter_statuses = []
    filter_models   = []
    current_filters = {}

    if active_table == "Machine":
        brand_map, status_map, category_map, employee_map, statuses, categories = _lookup_maps(client)
        filter_brands   = client.table("Brand").select("*").execute().data or []
        filter_statuses = client.table("Status").select("*").execute().data or []
        all_machines    = client.table("Machine").select("Model").execute().data or []
        filter_models   = sorted({m["Model"] for m in all_machines if m.get("Model")})

        brand_id  = request.args.get("brand_id")
        status_id = request.args.get("status_id")
        model     = request.args.get("model")
        current_filters = {"brand_id": brand_id, "status_id": status_id, "model": model}

        query = client.table("Machine").select(
            "Machine_ID, Machine_number, Year, Model, Plate_number, Mileage, Needs_service"
        )
        if brand_id:
            query = query.eq("Brand_ID", int(brand_id))
        if status_id:
            query = query.eq("Status_ID", int(status_id))
        if model:
            query = query.eq("Model", model)

        table_data = query.execute()
    else:
        table_data = client.table(active_table).select("*").execute()
    
    return render_template(
    "dashboard.html",
    tasks=table_data.data,
    employee=employee.data[0],
    tables=ALLOWED_TABLES,
    active_table=active_table,
    filter_brands=filter_brands,
    filter_statuses=filter_statuses,
    filter_models=filter_models,
    current_filters=current_filters,
    brands=client.table("Brand").select("*").execute().data or [],
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

    brand_map, status_map, category_map, employee_map, _, _ = _lookup_maps(client)
    enriched_schedules = _enrich_tasks(
        tasks,
        client.table("Machine").select("*").execute().data or [],
        brand_map, status_map, category_map, employee_map
    )

    return render_template(
        "plan_maintenance.html",
        employee=employee.data[0],
        active_page="plan_maintenance",
        machines=machines,
        categories=categories,
        statuses=statuses,
        employees=employees,
        schedules=enriched_schedules,
    )

@app.context_processor
def notification_data():

    if "user" not in session:
        return {"recent_notifications": []}

    try:
        client = _authed_client(session["user"]["access_token"])

        tasks = (
            client.table("Maintenance_task")
            .select("*")
            .order("Date", desc=True)
            .limit(5)
            .execute()
            .data
        ) or []

        brand_map, status_map, category_map, employee_map, _, _ = _lookup_maps(client)

        machines = client.table("Machine").select("*").execute().data or []

        notifications = _enrich_tasks(
            tasks,
            machines,
            brand_map,
            status_map,
            category_map,
            employee_map
        )

        return {"recent_notifications": notifications}

    except Exception:
        return {"recent_notifications": []}

# ── Settings ──────────────────────────────────────────────────────────────────

@app.route("/settings")
def settings():
    if "user" not in session:
        return redirect(url_for("login"))

    user_id      = session["user"]["id"]
    access_token = session["user"]["access_token"]
    client       = _authed_client(access_token)

    employee = client.table("Employee").select("*").eq("User_UID", user_id).execute()
    if not employee.data:
        return "No employee record found for this user"

    return render_template(
        "settings.html",
        employee=employee.data[0],
        active_page="settings",
    )

if __name__ == "__main__":
    app.run(debug=True)
