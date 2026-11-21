# Portrait Studio — starter bundle

This bundle includes the two supplied portrait generators, a combined landing page, a FastAPI backend, and a basic admin page.

## Important status
The supplied generators are preserved as standalone HTML pages. The API and admin dashboard are included, but the generator pages are **not yet wired to automatically upload each completed portrait**. Before using this for real customers, add the upload call after each generator finishes rendering, and record the returned portrait ID so the download endpoint can increment the count. Do not deploy until that integration, consent wording, privacy notice, retention/deletion process, authentication, and HTTPS have been reviewed and tested.

## Local preview
1. Unzip this folder.
2. Open a terminal in `frontend` and run `python3 -m http.server 8001`.
3. Visit `http://127.0.0.1:8001`.

## Backend setup
1. Create a Supabase project and run `backend/supabase-schema.sql` in its SQL editor.
2. Create `backend/.env` from `.env.example` and fill in your project URL, service-role key, and a strong admin password. Never put the service-role key in frontend files or commit `.env`.
3. In a terminal: `cd backend`, `python3 -m venv .venv`, `source .venv/bin/activate`, `pip install -r requirements.txt`, then `uvicorn main:app --reload`.
4. Backend health check: `http://127.0.0.1:8000/api/health`.

## Admin preview
Run `python3 -m http.server 8002` from the `admin` folder and visit `http://127.0.0.1:8002`. The admin page uses browser Basic Authentication.

## Before production
Configure CORS for your deployed frontend/admin origins; deploy the API and static frontend; use HTTPS; protect admin access with stronger authentication/rate limiting; add customer photo upload and download tracking to both generators; publish a clear privacy notice and obtain affirmative consent; set retention/deletion rules. The storage bucket is private and admin image links are signed for one hour.
