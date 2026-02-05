# Integration Guide (Models)

This repo uses a **service-layer integration** pattern. Please keep routes/UI/schema stable to avoid merge conflicts.

---

## Do NOT change (unless discussed)
- `shared/schemas.py` (API contracts)
- `backend/app/api/routes.py` (HTTP routes)
- `frontend/gradio_app.py` (UI wiring)

---

## Only change model logic here

### Paper module (Algo A)
File: `backend/app/services/paper_service.py`

Replace this function with real inference:
- `summarize_text(text: str, mode: str) -> Dict[str, Any]`

Must return:
- `request_id` (str)
- `one_liner` (str)
- `detailed` (str)
- `mermaid` (str)

Optional improvements (allowed here only):
- Add caching inside the service function if needed.
- Add timeouts / try-except fallbacks to avoid 500 during demos.

---

### Writing module (Algo B)
File: `backend/app/services/write_service.py`

Replace these functions with real logic:
- `profile_text(text: str, domain: str) -> Dict[str, Any]`
- `transfer_text(text: str, target_journal: str, formality: float, domain: str) -> Dict[str, Any]`

`profile_text` must return:
- `request_id` (str)
- `lexical` (dict)
- `structural` (dict)
- `diagnostics` (list of str)

`transfer_text` must return:
- `request_id` (str)
- `rewritten` (str)
- `suggestions` (list of str)

---

## Local verification (quick)
1) Activate venv
- macOS/Linux:
  - `source .venv/bin/activate`
- Windows PowerShell:
  - `.\.venv\Scripts\Activate.ps1`

2) Start backend
- `bash scripts/run_backend.sh`

3) Start frontend
- `bash scripts/run_frontend.sh`

4) Run smoke test
- `python scripts/smoke_test.py`

Expected output ends with:
- `OK ✅`

---

## Notes
- Keep responses aligned with `shared/schemas.py`.
- If you need new fields, update schema + routes + frontend together in ONE PR.
- Avoid committing large model weights or `.venv/`.