from io import BytesIO
from urllib.parse import quote
import qrcode

def build_upi_uri(upi_id, upi_name, amount):
    return (
        "upi://pay?"
        f"pa={quote(str(upi_id), safe='')}"
        f"&pn={quote(str(upi_name), safe='')}"
        f"&am={float(amount):.2f}"
        "&cu=INR"
    )

def generate_qr_png(upi_id, upi_name, amount):
    uri = build_upi_uri(upi_id, upi_name, amount)
    qr = qrcode.QRCode(version=None, box_size=10, border=4)
    qr.add_data(uri)
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return uri, buffer
