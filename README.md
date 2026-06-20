# Equipment Maintenance

A web application for managing and tracking equipment maintenance tasks, assets, and service history.

## Technologies

- **Python 3** — backend language
- **Flask** — web framework
- **Supabase** — cloud PostgreSQL database and authentication
- **Groq API** — AI-powered analytics (Llama 3.3 70B)
- **HTML / CSS / JavaScript** — frontend
- **python-dotenv** — environment variable management

## Requirements

- Python 3.10 or higher
- A [Supabase](https://supabase.com) project with the database schema applied
- A [Groq](https://console.groq.com) API key (free)

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Thia-Boetius/Equipment-Maintenance.git
   cd Equipment-Maintenance
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS / Linux
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create a `.env` file** in the project root:
   ```
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your-anon-key
   GROQ_API_KEY=your-groq-api-key
   ```

## Database Setup

This project uses Supabase (PostgreSQL). Apply the following tables in your Supabase project via the SQL editor:

- **Employee** — staff records linked to auth users
- **Machine** — equipment assets (brand, model, status, category)
- **Brand** — machine brands
- **Category** — machine categories
- **Status** — possible machine/task statuses
- **Maintenance_task** — maintenance jobs linked to machines, employees, and status
- **Department** — organisational departments
- **Position** — job positions linked to departments

The full schema SQL is available in the repository. After creating the tables, enable Row Level Security (RLS) policies in Supabase as needed and create at least one user via Supabase Auth.

## Usage

1. Start the Flask development server:
   ```bash
   python app.py
   ```

2. Open your browser and go to `http://127.0.0.1:5000`

3. Log in with your Supabase Auth credentials.

4. Use the sidebar to navigate:
   - **Dashboard** — overview of machines and recent maintenance tasks
   - **Equipment** — full machine register
   - **Maintenance** — all maintenance tasks with joined details
   - **Checklist** — tasks grouped per machine with completion status
   - **Reports** — summary statistics and status breakdowns
   - **Analytics** — AI-generated insights based on your data
