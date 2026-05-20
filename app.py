from flask import Flask, render_template, url_for, session, redirect
from flask_sqlalchemy import SQLAlchemy

from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()  # reads your .env file

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_ANON_KEY")
)

# Test query
response = supabase.table("Department").select("*").execute()
print(response.data)

app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
app.secret_key = "my_secret_key"

#configure sql alchemy 
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///user.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)



#database Model










#routes

@app.route('/login')
def login():
    return render_template('login.html')

    

@app.route("/")
def home():
    if "username" in session:
        return redirect(url_for('dashboard'))
    return render_template("login.html")




if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
