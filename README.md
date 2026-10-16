# 🧾 LedgerLens — Accounts-Payable Exception Copilot

An autonomous accounts-payable agent that reads supplier invoices, reconciles them against
purchase orders and company policy, **auto-approves clean matches**, and **escalates only true
exceptions** to a human — with a plain-language explanation and a full audit trail.

Built for the **AMD Developer Hackathon: ACT III** — *Business Agents on AMD (Evolus)* track.
The reasoning model runs on an open model served on **AMD infrastructure**, and the process is
orchestrated with **Evolus**.

## How it works

1. A supplier invoice arrives (PDF or text).
2. **Evolus document extractor** turns it into structured JSON (vendor, PO, line items, totals, bank details).
3. The **AMD-hosted model** reasons over the extraction, the matching purchase order, and the
   company procurement policy (Evolus knowledge library) to perform a three-way match and tolerance check.
4. Clean matches are **auto-approved** and pushed to the accounting system through an **Evolus MCP connector**.
5. Exceptions are **escalated to a human** with an explanation and a suggested resolution, and the
   **Evolus chat widget** answers follow-up questions grounded in policy.

## AMD integration

The agent's decision-making runs on an open model (default **Gemma**, eligible for the Google prize)
served through our own **vLLM endpoint on AMD Developer Cloud** using the **ROCm** stack
(`AMD_BASE_URL`, `AMD_API_KEY`, `AMD_MODEL`).

## Evolus building blocks used

- **Workflows** — email/upload triggered pipeline
- **Document extractors** — PDF → structured JSON
- **AI Tools** — translation, redaction of bank data, summarisation
- **Knowledge library** — procurement policy (RAG) behind "ask about this decision"
- **MCP connector** — push approved invoices to the accounting system
- **Chat widget** — human review of exceptions

## Quickstart

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
streamlit run app.py
```

The app runs **offline by default** (heuristic fallback) so it demos without keys. Add your
`AMD_*` and `EVOLUS_*` values to `.env` to enable the live model and Evolus pipeline.

### Docker

```bash
docker build -t ledgerlens .
docker run -p 8501:8501 --env-file .env ledgerlens
```

## Demo script

| # | Action | Expected result |
|---|--------|-----------------|
| 1 | Reconcile `INV-1001.txt` (Northwind, PO-5001) | ✅ AUTO-APPROVE, pushed to ERP |
| 2 | Reconcile `INV-1002.txt` (Acme, price 3.50 vs 3.20) | ⛔ EXCEPTION — price + total mismatch |
| 3 | Reconcile `INV-1003.txt` (vendor "Northwind Trading Ltd") | ⛔ EXCEPTION — vendor mismatch |
| 4 | Reconcile `INV-1001.txt` again | ⛔ EXCEPTION — duplicate invoice |
| 5 | Ask *"why was this flagged?"* / *"what is the price tolerance?"* | Policy-grounded answer (clause 1–4) |

## Environment variables

See `.env.example`. Never commit `.env` — keys are read from the environment only.

## License

MIT
