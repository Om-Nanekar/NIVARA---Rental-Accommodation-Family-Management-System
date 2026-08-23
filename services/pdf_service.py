from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

def build_bill_pdf(bill, family, room, settings, payment_summary):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm,
                            topMargin=15*mm, bottomMargin=15*mm)
    styles = getSampleStyleSheet()
    title = ParagraphStyle("BillTitle", parent=styles["Title"], fontSize=19, spaceAfter=8)
    body = styles["BodyText"]
    story = [
        Paragraph(settings["property_name"], title),
        Paragraph(f"Contact: {settings['property_contact']}", body),
        Spacer(1, 6*mm),
        Paragraph(f"<b>Invoice #{bill['bill_id']}</b> &nbsp; | &nbsp; Billing month: {bill['billing_month']}", body),
        Spacer(1, 3*mm),
    ]
    details = [
        ["Family Head", family["head_name"], "Room", room["room_number"]],
        ["Phone", family["head_phone"], "Due Date", str(bill["due_date"])],
        ["Move-in Date", str(family["move_in_date"]), "Status", bill["payment_status"]],
    ]
    t = Table(details, colWidths=[30*mm, 65*mm, 30*mm, 55*mm])
    t.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.4, colors.grey),
        ("BACKGROUND", (0,0), (0,-1), colors.whitesmoke),
        ("BACKGROUND", (2,0), (2,-1), colors.whitesmoke),
        ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME", (2,0), (2,-1), "Helvetica-Bold"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))
    story += [t, Spacer(1, 8*mm)]
    line_items = [
        ["Description", "Amount (INR)"],
        ["Monthly Rent", f"{bill['rent_amount']:.2f}"],
        [f"Electricity ({bill['units_consumed']:.2f} units × ₹{bill['electricity_rate']:.2f})", f"{bill['electricity_amount']:.2f}"],
        ["Other Charges", f"{bill['other_charges']:.2f}"],
        ["Total Payable", f"{bill['total_payable']:.2f}"],
        ["Total Paid", f"{payment_summary['paid']:.2f}"],
        ["Balance Due", f"{payment_summary['balance']:.2f}"],
    ]
    t2 = Table(line_items, colWidths=[125*mm, 55*mm], hAlign="LEFT")
    t2.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.4, colors.grey),
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#e9ecef")),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTNAME", (0,4), (-1,6), "Helvetica-Bold"),
        ("ALIGN", (1,1), (1,-1), "RIGHT"),
    ]))
    story += [t2, Spacer(1, 8*mm), Paragraph("Generated electronically. Historical billing values are stored as a financial snapshot.", body)]
    doc.build(story)
    buffer.seek(0)
    return buffer
