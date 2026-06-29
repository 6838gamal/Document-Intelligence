# Document Intelligence & Workflow Automation Platform

Enterprise SaaS platform for document management with AI-powered features.

## Tech Stack
- **Backend**: Python 3.11+ / FastAPI / Jinja2 / HTMX / Alpine.js
- **Database**: SQLite (dev) / PostgreSQL (production)
- **Styling**: TailwindCSS via CDN + custom CSS variables
- **Charts**: Chart.js
- **Icons**: Font Awesome 6

## Running the App
```bash
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 5000 --reload
```

## Default Login
- Email: `admin@dociq.io` / Password: `admin123` (Super Admin)
- Email: `manager@dociq.io` / Password: `manager123` (Manager)

## User Preferences
- Port: 5000
- Language: Arabic (RTL) by default, switchable to English
- Theme: Light by default, switchable to Dark
