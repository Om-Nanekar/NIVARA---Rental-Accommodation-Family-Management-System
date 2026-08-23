from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, abort, jsonify
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from database import get_connection, fetch_all, fetch_one, transaction, execute
from services.qr_service import generate_qr_png, build_upi_uri
from services.pdf_service import build_bill_pdf

app = Flask(__name__)
app.config.from_object(Config)


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "admin_id" not in session:
            return redirect(url_for("login", next=request.path))
        return fn(*args, **kwargs)
    return wrapper


def decimal_field(name, default="0"):
    try:
        value = Decimal(request.form.get(name, default))
        if value < 0:
            raise InvalidOperation
        return value
    except (InvalidOperation, ValueError):
        raise ValueError(f"Invalid value for {name}.")


def get_settings():
    return fetch_one("SELECT * FROM system_settings ORDER BY setting_id LIMIT 1")


def current_rate(on_date=None):
    on_date = on_date or date.today()
    return fetch_one(
        """SELECT * FROM electricity_rates
           WHERE effective_from <= %s
             AND (effective_to IS NULL OR effective_to >= %s)
           ORDER BY effective_from DESC, rate_id DESC LIMIT 1""",
        (on_date, on_date),
    )


def cycle_info(family):
    last = family.get("last_reading_date") or family["move_in_date"]
    days = (date.today() - last).days
    return days, days >= 30


def calculate_payment_status(total, paid):
    if paid <= 0:
        return "UNPAID"
    if paid >= total:
        return "PAID"
    return "PARTIALLY_PAID"


@app.template_filter("money")
def money(value):
    return f"₹{Decimal(value or 0):,.2f}"


@app.context_processor
def inject_globals():
    return {"current_date": date.today()}


@app.route("/")
def home():
    return redirect(url_for("dashboard")) if "admin_id" in session else redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        admin = fetch_one("SELECT * FROM admin WHERE username = %s", (username,))
        if admin and check_password_hash(admin["password_hash"], password):
            session.clear()
            session["admin_id"] = admin["admin_id"]
            session["username"] = admin["username"]
            return redirect(request.args.get("next") or url_for("dashboard"))
        flash("Invalid username or password.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    counts = {
        "rooms": fetch_one("SELECT COUNT(*) AS c FROM rooms")["c"],
        "available_rooms": fetch_one("SELECT COUNT(*) AS c FROM rooms WHERE status='AVAILABLE'")["c"],
        "occupied_rooms": fetch_one("SELECT COUNT(*) AS c FROM rooms WHERE status='OCCUPIED'")["c"],
        "families": fetch_one("SELECT COUNT(*) AS c FROM families WHERE status='ACTIVE'")["c"],
        "due_cycles": fetch_one("""
            SELECT COUNT(*) AS c FROM families f
            WHERE f.status='ACTIVE' AND DATEDIFF(CURRENT_DATE,
                COALESCE((SELECT MAX(er.reading_date) FROM electricity_readings er WHERE er.room_id=f.room_id), f.move_in_date)) >= 30
        """)["c"],
        "unpaid": fetch_one("SELECT COUNT(*) AS c FROM bills WHERE payment_status <> 'PAID'")["c"],
        "outstanding": fetch_one("""
    SELECT COALESCE(
        SUM(
            GREATEST(
                b.total_payable - COALESCE(p.paid, 0),
                0
            )
        ),
        0
    ) AS v
    FROM bills b
    LEFT JOIN (
        SELECT
            bill_id,
            SUM(amount_paid) AS paid
        FROM payments
        GROUP BY bill_id
    ) p
        ON p.bill_id = b.bill_id
""")["v"],
    }
    recent_bills = fetch_all("""
        SELECT b.*, f.head_name, r.room_number,
               COALESCE(p.paid,0) AS paid,
               (b.total_payable - COALESCE(p.paid,0)) AS balance
        FROM bills b
        JOIN families f ON f.family_id=b.family_id
        JOIN rooms r ON r.room_id=b.room_id
        LEFT JOIN (SELECT bill_id, SUM(amount_paid) paid FROM payments GROUP BY bill_id) p ON p.bill_id=b.bill_id
        ORDER BY b.bill_id DESC LIMIT 8
    """)
    due_families = fetch_all("""
        SELECT f.family_id, f.head_name, f.head_phone, f.move_in_date, r.room_number,
               COALESCE(MAX(er.reading_date), f.move_in_date) AS last_reading_date,
               DATEDIFF(CURRENT_DATE, COALESCE(MAX(er.reading_date), f.move_in_date)) AS cycle_days
        FROM families f
        JOIN rooms r ON r.room_id=f.room_id
        LEFT JOIN electricity_readings er ON er.room_id=f.room_id
        WHERE f.status='ACTIVE'
        GROUP BY f.family_id, f.head_name, f.head_phone, f.move_in_date, r.room_number
        HAVING cycle_days >= 30
        ORDER BY cycle_days DESC
    """)
    return render_template("dashboard.html", counts=counts, recent_bills=recent_bills, due_families=due_families)


@app.route("/rooms", methods=["GET", "POST"])
@login_required
def rooms():
    if request.method == "POST":
        action = request.form.get("action")
        try:
            if action == "add":
                execute("""INSERT INTO rooms(room_number,floor,capacity,current_rent,status)
                           VALUES(%s,%s,%s,%s,%s)""", (
                    request.form["room_number"].strip(), int(request.form["floor"]),
                    int(request.form["capacity"]), decimal_field("current_rent"),
                    request.form.get("status", "AVAILABLE"),
                ))
                flash("Room added successfully.", "success")
            elif action == "update":
                room_id = int(request.form["room_id"])
                execute("""UPDATE rooms SET room_number=%s,floor=%s,capacity=%s,current_rent=%s
                           WHERE room_id=%s""", (
                    request.form["room_number"].strip(), int(request.form["floor"]),
                    int(request.form["capacity"]), decimal_field("current_rent"), room_id
                ))
                flash("Room details updated. Existing bills remain unchanged.", "success")
            elif action == "status":
                room_id = int(request.form["room_id"])
                status = request.form["status"]
                if status == "AVAILABLE":
                    active = fetch_one("SELECT family_id FROM families WHERE room_id=%s AND status='ACTIVE'", (room_id,))
                    if active:
                        flash("An active family is still assigned to this room.", "warning")
                    else:
                        execute("UPDATE rooms SET status='AVAILABLE' WHERE room_id=%s", (room_id,))
                        flash("Room marked available.", "success")
                elif status == "MAINTENANCE":
                    active = fetch_one("SELECT family_id FROM families WHERE room_id=%s AND status='ACTIVE'", (room_id,))
                    if active:
                        flash("Cannot place an occupied room into maintenance.", "warning")
                    else:
                        execute("UPDATE rooms SET status='MAINTENANCE' WHERE room_id=%s", (room_id,))
                        flash("Room marked for maintenance.", "success")
        except Exception as exc:
            flash(f"Room operation failed: {exc}", "danger")
        return redirect(url_for("rooms"))
    room_rows = fetch_all("""
        SELECT r.*, f.head_name,
               (SELECT COUNT(*) FROM families fa WHERE fa.room_id=r.room_id AND fa.status='ACTIVE') AS active_family_count
        FROM rooms r
        LEFT JOIN families f ON f.room_id=r.room_id AND f.status='ACTIVE'
        ORDER BY r.floor, r.room_number
    """)
    return render_template("rooms.html", rooms=room_rows)


@app.route("/families", methods=["GET", "POST"])
@login_required
def families():
    if request.method == "POST":
        room_id = int(request.form["room_id"])
        head_name = request.form["head_name"].strip()
        head_phone = request.form["head_phone"].strip()
        move_in = request.form["move_in_date"] or str(date.today())
        names = request.form.getlist("member_name[]")
        ages = request.form.getlist("member_age[]")

        def create_family(conn):
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT * FROM rooms WHERE room_id=%s FOR UPDATE", (room_id,))
            room = cur.fetchone()
            if not room or room["status"] != "AVAILABLE":
                raise ValueError("Selected room is not available.")
            if len(names) > room["capacity"] - 1:
                raise ValueError(f"Room capacity is {room['capacity']}; the family head already uses one place.")
            if not head_name or not head_phone:
                raise ValueError("Family head name and phone are required.")
            cur.execute("""INSERT INTO families(room_id,head_name,head_phone,move_in_date,status)
                           VALUES(%s,%s,%s,%s,'ACTIVE')""", (room_id, head_name, head_phone, move_in))
            family_id = cur.lastrowid
            member_rows = []
            for name, age in zip(names, ages):
                if name.strip():
                    a = int(age)
                    if a < 0 or a > 120:
                        raise ValueError("Member age must be between 0 and 120.")
                    member_rows.append((family_id, name.strip(), a, "Member"))
            if member_rows:
                cur.executemany("""INSERT INTO family_members(family_id,full_name,age,relationship_to_head)
                                   VALUES(%s,%s,%s,%s)""", member_rows)
            cur.execute("UPDATE rooms SET status='OCCUPIED' WHERE room_id=%s", (room_id,))
            cur.close()
            return family_id

        try:
            transaction(create_family)
            flash("Family allocated successfully; room is now occupied.", "success")
            return redirect(url_for("families"))
        except Exception as exc:
            flash(f"Family allocation failed: {exc}", "danger")

    available_rooms = fetch_all("SELECT * FROM rooms WHERE status='AVAILABLE' ORDER BY floor, room_number")
    active_families = fetch_all("""
        SELECT f.*, r.room_number, r.capacity, COUNT(fm.member_id) AS member_count
        FROM families f JOIN rooms r ON r.room_id=f.room_id
        LEFT JOIN family_members fm ON fm.family_id=f.family_id
        WHERE f.status='ACTIVE'
        GROUP BY f.family_id
        ORDER BY r.floor, r.room_number
    """)
    return render_template("family_allocation.html", rooms=available_rooms, families=active_families)


@app.post("/families/<int:family_id>/checkout")
@login_required
def checkout_family(family_id):
    def checkout(conn):
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM families WHERE family_id=%s FOR UPDATE", (family_id,))
        family = cur.fetchone()
        if not family or family["status"] != "ACTIVE":
            raise ValueError("Family is not active.")
        cur.execute("SELECT COUNT(*) c FROM bills WHERE family_id=%s AND payment_status <> 'PAID'", (family_id,))
        if cur.fetchone()["c"]:
            raise ValueError("Family has unpaid or partially paid bills. Settle them before checkout.")
        cur.execute("UPDATE families SET status='CHECKED_OUT', move_out_date=%s WHERE family_id=%s", (date.today(), family_id))
        cur.execute("UPDATE rooms SET status='AVAILABLE' WHERE room_id=%s", (family["room_id"],))
        cur.close()
    try:
        transaction(checkout)
        flash("Family checked out and room released.", "success")
    except Exception as exc:
        flash(f"Checkout failed: {exc}", "danger")
    return redirect(url_for("families"))


@app.route("/electricity", methods=["GET", "POST"])
@login_required
def electricity():
    if request.method == "POST":
        family_id = int(request.form["family_id"])
        current_reading = Decimal(request.form["current_reading"])
        other_charges = decimal_field("other_charges", "0")
        reading_date = request.form.get("reading_date") or str(date.today())
        billing_month = request.form["billing_month"]
        due_date = request.form["due_date"]

        def create_cycle(conn):
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT * FROM families WHERE family_id=%s AND status='ACTIVE' FOR UPDATE", (family_id,))
            family = cur.fetchone()
            if not family:
                raise ValueError("Active family not found.")
            cur.execute("SELECT * FROM rooms WHERE room_id=%s", (family["room_id"],))
            room = cur.fetchone()
            cur.execute("""SELECT * FROM electricity_readings WHERE room_id=%s ORDER BY reading_date DESC, reading_id DESC LIMIT 1 FOR UPDATE""", (family["room_id"],))
            previous = cur.fetchone()
            previous_value = Decimal(previous["current_reading"]) if previous else Decimal("0")
            if current_reading < previous_value:
                raise ValueError(f"Current reading cannot be below previous reading ({previous_value}).")
            cur.execute("""SELECT * FROM electricity_rates WHERE effective_from <= %s
                           AND (effective_to IS NULL OR effective_to >= %s)
                           ORDER BY effective_from DESC, rate_id DESC LIMIT 1""", (reading_date, reading_date))
            rate = cur.fetchone()
            if not rate:
                raise ValueError("No electricity rate is active for this reading date.")
            cur.execute("""SELECT bill_id FROM bills WHERE family_id=%s AND billing_month=%s""", (family_id, billing_month))
            if cur.fetchone():
                raise ValueError("A bill already exists for this family and billing month.")
            cur.execute("""INSERT INTO electricity_readings(room_id,reading_date,previous_reading,current_reading)
                           VALUES(%s,%s,%s,%s)""", (family["room_id"], reading_date, previous_value, current_reading))
            reading_id = cur.lastrowid
            units = current_reading - previous_value
            electricity_amount = units * Decimal(rate["rate_per_unit"])
            rent = Decimal(room["current_rent"])
            total = rent + electricity_amount + other_charges
            cur.execute("""INSERT INTO bills(family_id,room_id,reading_id,billing_month,rent_amount,units_consumed,
                           electricity_rate,electricity_amount,other_charges,total_payable,due_date,payment_status)
                           VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'UNPAID')""",
                        (family_id, family["room_id"], reading_id, billing_month, rent, units,
                         rate["rate_per_unit"], electricity_amount, other_charges, total, due_date))
            bill_id = cur.lastrowid
            cur.close()
            return bill_id

        try:
            bill_id = transaction(create_cycle)
            flash("Reading recorded and immutable bill snapshot created.", "success")
            return redirect(url_for("bill_detail", bill_id=bill_id))
        except Exception as exc:
            flash(f"Cycle billing failed: {exc}", "danger")

    due_families = fetch_all("""
        SELECT f.family_id, f.head_name, r.room_number, f.move_in_date,
               COALESCE(MAX(er.reading_date), f.move_in_date) AS last_reading_date,
               DATEDIFF(CURRENT_DATE, COALESCE(MAX(er.reading_date), f.move_in_date)) AS cycle_days,
               COALESCE(MAX(er.current_reading), 0) AS last_meter
        FROM families f JOIN rooms r ON r.room_id=f.room_id
        LEFT JOIN electricity_readings er ON er.room_id=f.room_id
        WHERE f.status='ACTIVE'
        GROUP BY f.family_id, f.head_name, r.room_number, f.move_in_date
        ORDER BY cycle_days DESC
    """)
    rate = current_rate()
    return render_template("electricity.html", families=due_families, rate=rate)


@app.route("/bills")
@login_required
def bills():
    rows = fetch_all("""
        SELECT b.*, f.head_name, r.room_number,
               COALESCE(SUM(p.amount_paid),0) AS paid,
               GREATEST(
                b.total_payable - COALESCE(SUM(p.amount_paid), 0),
                0
            ) AS balance
        FROM bills b JOIN families f ON f.family_id=b.family_id JOIN rooms r ON r.room_id=b.room_id
        LEFT JOIN payments p ON p.bill_id=b.bill_id
        GROUP BY b.bill_id, f.head_name, r.room_number
        ORDER BY b.bill_id DESC
    """)
    return render_template("billing.html", bills=rows)


@app.route("/bills/<int:bill_id>")
@login_required
def bill_detail(bill_id):
    bill = fetch_one("SELECT * FROM bills WHERE bill_id=%s", (bill_id,))
    if not bill:
        abort(404)
    family = fetch_one("SELECT * FROM families WHERE family_id=%s", (bill["family_id"],))
    room = fetch_one("SELECT * FROM rooms WHERE room_id=%s", (bill["room_id"],))
    settings = get_settings()
    payments = fetch_all("SELECT * FROM payments WHERE bill_id=%s ORDER BY payment_date DESC", (bill_id,))
    paid = sum((Decimal(p["amount_paid"]) for p in payments), Decimal("0"))
    balance = max(Decimal("0"), Decimal(bill["total_payable"]) - paid)
    uri = build_upi_uri(settings["upi_id"], settings["upi_name"], balance)
    return render_template("bill_detail.html", bill=bill, family=family, room=room, settings=settings,
                           payments=payments, paid=paid, balance=balance, upi_uri=uri)


@app.route("/bills/<int:bill_id>/qr.png")
@login_required
def bill_qr(bill_id):
    row = fetch_one("""SELECT b.total_payable, s.upi_id, s.upi_name,
                      COALESCE((SELECT SUM(amount_paid) FROM payments p WHERE p.bill_id=b.bill_id),0) paid
                      FROM bills b CROSS JOIN system_settings s WHERE b.bill_id=%s LIMIT 1""", (bill_id,))
    if not row:
        abort(404)
    balance = max(Decimal("0"), Decimal(row["total_payable"]) - Decimal(row["paid"]))
    _, image = generate_qr_png(row["upi_id"], row["upi_name"], balance)
    return send_file(image, mimetype="image/png", as_attachment=False, download_name=f"bill_{bill_id}_upi.png")


@app.route("/bills/<int:bill_id>/pdf")
@login_required
def bill_pdf(bill_id):
    bill = fetch_one("SELECT * FROM bills WHERE bill_id=%s", (bill_id,))
    if not bill:
        abort(404)
    family = fetch_one("SELECT * FROM families WHERE family_id=%s", (bill["family_id"],))
    room = fetch_one("SELECT * FROM rooms WHERE room_id=%s", (bill["room_id"],))
    settings = get_settings()
    paid = Decimal(fetch_one("SELECT COALESCE(SUM(amount_paid),0) paid FROM payments WHERE bill_id=%s", (bill_id,))["paid"])
    total = Decimal(bill["total_payable"])
    payment_summary = {"paid": paid, "balance": max(Decimal("0"), total-paid)}
    pdf = build_bill_pdf(bill, family, room, settings, payment_summary)
    return send_file(pdf, mimetype="application/pdf", as_attachment=True, download_name=f"bill_{bill_id}.pdf")


@app.route("/payments/<int:bill_id>", methods=["POST"])
@login_required
def record_payment(bill_id):
    try:
        amount = decimal_field("amount_paid")
        if amount <= 0:
            raise ValueError("Payment must be greater than zero.")
        method = request.form["payment_method"]
        ref = request.form.get("transaction_ref", "").strip() or None
        def add_payment(conn):
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT total_payable FROM bills WHERE bill_id=%s FOR UPDATE", (bill_id,))
            bill = cur.fetchone()
            if not bill:
                raise ValueError("Bill not found.")
            cur.execute("SELECT COALESCE(SUM(amount_paid),0) AS paid FROM payments WHERE bill_id=%s", (bill_id,))
            paid = Decimal(cur.fetchone()["paid"])
            if paid + amount > Decimal(bill["total_payable"]):
                raise ValueError("Payment exceeds outstanding balance.")
            cur.execute("""INSERT INTO payments(bill_id,amount_paid,payment_method,transaction_ref)
                           VALUES(%s,%s,%s,%s)""", (bill_id, amount, method, ref))
            new_paid = paid + amount
            status = calculate_payment_status(Decimal(bill["total_payable"]), new_paid)
            cur.execute("UPDATE bills SET payment_status=%s WHERE bill_id=%s", (status, bill_id))
            cur.close()
        transaction(add_payment)
        flash("Payment recorded and bill status updated.", "success")
    except Exception as exc:
        flash(f"Payment failed: {exc}", "danger")
    return redirect(url_for("bill_detail", bill_id=bill_id))


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        action = request.form.get("action")
        try:
            if action == "property":
                row = get_settings()
                values = (request.form["upi_id"].strip(), request.form["upi_name"].strip(),
                          request.form["property_name"].strip(), request.form["property_contact"].strip())
                if row:
                    execute("""UPDATE system_settings SET upi_id=%s,upi_name=%s,property_name=%s,property_contact=%s
                               WHERE setting_id=%s""", values + (row["setting_id"],))
                else:
                    execute("""INSERT INTO system_settings(upi_id,upi_name,property_name,property_contact)
                               VALUES(%s,%s,%s,%s)""", values)
                flash("System settings updated.", "success")
            elif action == "rate":
                rate = decimal_field("rate_per_unit")
                effective_from = request.form["effective_from"]
                execute("INSERT INTO electricity_rates(rate_per_unit,effective_from) VALUES(%s,%s)", (rate, effective_from))
                flash("New electricity rate added. Existing bills are unaffected.", "success")
            elif action == "password":
                username = session["username"]
                admin = fetch_one("SELECT * FROM admin WHERE username=%s", (username,))
                if not admin or not check_password_hash(admin["password_hash"], request.form["current_password"]):
                    raise ValueError("Current password is incorrect.")
                new_password = request.form["new_password"]
                if len(new_password) < 8:
                    raise ValueError("New password must contain at least 8 characters.")
                execute("UPDATE admin SET password_hash=%s WHERE admin_id=%s", (generate_password_hash(new_password), admin["admin_id"]))
                flash("Password updated.", "success")
        except Exception as exc:
            flash(f"Settings update failed: {exc}", "danger")
        return redirect(url_for("settings"))
    return render_template("settings.html", settings=get_settings(), rates=fetch_all("SELECT * FROM electricity_rates ORDER BY effective_from DESC"))


@app.errorhandler(404)
def not_found(_):
    return render_template("error.html", title="Not Found", message="The requested record or page does not exist."), 404


@app.errorhandler(500)
def server_error(_):
    return render_template("error.html", title="Server Error", message="The server encountered an unexpected error."), 500


if __name__ == "__main__":
    app.run(debug=True)
