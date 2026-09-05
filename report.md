# NIVARA — Rental Accommodation & Family Billing Management System
## Comprehensive Project Engineering & Architectural Report

---

## 1. Executive Summary

**NIVARA** is a dedicated, production-oriented property and tenant accommodation management system engineered using Python (Flask) and MySQL (InnoDB). The system addresses common challenges faced by property managers, landlords, and hostel administrators, including multi-tenant occupancy limits, complex 30-day electricity consumption cycles, historical financial snapshot immutability, on-the-fly UPI payment QR generation, and automated PDF invoice compilation.

The application adheres to clean architecture principles with a decoupled presentation layer styled according to a modern, restrained SaaS design philosophy (inspired by Linear, Stripe Dashboard, Vercel, and Notion).

---

## 2. Technology Stack & Dependencies

### 2.1 Core Technologies

| Layer | Technology | Version / Specification | Description |
| :--- | :--- | :--- | :--- |
| **Backend Language** | Python | 3.10+ | Primary server-side execution environment |
| **Web Framework** | Flask | >= 3.0, < 4.0 | WSGI microframework for routing, session management, and template rendering |
| **Database Engine** | MySQL | 8.0+ (InnoDB) | Relational database providing ACID transactions, foreign keys, and generated columns |
| **Database Connector**| `mysql-connector-python` | >= 8.4, < 10.0 | Native MySQL Python driver with connection management and dictionary cursors |
| **PDF Generation** | ReportLab | >= 4.0, < 5.0 | Dynamic binary document generator producing standard A4 financial PDF invoices |
| **QR Code Engine** | `qrcode[pil]` & Pillow | qrcode >= 7.4, Pillow >= 10.0 | Generates compliant UPI payment QR matrix images in memory |
| **Security & Hashing** | Werkzeug | >= 3.0, < 4.0 | PBKDF2:SHA256 password hashing and secure session abstractions |
| **Environment Mgmt** | `python-dotenv` | >= 1.0, < 2.0 | Loads environment variables from `.env` files into configuration objects |
| **Frontend Styling** | Custom CSS + Bootstrap | 5.3 (Grid/Utilities) | Clean SaaS design system with CSS custom properties (variables) |
| **Iconography** | Bootstrap Icons | 1.11.3 | Scalable vector icons for navigation, status indicators, and actions |
| **Typography** | Google Fonts (Inter) | 300, 400, 500, 600, 700 | Highly legible neutral sans-serif typography |

### 2.2 Python Package Dependencies (`requirements.txt`)

```plaintext
Flask>=3.0,<4.0
mysql-connector-python>=8.4,<10
python-dotenv>=1.0,<2
qrcode[pil]>=7.4,<9
Pillow>=10,<12
reportlab>=4.0,<5
Werkzeug>=3.0,<4
```

---

## 3. Project Directory & File Structure

```plaintext
rental_accommodation_system/
│
├── assets/                                 # Raw graphic assets
│   └── images/
│       └── Main_logo.svg                   # Original SVG vector logo
│
├── services/                               # Isolated domain services & generators
│   ├── __init__.py                         # Package identifier
│   ├── pdf_service.py                      # ReportLab PDF invoice generation engine
│   └── qr_service.py                       # Dynamic UPI URI and QR code image generator
│
├── sql/                                    # Database definitions and seed scripts
│   ├── schema.sql                          # Full DDL database schema with foreign keys and constraints
│   └── seed.sql                            # Initial administrative and default property seed data
│
├── static/                                 # Static assets served by Flask
│   ├── css/
│   │   ├── bootstrap.min.css               # Base responsive grid and utility stylesheet
│   │   ├── style.css                       # Primary NIVARA SaaS design system stylesheet
│   │   └── app.css                         # Supporting theme rules and legacy styling overrides
│   ├── images/
│   │   └── Main_logo.svg                   # Static logo asset for web use
│   └── js/
│       ├── app.js                          # Client-side dynamic member rows, search & table filtering
│       └── bootstrap.bundle.min.js         # Bootstrap JavaScript bundle (modals, dropdowns, collapse)
│
├── templates/                              # Jinja2 HTML layout and view templates
│   ├── base.html                           # Master application layout (fixed sidebar, topbar, alerts)
│   ├── dashboard.html                      # Executive dashboard with stat cards, recent bills, and due cycles
│   ├── rooms.html                          # Room inventory management, status switches, and edit panels
│   ├── family_allocation.html              # Tenant allocation interface with dynamic member counter
│   ├── electricity.html                    # Electricity reading cycles and modal snapshot generator
│   ├── billing.html                        # Historical billing snapshot register with live filters
│   ├── bill_detail.html                    # Invoice breakdown, UPI payment QR, and payment recorder
│   ├── settings.html                       # Property profile, UPI receiver info, electricity rates, password
│   ├── login.html                          # Minimal administrator authentication portal
│   └── error.html                          # Standardized HTTP 404/500 error display template
│
├── .env.example                            # Template configuration for environment variables
├── .env                                    # Active environment configuration (Credentials)
├── app.py                                  # Core Flask application, route controllers, and filters
├── config.py                               # Configuration manager loading environment parameters
├── database.py                             # MySQL connection context managers and query helpers
├── requirements.txt                        # Pinned dependencies definition
├── run.py                                  # WSGI development launcher script
├── README.md                               # Developer and operator documentation
└── report.md                               # Complete architectural and technical project report
```

### 3.1 File Functionality Overview

| File | Purpose |
| :--- | :--- |
| `run.py` | Imports the Flask application instance from `app.py` and executes the local web server on port 5000. |
| `config.py` | Resolves the project base directory and loads environment variables into a structured `Config` class. |
| `database.py` | Provides context-managed connections (`get_connection`), single/multi-row fetch helpers (`fetch_one`, `fetch_all`), execution routines (`execute`), and transaction management (`transaction`). |
| `app.py` | Contains all Flask route controllers, authentication decorators (`@login_required`), Jinja template filters (`@app.template_filter("money")`), global context processors, and error handlers. |
| `services/pdf_service.py` | Uses ReportLab Flowables (`SimpleDocTemplate`, `Table`, `Paragraph`) to generate downloadable PDF receipts. |
| `services/qr_service.py` | Encodes payment details into a standard `upi://pay` URI string and renders PNG image byte buffers. |
| `static/css/style.css` | Implements the complete design system: custom CSS variables, neutral backgrounds, border hierarchies, table styles, and status badges. |
| `static/js/app.js` | Manages real-time client-side table searching, live room capacity validation for tenant forms, and mobile navigation toggles. |

---

## 4. Database Architecture & Schema

The database utilizes the MySQL **InnoDB** storage engine to guarantee ACID transaction compliance, strict referential integrity through foreign keys, generated columns for automatic calculations, and index optimizations.

### 4.1 Relational Schema Summary

| Table Name | Description | Key Relationships |
| :--- | :--- | :--- |
| `admin` | Stores administrative credentials and PBKDF2 password hashes | Standalone |
| `rooms` | Stores room inventory, floor levels, capacity limits, and current rent rates | Referenced by `families`, `electricity_readings`, `bills` |
| `families` | Stores tenant family head records, contact numbers, and occupancy dates | References `rooms`; Referenced by `family_members`, `bills` |
| `family_members` | Stores individual household member names, ages, and relationships | References `families` (Cascade Delete) |
| `electricity_rates` | Stores date-effective electricity unit prices for tariff snapshotting | Referenced implicitly during billing calculation |
| `electricity_readings`| Stores physical meter readings and automatically computes consumed units | References `rooms`; Referenced by `bills` |
| `bills` | Stores immutable monthly financial snapshots (rent, units, rate, total) | References `families`, `rooms`, `electricity_readings`; Referenced by `payments` |
| `payments` | Stores individual payment transactions against generated bills | References `bills` |
| `system_settings` | Stores global property metadata, contact details, and UPI receiver info | Standalone configuration table |

---

### 4.2 Detailed Table Specifications

#### 1. Table: `admin`
Stores system operator authentication data.

| Column | Data Type | Modifiers | Description |
| :--- | :--- | :--- | :--- |
| `admin_id` | INT | PRIMARY KEY, AUTO_INCREMENT | Unique administrator ID |
| `username` | VARCHAR(50) | NOT NULL, UNIQUE | Administrative login username |
| `password_hash` | VARCHAR(255) | NOT NULL | Werkzeug-compatible PBKDF2:SHA256 password hash |

#### 2. Table: `rooms`
Maintains room capacity, location, rent structure, and live occupancy states.

| Column | Data Type | Modifiers | Description |
| :--- | :--- | :--- | :--- |
| `room_id` | INT | PRIMARY KEY, AUTO_INCREMENT | Unique room identifier |
| `room_number` | VARCHAR(10) | NOT NULL, UNIQUE | Room code or number (e.g., 101, A-12) |
| `floor` | INT | NOT NULL | Floor number (0 for Ground, 1, 2, etc.) |
| `capacity` | INT | NOT NULL | Maximum resident capacity count |
| `current_rent` | DECIMAL(10,2) | NOT NULL | Default monthly room rental rate |
| `status` | ENUM | NOT NULL, DEFAULT 'AVAILABLE' | Values: `'AVAILABLE'`, `'OCCUPIED'`, `'MAINTENANCE'` |

- **Indexes:** `idx_rooms_status (status)`, `idx_rooms_floor (floor)`

#### 3. Table: `families`
Stores active and historical tenant records.

| Column | Data Type | Modifiers | Description |
| :--- | :--- | :--- | :--- |
| `family_id` | INT | PRIMARY KEY, AUTO_INCREMENT | Unique tenant family identifier |
| `room_id` | INT | NOT NULL, FK to `rooms(room_id)` | Allocated room identifier |
| `head_name` | VARCHAR(100) | NOT NULL | Full name of primary family head |
| `head_phone` | VARCHAR(15) | NOT NULL | Primary contact phone number |
| `move_in_date` | DATE | NOT NULL | Tenancy commencement date |
| `move_out_date` | DATE | NULL | Date of checkout (NULL while active) |
| `status` | ENUM | NOT NULL, DEFAULT 'ACTIVE' | Values: `'ACTIVE'`, `'CHECKED_OUT'` |

- **Indexes:** `idx_families_room_status (room_id, status)`, `idx_families_status (status)`

#### 4. Table: `family_members`
Stores household members associated with a tenant family.

| Column | Data Type | Modifiers | Description |
| :--- | :--- | :--- | :--- |
| `member_id` | INT | PRIMARY KEY, AUTO_INCREMENT | Unique member identifier |
| `family_id` | INT | NOT NULL, FK to `families(family_id)` | Parent family record (ON DELETE CASCADE) |
| `full_name` | VARCHAR(100) | NOT NULL | Full name of member |
| `age` | INT | NOT NULL | Age in years (Checked: 0 to 120) |
| `relationship_to_head`| VARCHAR(50)| NOT NULL, DEFAULT 'Member'| Relationship to family head |

- **Indexes:** `idx_family_members_family (family_id)`

#### 5. Table: `electricity_rates`
Maintains historical and active electricity unit charges.

| Column | Data Type | Modifiers | Description |
| :--- | :--- | :--- | :--- |
| `rate_id` | INT | PRIMARY KEY, AUTO_INCREMENT | Unique rate record identifier |
| `rate_per_unit` | DECIMAL(6,2) | NOT NULL | Tariff cost per kWh unit (in INR) |
| `effective_from` | DATE | NOT NULL | Start date of rate applicability |
| `effective_to` | DATE | NULL | Expiration date (NULL indicates active rate) |

- **Indexes:** `idx_electricity_rates_effective (effective_from, effective_to)`

#### 6. Table: `electricity_readings`
Records meter captures and calculates consumption automatically via database generated columns.

| Column | Data Type | Modifiers | Description |
| :--- | :--- | :--- | :--- |
| `reading_id` | INT | PRIMARY KEY, AUTO_INCREMENT | Unique meter reading identifier |
| `room_id` | INT | NOT NULL, FK to `rooms(room_id)` | Associated room |
| `reading_date` | DATE | NOT NULL | Date meter was recorded |
| `previous_reading` | DECIMAL(10,2)| NOT NULL | Prior meter reading value |
| `current_reading` | DECIMAL(10,2)| NOT NULL | Newly observed meter reading value |
| `units_consumed` | DECIMAL(10,2)| GENERATED ALWAYS AS (current - previous) STORED | Automatically computed consumption |

- **Constraints:** `chk_reading_progress CHECK (current_reading >= previous_reading)`, `uq_reading_room_date UNIQUE (room_id, reading_date)`
- **Indexes:** `idx_readings_room_date (room_id, reading_date)`

#### 7. Table: `bills`
Stores immutable monthly invoice snapshots.

| Column | Data Type | Modifiers | Description |
| :--- | :--- | :--- | :--- |
| `bill_id` | INT | PRIMARY KEY, AUTO_INCREMENT | Unique invoice/bill identifier |
| `family_id` | INT | NOT NULL, FK to `families(family_id)` | Tenant family billed |
| `room_id` | INT | NOT NULL, FK to `rooms(room_id)` | Room billed |
| `reading_id` | INT | NOT NULL, FK to `electricity_readings`| Meter reading reference |
| `billing_month` | VARCHAR(7) | NOT NULL | Format `YYYY-MM` (e.g. 2026-08) |
| `rent_amount` | DECIMAL(10,2)| NOT NULL | Frozen room rent snapshot |
| `units_consumed` | DECIMAL(10,2)| NOT NULL | Frozen electricity units snapshot |
| `electricity_rate` | DECIMAL(6,2) | NOT NULL | Frozen rate per unit snapshot |
| `electricity_amount`| DECIMAL(10,2)| NOT NULL | Computed electricity subtotal |
| `other_charges` | DECIMAL(10,2)| NOT NULL, DEFAULT 0.00 | Maintenance, water, or miscellaneous fees |
| `total_payable` | DECIMAL(10,2)| NOT NULL | Total gross invoice amount |
| `due_date` | DATE | NOT NULL | Final payment due date |
| `payment_status` | ENUM | NOT NULL, DEFAULT 'UNPAID' | Values: `'UNPAID'`, `'PARTIALLY_PAID'`, `'PAID'` |

- **Constraints:** `uq_bill_family_month UNIQUE (family_id, billing_month)`
- **Indexes:** `idx_bills_family_month (family_id, billing_month)`, `idx_bills_status_due (payment_status, due_date)`

#### 8. Table: `payments`
Tracks financial transactions recorded against invoices.

| Column | Data Type | Modifiers | Description |
| :--- | :--- | :--- | :--- |
| `payment_id` | INT | PRIMARY KEY, AUTO_INCREMENT | Unique transaction identifier |
| `bill_id` | INT | NOT NULL, FK to `bills(bill_id)` | Target invoice identifier |
| `amount_paid` | DECIMAL(10,2)| NOT NULL | Transaction amount |
| `payment_date` | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Exact date and time of payment |
| `payment_method` | ENUM | NOT NULL | Values: `'UPI'`, `'CASH'`, `'BANK_TRANSFER'` |
| `transaction_ref`| VARCHAR(100)| NULL | UTR, bank reference, or cash receipt number |

- **Constraints:** `chk_payment_positive CHECK (amount_paid > 0)`
- **Indexes:** `idx_payments_bill_date (bill_id, payment_date)`

#### 9. Table: `system_settings`
Single-row configuration record storing property branding and payment receiving parameters.

| Column | Data Type | Modifiers | Description |
| :--- | :--- | :--- | :--- |
| `setting_id` | INT | PRIMARY KEY, AUTO_INCREMENT | Setting row identifier |
| `upi_id` | VARCHAR(100)| NOT NULL | Virtual Payment Address (VPA) for UPI QR |
| `upi_name` | VARCHAR(100)| NOT NULL | Registered receiver name for UPI transactions |
| `property_name` | VARCHAR(150)| NOT NULL | Official commercial name of accommodation |
| `property_contact`| VARCHAR(15) | NOT NULL | Landlord/Manager primary telephone number |

---

## 5. Core Business Rules & Accounting Logic

The system incorporates rigorous DBMS and financial constraints to prevent data inconsistency:

1. **Single Active Tenancy per Room:** A room can have at most one active family assigned to it (`status = 'ACTIVE'`). Allocating a family updates the room status to `OCCUPIED`.
2. **Occupancy Limit Validation:** The capacity field in `rooms` defines the maximum allowable occupants. The family head occupies 1 place. Additional members entered cannot exceed `capacity - 1`.
3. **Automatic 30-Day Cycle Detection:** Billing cycles are computed based on the difference between the current date and the latest recorded meter reading date (or the family move-in date if no prior reading exists). When `cycle_days >= 30`, the dashboard and electricity panel trigger warning badges.
4. **Immutable Historical Snapshots:** When a bill is created, the system locks in the exact values of:
   - `rent_amount` (from `rooms.current_rent`)
   - `units_consumed` (from `electricity_readings.units_consumed`)
   - `electricity_rate` (from `electricity_rates` applicable on the reading date)
   - `other_charges` (manually entered fees)
   - `total_payable` = `rent_amount + (units_consumed * electricity_rate) + other_charges`
   *Modifying future room rents or electricity unit rates has zero impact on past generated bills.*
5. **Progressive Payment Lifecycle:**
   - Total payments = 0.00 $\rightarrow$ `UNPAID`
   - 0.00 < Total payments < `total_payable` $\rightarrow$ `PARTIALLY_PAID`
   - Total payments $\ge$ `total_payable` $\rightarrow$ `PAID`
6. **Dynamic UPI URI Formulation:** Generates standard merchant payment URIs in the format:
   `upi://pay?pa={upi_id}&pn={upi_name}&am={balance}&cu=INR`
   The QR code encodes only the remaining outstanding balance.
7. **Safe Tenant Checkout Lock:** A tenant family cannot be checked out (`status = 'CHECKED_OUT'`) if any bill linked to that family has a status of `UNPAID` or `PARTIALLY_PAID`. Checking out releases the room back to `AVAILABLE`.

---

## 6. UI/UX Design System Specification

The user interface follows a modern, minimal, professional **SaaS Design System** implemented in `static/css/style.css`.

### 6.1 Color Palette Tokens

| Variable Name | Hex Code | Purpose & Usage |
| :--- | :--- | :--- |
| `--primary` | `#2563EB` | Royal Blue: Primary action buttons, active navigation, focused borders |
| `--primary-hover` | `#1D4ED8` | Darker Blue: Interactive hover states for primary buttons |
| `--primary-light` | `#EFF6FF` | Soft Tinted Blue: Active sidebar link background, focus highlight |
| `--background` | `#F8FAFC` | Light Slate: Global application canvas background |
| `--surface` | `#FFFFFF` | Pure White: Card containers, topbar, sidebar, table rows |
| `--surface-muted`| `#F1F5F9` | Neutral Light: Table header backgrounds, user profile tags |
| `--border` | `#E2E8F0` | Subtle Slate: Standard 1px structural container borders |
| `--border-light` | `#EEF2F7` | Ultra-subtle divider lines between table rows |
| `--text-primary` | `#0F172A` | Deep Charcoal: Main titles, headings, and primary body text |
| `--text-secondary`| `#475569`| Medium Slate: Descriptions, table labels, metadata |
| `--text-muted` | `#94A3B8` | Light Slate: Placeholders, timestamps, supporting captions |
| `--success` | `#16A34A` | Emerald Green: Paid badges, available statuses, active state dots |
| `--success-bg` | `#F0FDF4` | Soft Emerald Tint: Background for success badges and alerts |
| `--warning` | `#D97706` | Warm Amber: Partially paid badges, billing cycles $\ge 30$ days |
| `--warning-bg` | `#FFFBEB` | Soft Amber Tint: Background for warning badges and due notices |
| `--danger` | `#DC2626` | Crimson Red: Unpaid badges, maintenance status, checkout actions |
| `--danger-bg` | `#FEF2F2` | Soft Red Tint: Background for danger badges and error banners |

### 6.2 Typography Hierarchy

- **Base Font Family:** `Inter`, ui-sans-serif, system-ui, -apple-system, sans-serif
- **Page Titles:** 22px / 24px, Font-weight: 600, Line-height: 1.25
- **Section & Card Titles:** 14px / 16px, Font-weight: 600
- **Body Text:** 13.5px / 14px, Font-weight: 400
- **Small & Metadata:** 12px / 13px, Font-weight: 500
- **Table Numbers / Monetary:** Tabular numbers (`font-variant-numeric: tabular-nums`), right-aligned.

### 6.3 Component Standards

1. **Sidebar Navigation:**
   - Width: 240px fixed width on desktop.
   - Divided into 3 semantic groups: `MAIN` (Dashboard, Rooms, Tenants), `FINANCE` (Electricity, Billing), `SYSTEM` (Settings).
   - Active link: Highlighted with `--primary-light` (`#EFF6FF`) background and `--primary` (`#2563EB`) text.
   - Mobile: Transforms into an off-canvas drawer toggled via the topbar hamburger button.
2. **Top Bar:**
   - Height: 56px sticky header with subtle bottom border (`1px solid #E2E8F0`).
   - Displays live property status dot and current formatted system date.
3. **Cards & Surfaces:**
   - White background, 1px subtle border (`#E2E8F0`), border-radius: 10px (`--radius-lg`), zero heavy drop shadows.
4. **Status Badges:**
   - Pill badges with a 6px status dot (`● Paid`, `● Available`, `● Due`, `● Unpaid`).
   - Uses matching light background and deep text contrast.
5. **Buttons:**
   - Standard height: 38px (Small: 32px), border-radius: 8px (`--radius-md`), font-weight: 500.

---

## 7. Application Route Map & Controller Endpoints

| Route Path | HTTP Methods | Function / Controller | Authentication | Description |
| :--- | :---: | :--- | :---: | :--- |
| `/` | `GET` | `home()` | Optional | Redirects to `/dashboard` if logged in, else `/login` |
| `/login` | `GET`, `POST` | `login()` | Public | Admin login portal with credential verification |
| `/logout` | `GET` | `logout()` | Session | Clears session data and redirects to login |
| `/dashboard` | `GET` | `dashboard()` | `@login_required` | Main metrics, due reading cycles, and recent invoices |
| `/rooms` | `GET`, `POST` | `rooms()` | `@login_required` | Add room, edit room properties, switch room status |
| `/families` | `GET`, `POST` | `families()` | `@login_required` | Allocate tenant family to room, record members |
| `/families/<id>/checkout` | `POST` | `checkout_family()` | `@login_required` | Validates zero outstanding balance and frees room |
| `/electricity` | `GET`, `POST` | `electricity()` | `@login_required` | Tracks cycle durations and records meter readings |
| `/bills` | `GET` | `bills()` | `@login_required` | Filterable historical billing snapshots register |
| `/bills/<id>` | `GET` | `bill_detail()` | `@login_required` | Displays invoice snapshot, payment ledger, and UPI QR |
| `/bills/<id>/qr.png` | `GET` | `bill_qr()` | `@login_required` | Streams dynamically generated binary PNG of UPI QR |
| `/bills/<id>/pdf` | `GET` | `bill_pdf()` | `@login_required` | Compiles and downloads ReportLab PDF invoice |
| `/payments/<id>` | `POST` | `record_payment()` | `@login_required` | Records transaction and updates invoice payment status |
| `/settings` | `GET`, `POST` | `settings()` | `@login_required` | Configures property profile, UPI VPA, tariffs, password |

---

## 8. Installation, Configuration & Execution

### 8.1 System Requirements
- Python 3.10 or higher
- MySQL Server 8.0 or higher (running on port 3306)
- Git (optional)

### 8.2 Step-by-Step Installation

#### Step 1: Clone or Enter the Project Directory
```plaintext
cd rental_accommodation_system
```

#### Step 2: Set Up Python Virtual Environment
**On Windows (PowerShell):**
```plaintext
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**On Linux / macOS:**
```plaintext
python3 -m venv .venv
source .venv/bin/activate
```

#### Step 3: Install Required Packages
```plaintext
pip install -r requirements.txt
```

#### Step 4: Configure Environment Variables
Create the active `.env` file from `.env.example`:
```plaintext
SECRET_KEY=your-secure-random-secret-key
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=rental_accommodation
```

#### Step 5: Initialize the MySQL Database
Execute the database initialization scripts in sequence:
```plaintext
mysql -u root -p < sql/schema.sql
mysql -u root -p < sql/seed.sql
```

#### Step 6: Start the Application
```plaintext
python run.py
```
Open **`http://127.0.0.1:5000`** in any modern web browser.

---

## 9. Default Credentials & Security Guidelines

The seed database script provisions default credentials for immediate setup:

| Attribute | Default Value |
| :--- | :--- |
| **Login URL** | `http://127.0.0.1:5000/login` |
| **Default Username** | `admin` |
| **Default Password** | `admin123` |

### Security Measures:
- Passwords are encrypted using Werkzeug's `generate_password_hash` with `pbkdf2:sha256:600000` iterations.
- Database access uses parameterized SQL queries throughout all endpoints to prevent SQL injection vulnerabilities.
- Financial transactions execute inside ACID-compliant rollback transactions (`transaction(callback)`).
- Session identifiers are signed using `SECRET_KEY` and cleared upon logout.
- In production, administrators should immediately update the default password via the **Settings** portal (`/settings`).

---

## 10. Conclusion

The **NIVARA** accommodation management system combines robust relational database modeling, clean transaction handling, and a modern, high-contrast SaaS interface. By isolating financial snapshots and enforcing strict referential integrity at the database layer, the platform guarantees zero financial data drift while offering a fast, responsive user experience for day-to-day property management operations.
