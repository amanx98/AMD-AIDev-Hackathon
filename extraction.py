import io
import re

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

FIELD_PATTERNS = {
    "vendor": r"Vendor:\s*(.+)",
    "invoice_number": r"Invoice Number:\s*(\S+)",
    "po_number": r"PO Number:\s*(\S+)",
    "invoice_date": r"Invoice Date:\s*(\S+)",
    "currency": r"Currency:\s*(\S+)",
    "bank_details": r"Bank Details:\s*(.+)",
    "subtotal": r"Subtotal:\s*([\d.]+)",
    "tax": r"Tax:\s*([\d.]+)",
    "total": r"Total:\s*([\d.]+)",
}

LINE_PATTERN = re.compile(
    r"^-\s*(?P<description>.+?)\s*@\s*(?P<unit_price>[\d.]+)\s*x\s*(?P<quantity>\d+)\s*$",
    re.MULTILINE,
)


def pdf_to_text(content: bytes) -> str:
    if PdfReader is None:
        return ""
    reader = PdfReader(io.BytesIO(content))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def extract_invoice_from_text(text: str) -> dict:
    invoice = {}
    for key, pattern in FIELD_PATTERNS.items():
        match = re.search(pattern, text)
        if match:
            invoice[key] = match.group(1).strip()
    for numeric in ("subtotal", "tax", "total"):
        if numeric in invoice:
            try:
                invoice[numeric] = float(invoice[numeric])
            except ValueError:
                pass
    invoice["line_items"] = [
        {
            "description": match.group("description").strip(),
            "unit_price": float(match.group("unit_price")),
            "quantity": int(match.group("quantity")),
        }
        for match in LINE_PATTERN.finditer(text)
    ]
    return invoice


def extract_invoice(filename: str, content: bytes) -> dict:
    if filename.lower().endswith(".pdf"):
        text = pdf_to_text(content)
    else:
        text = content.decode("utf-8", errors="ignore")
    return extract_invoice_from_text(text)
