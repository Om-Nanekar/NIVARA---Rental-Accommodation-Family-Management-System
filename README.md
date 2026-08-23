# Rental Accommodation & Family Billing Management System

Flask + MySQL/InnoDB rental accommodation system with family-based room allocation, 30-day electricity billing cycles, immutable billing snapshots, local UPI QR generation, PDF invoices and payment tracking.

## 1. Requirements

- Python 3.10+
- MySQL 8.x recommended
- A MySQL user with permission to create/use the project database

## 2. Install

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# Linux/macOS
# source .venv/bin/activate

pip install -r requirements.txt
```

## 3. Configure

Copy `.env.example` to `.env` and set the MySQL credentials and Flask secret key.

## 4. Create database

Run `sql/schema.sql` first, then `sql/seed.sql`.

The seed admin is:

- Username: `admin`
- Password: `admin123`

Change this password immediately from **Settings**.

## 5. Run

```bash
python run.py
```

Open `http://127.0.0.1:5000/login`.

## Business rules implemented

1. A room can have one active family at a time.
2. The family head stores the primary contact details.
3. Additional family members are stored separately with name and age.
4. Allocating a family automatically changes the room status to `OCCUPIED`.
5. A billing cycle is due after 30 days from the latest room reading, or from move-in when no reading exists.
6. The previous electricity reading is retrieved automatically.
7. Electricity cost uses the effective rate for the reading date.
8. Each bill stores rent, rate, units, electricity amount, other charges and total as a historical snapshot.
9. Updating future rent or electricity rates does not recalculate prior bills.
10. Payments update bill status to `UNPAID`, `PARTIALLY_PAID` or `PAID`.
11. UPI QR codes are generated locally from the current outstanding balance.
12. PDF invoices are generated locally with ReportLab.
13. Family checkout is blocked while unpaid or partially paid bills remain.

## Notes

The frontend uses Bootstrap 5 from jsDelivr. No charting library, external payment gateway or WhatsApp API is used.
