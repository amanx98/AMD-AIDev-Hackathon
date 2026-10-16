POLICY_TEXT = """
LEDGERLENS PROCUREMENT & PAYMENT POLICY

1. Tolerances: Unit prices may deviate up to 2% from the purchase order. Quantities may
   not exceed the ordered quantity. Totals must match the PO within 2%.
2. Vendor identity: The invoice vendor must match the purchase order vendor exactly. Any
   vendor mismatch is a hard exception and must be reviewed by a human.
3. Duplicate invoices: An invoice number already recorded for the same vendor is a
   duplicate and must never be paid twice.
4. Bank details: Any change to supplier bank details is treated as a fraud risk and always
   requires human verification out of band.
5. Three-way match: Invoices are matched against the purchase order and the goods receipt.
   Only fully matched invoices are approved for straight-through processing.
6. Escalation: Every exception is routed to an accounts-payable clerk with a plain-language
   explanation and a suggested resolution. Clean invoices are auto-approved and pushed to
   the accounting system.
"""


def grounded_answer(question, decision, model=None):
    question_lower = question.lower()

    if model is not None and model.enabled:
        evidence = "\n".join(decision.get("flags", [])) or "No flags: the invoice fully matches the purchase order."
        prompt = (
            f"Policy:\n{POLICY_TEXT}\n\n"
            f"Invoice decision: {decision.get('decision')}\n"
            f"Evidence:\n{evidence}\n\n"
            f"Question: {question}\n"
            "Answer concisely and cite the policy clause number."
        )
        reply = model.reason(prompt)
        if reply:
            return reply

    if "duplicate" in question_lower:
        return "Policy clause 3: an invoice number already recorded for the same vendor is a duplicate and must never be paid twice."
    if "bank" in question_lower:
        return "Policy clause 4: any change to supplier bank details is a fraud risk and always requires human verification out of band."
    if "vendor" in question_lower:
        return "Policy clause 2: the vendor must match the purchase order exactly; a mismatch is a hard exception for human review."
    if "tolerance" in question_lower or "price" in question_lower:
        return "Policy clause 1: unit prices may deviate up to 2% from the purchase order; quantities may not exceed the ordered quantity."
    if decision.get("flags"):
        return "This invoice was flagged because: " + " ".join(decision["flags"]) + " Policy clauses 1-6 require human review of exceptions."
    return "This invoice fully matches the purchase order, so policy clause 5 approves it for straight-through processing."
