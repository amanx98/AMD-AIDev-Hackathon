from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from amd_model import AMDModel
from evolus_client import EvolusClient
from extraction import extract_invoice
from matching import load_purchase_orders, reconcile
from policy import POLICY_TEXT, grounded_answer

load_dotenv()

st.set_page_config(page_title="LedgerLens", page_icon="🧾", layout="wide")

BASE = Path(__file__).parent
SAMPLE_DIR = BASE / "sample_data" / "invoices"
PO_PATH = BASE / "sample_data" / "purchase_orders.csv"

model = AMDModel()
evolus = EvolusClient()

for key, default in (("audit", []), ("invoice", None), ("decision", None)):
    st.session_state.setdefault(key, default)

st.title("🧾 LedgerLens")
st.caption("Accounts-Payable Exception Copilot — AMD-hosted model + Evolus")

with st.sidebar:
    st.subheader("Connections")
    st.write(f"AMD model: **{model.status()}**")
    st.write(f"Evolus: **{evolus.status()}**")
    st.divider()
    price_tol = st.slider("Price tolerance (%)", 0, 10, 2) / 100
    st.divider()
    st.subheader("Procurement policy")
    st.text(POLICY_TEXT.strip())

st.subheader("1. Ingest supplier document")
choice = st.radio("Source", ["Sample invoice", "Upload file"], horizontal=True)

content, filename = None, None
if choice == "Sample invoice":
    samples = sorted(p.name for p in SAMPLE_DIR.glob("*")) if SAMPLE_DIR.exists() else []
    if samples:
        selected = st.selectbox("Sample invoice", samples)
        content = (SAMPLE_DIR / selected).read_bytes()
        filename = selected
    else:
        st.warning("No sample invoices found.")
else:
    uploaded = st.file_uploader("Upload invoice (PDF or TXT)", type=["pdf", "txt"])
    if uploaded is not None:
        content = uploaded.read()
        filename = uploaded.name

if st.button("Reconcile invoice", type="primary", disabled=content is None):
    invoice = extract_invoice(filename, content)
    if evolus.enabled:
        extracted = evolus.extract_document(filename, content)
        if extracted:
            invoice = extracted

    decision = reconcile(invoice, load_purchase_orders(PO_PATH), price_tolerance=price_tol)

    if invoice.get("invoice_number") and any(
        entry["invoice"] == invoice["invoice_number"] for entry in st.session_state.audit
    ):
        decision["flags"].append(f"Duplicate invoice {invoice['invoice_number']} already recorded.")
        decision["decision"] = "EXCEPTION"

    decision["explanation"] = grounded_answer(
        "why was this flagged" if decision["flags"] else "summary", decision, model
    )

    if decision["decision"] == "AUTO_APPROVE" and evolus.enabled:
        evolus.execute_workflow({"action": "push_to_erp", "invoice": invoice})

    st.session_state.invoice = invoice
    st.session_state.decision = decision
    st.session_state.audit.append(
        {
            "invoice": invoice.get("invoice_number"),
            "vendor": invoice.get("vendor"),
            "decision": decision["decision"],
            "flags": len(decision["flags"]),
        }
    )

invoice = st.session_state.invoice
decision = st.session_state.decision

if invoice and decision:
    left, right = st.columns(2)
    with left:
        st.subheader("2. Extracted invoice")
        st.json(invoice)
    with right:
        st.subheader("3. Reconciliation")
        if decision["decision"] == "AUTO_APPROVE":
            st.success("AUTO-APPROVED — pushed to the accounting system")
        else:
            st.error("EXCEPTION — escalated to a human reviewer")
        for flag in decision["flags"]:
            st.write(f"- {flag}")
        st.info(decision["explanation"])
        if decision["lines"]:
            st.dataframe(pd.DataFrame(decision["lines"]), use_container_width=True)

    st.subheader("4. Ask about this decision")
    question = st.text_input("e.g. why was this flagged? / what is the price tolerance?")
    if question:
        st.info(grounded_answer(question, decision, model))

st.subheader("5. Audit trail")
if st.session_state.audit:
    st.dataframe(pd.DataFrame(st.session_state.audit), use_container_width=True)
else:
    st.write("No invoices processed yet.")
