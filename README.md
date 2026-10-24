# CareerTrust — local demo

A local, fictional public career-service demo for the IMPACTX 2026 Challenge 05. It combines a Flask API and SQLite persistence with a React/Vite interface. Scoring and risk analysis are deterministic and explainable. No external employer, job-board, or domain verification runs.

## Requirements

- Python 3.10+
- Node.js 20+
- Network access for the first package install (or locally cached dependencies)

## Start the backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

The API initializes `backend/instance/careertrust.db` and seeds a fictional candidate, 40 synthetic listings (six labeled scam/impersonation cases), and a five-task roadmap. API listens at `http://localhost:5000`.

## Start the frontend

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Use **Explore opportunities** from the home page. To clear local demo changes, open **More tools → Reset demo scenario** and confirm.

## Offline and mobile use

The installed web app caches its shell and the public company directory. If the service is unreachable, it opens a clearly labeled sample directory and keeps candidate profile edits on that device; those edits sync when the API is reachable again. Other offline actions are read-only. The directory rows shown without a service are fictional sample roles, not current vacancies. For a phone on the same Wi-Fi as a development laptop, set `VITE_API_BASE` to the laptop's reachable API URL and allow that origin in `CAREERTRUST_ALLOWED_ORIGINS`; a production deployment should serve the API and site through the same origin.

## Verify

```powershell
cd backend
python -m unittest -v test_app.py
```

The tests use an isolated in-memory SQLite database. The evaluation screen computes confusion-matrix metrics over the local synthetic labels. Fairness checks rerun the same matcher with controlled metadata variations. Neither represents real-world validation.

## Implemented flows

- Candidate profile retrieval/update and evidence ledger; adding evidence via `POST /api/evidence`.
- Job search, evidence-linked match explanations, save/unsave, detail view, automatic pause after 14 days without a listing update; stale roles are blocked from new applications.
- Skill roadmap task progress; completion does not grant mastery.
- Trust analysis for pasted text and demo listings with rule explanations, synthetic clone comparison, and private concern/correction/appeal notes.
- Persisted application tracking and status changes with duplicate-record prevention.
- Deterministic interview questions tied to actual role requirements and candidate evidence, with persisted practice notes.
- Truthful role-focused resume previews from profile facts, private-by-default contact omission, and explicit local consent/disclosure records.
- Computed controlled fairness checks and synthetic scam-evaluation metrics.
- Dashboard counts from persisted records; confirmed reset of local demo records.
- Photographic banyan hero with lightweight falling-leaf motion and a mobile responsive layout; PWA shell and limited cache of public listings and aggregate counts for low-connectivity use.
- Candidate profile fields for college, education, language, career direction, and skills. College and language preference are not used to score job matches. This is a local profile, not a sign-in or NCS account.
- Employer vacancy intake with alternate local-business evidence routes, a required no-fee pledge, email/website consistency signals, and organization checks. Submissions are stored as `Pending review` and never become searchable jobs automatically.
- Trust rules include placement, toolkit, onboarding, training, and deposit fee language. Listing dates are labeled as demo record dates, not employer confirmation.
- Home page maps the ten user-identified problems to the implemented workflows and clearly labels prototype limits. Source-linked public career notes rotate around the tree every five seconds; there are no paid promotions or chat interfaces.

## Scoring and limitations

Match score is `100 × earned requirement weights / total requirement weights`: mandatory requirements weigh 2, preferred requirements weigh 1. A profile proficiency from 0–3 contributes proportionally; demonstrated evidence adds up to 0.25 credit, capped at 1. Scores describe requirement coverage, not hiring probability. Trust rule points are transparent additive flags with caps, not probabilities or calibrated estimates. Demo company names and domains use fictional `.example` references. Domain checks compare local records only.

Resume PDF/DOCX parsing and editing, real employer-side sharing, live employer/domain checks, full duplicate-source lineage, and a reviewer adjudication console are not implemented. Employer submissions remain pending indefinitely in this demo; no vacancy is approved or published. Dates and job quality details are fictional, and no live employer reconfirmation occurs. Active records are automatically paused after 14 days without an update. Resume disclosure is a local simulation: consent is recorded, but no file is sent. Private Trust notes are stored locally and are not reviewed by a live moderator. The service worker caches the app shell and static assets. Only public job fields and aggregate dashboard counts are cached after a successful read; private profiles, applications, notes, and consent records stay out of browser cache. Writes require the local backend. Language preference does not translate all listing text. The interface uses a custom responsive beige-and-sage design rather than Tailwind/Framer Motion. Never enter real personal or sensitive data.


