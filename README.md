# TransitOps — Smart Transport Operations Platform (Odoo 18 Module)

This repository contains the scaffolded Odoo 18 module and Docker environment for the TransitOps hackathon.

## Getting Started

Follow these steps to spin up the local development environment:

### Prerequisites
- Docker and Docker Compose installed.

### Setup Instructions
1. Copy the environment variables template:
   ```bash
   cp .env.example .env
   ```
2. Run the containers:
   ```bash
   docker compose up -d
   ```
3. Open your web browser and go to `http://localhost:8069`.

3. Create a new database with name `transit_ops` (or let Odoo create it default). Use Master Password `admin123` if prompted.
4. Log in (default master password is in `odoo.conf`).
5. Go to **Apps**, search for `transit_ops` (remove the `Apps` filter if it doesn't show up), and click **Activate/Install**.

---

## Shared Scaffolding Structure & Tasks Division

Each team member should claim one of the following tracks:

### 🅰️ Track A: Vehicle Registry, Driver CRUD, & Reports
- **Python Models:** `models/transit_vehicle.py`, `models/transit_driver.py`
- **Views:** `views/vehicle_views.xml`, `views/driver_views.xml`
- **Reporting & Wizard:** `wizard/report_wizard.py`, `wizard/report_wizard_views.xml`, `reports/report_templates.xml`

### 🅱️ Track B: Trip Management & Business Rules (Hardest)
- **Python Models:** `models/transit_trip.py` (complete state machines, constraints, action overrides)
- **Views:** `views/trip_views.xml` (dispatch board kanban, form views with dynamic domains)
- **Data:** `data/sequences.xml`

### 🅲 Track C: Maintenance Logs, Fuel Logs, Expenses, & Demo Data
- **Python Models:** `models/transit_maintenance.py`, `models/transit_fuel_log.py`, `models/transit_expense.py`
- **Views:** `views/maintenance_views.xml`, `views/fuel_log_views.xml`, `views/expense_views.xml`
- **Demo Data:** `data/demo_data.xml` (expand with test records)

### 🅳 Track D: RBAC Security, Menu Navigation, & OWL Dashboard (Hardest)
- **Security:** `security/security.xml`, `security/ir.model.access.csv`
- **Menus:** `views/menu_views.xml`
- **Dashboard:** `controllers/dashboard.py`, `static/src/js/dashboard.js`, `static/src/xml/dashboard.xml`, `static/src/css/dashboard.css`

---

## Helpful Development Command Reference
- Restart Odoo server (pick up Python updates):
  ```bash
  docker compose restart odoo
  ```
- Tail logs to debug exceptions:
  ```bash
  docker compose logs -f odoo
  ```
