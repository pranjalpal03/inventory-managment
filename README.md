# Smart Inventory Dashboard

Monorepo with a FastAPI backend and a Vite + React frontend.

## Local development

Prereqs: Python 3.11+, Node 18+, MongoDB (local or Atlas)

Backend

```bash
cd smart-inventory-dashboard/backend
python -m pip install -r requirements.txt
# start local dev server
py -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend

```bash
cd smart-inventory-dashboard/frontend
npm install
npm run dev
```

The frontend expects the API at `/api` by default. For separate hosting, set `VITE_API_BASE` to your backend URL.

## Build for production

Frontend

```bash
cd smart-inventory-dashboard/frontend
npm install
npm run build
# Output folder: dist
```

Backend

Use a production ASGI runner like `gunicorn` with the Uvicorn worker, or run `uvicorn` behind a process manager.

Example start command (Render / general):

```bash
# (Render) Start command
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Deploy

- Frontend: Vercel (link repo, set root to `smart-inventory-dashboard/frontend`, build `npm run build`, output `dist`).
- Backend: Render / Railway / Fly.io — connect the `smart-inventory-dashboard/backend` folder and set env vars.
- Database: MongoDB Atlas (set `MONGODB_URI`).

### Required environment variables (backend)

- `MONGODB_URI` — MongoDB connection string
- `MONGODB_DB_NAME` — database name
- `JWT_SECRET` — strong secret for JWTs
- `JWT_ALGORITHM` — usually `HS256`
- `JWT_EXPIRE_MINUTES`
- `DEMO_ADMIN_EMAIL`, `DEMO_ADMIN_PASSWORD`
- `CORS_ORIGINS` — include your Vercel domain (e.g. `https://your-site.vercel.app`)

## Suggested commit message

`docs: add README and .gitignore, prepare repo for deployment`
