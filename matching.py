from pathlib import Path

import pandas as pd

DEFAULT_PO_PATH = Path(__file__).parent / "sample_data" / "purchase_orders.csv"


def load_purchase_orders(path=DEFAULT_PO_PATH) -> pd.DataFrame:
    return pd.read_csv(path)


def _find_po_line(invoice_line, po_lines):
    description = invoice_line["description"].lower()
    for _, row in po_lines.iterrows():
        po_description = str(row["description"]).lower()
        if po_description in description or description in po_description:
            return row
    return None


def reconcile(invoice, pos, price_tolerance=0.02):
    flags = []
    lines = []
    po_number = invoice.get("po_number")
    po_lines = pos[pos["po_number"] == po_number]

    if po_lines.empty:
        flags.append(f"No purchase order found for PO {po_number}.")
    else:
        po_vendor = po_lines.iloc[0]["vendor"]
        if str(po_vendor).lower() != str(invoice.get("vendor", "")).lower():
            flags.append(
                f"Vendor mismatch: invoice '{invoice.get('vendor')}' vs PO '{po_vendor}'."
            )

        po_total = float((po_lines["unit_price"] * po_lines["quantity"]).sum())

        for line in invoice.get("line_items", []):
            po_line = _find_po_line(line, po_lines)
            if po_line is None:
                flags.append(f"Line not on PO: {line['description']}.")
                lines.append(
                    {**line, "po_price": None, "po_qty": None, "price_ok": False, "qty_ok": False}
                )
                continue

            po_price = float(po_line["unit_price"])
            po_qty = int(po_line["quantity"])
            price_ok = abs(line["unit_price"] - po_price) <= price_tolerance * po_price
            qty_ok = line["quantity"] <= po_qty

            if not price_ok:
                flags.append(
                    f"Price mismatch on {line['description']}: invoiced {line['unit_price']} vs PO {po_price}."
                )
            if not qty_ok:
                flags.append(
                    f"Quantity exceeds PO on {line['description']}: invoiced {line['quantity']} vs PO {po_qty}."
                )

            lines.append(
                {
                    **line,
                    "po_price": po_price,
                    "po_qty": po_qty,
                    "price_ok": price_ok,
                    "qty_ok": qty_ok,
                }
            )

        invoice_net = invoice.get("subtotal", invoice.get("total"))
        if invoice_net is not None and abs(invoice_net - po_total) > max(
            1.0, price_tolerance * po_total
        ):
            flags.append(
                f"Total mismatch: invoice {invoice_net} vs PO {round(po_total, 2)}."
            )

    decision = "AUTO_APPROVE" if not flags else "EXCEPTION"
    return {"decision": decision, "flags": flags, "lines": lines, "po_number": po_number}
