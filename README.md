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

### Vercel configuration

If you deploy the frontend on Vercel and the backend on Render (or another host), set an environment variable in the Vercel project:

- Key: `VITE_API_BASE`
- Value: `https://your-backend.onrender.com` (replace with your backend URL)

Vercel environment variables are exposed to the client when their names are prefixed with `VITE_` and are available at runtime via `import.meta.env`. This project reads `VITE_API_BASE` and falls back to `/api` when not set, so same-origin hosting requires no change.

To add the variable on Vercel: Project → Settings → Environment Variables → Add New → set `VITE_API_BASE`. Redeploy after saving.

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

### Docker-based deployment (local test or as a containerized deploy)

I added production-ready `Dockerfile`s and a `docker-compose.yml` to the repository so you can run and test the whole stack locally or use the Docker images for cloud deployment.

Files added:
- `backend/Dockerfile` — runs the FastAPI app with Gunicorn + Uvicorn worker
- `frontend/Dockerfile` — builds the Vite app and serves it with nginx
- `docker-compose.yml` — runs `mongo`, `backend`, and `frontend` together for local testing

Local test commands (from repo root):

```bash
docker compose build
docker compose up
```

Then visit the frontend at `http://localhost:5173` and backend at `http://localhost:8000`.

### Deploying to Render using the backend Dockerfile

1. Go to Render dashboard → New → Web Service.
2. Connect your GitHub repo and select the `smart-inventory-dashboard` repository.
3. Select the `backend` folder as the deploy path and set Environment to `Docker` (Render will use the `backend/Dockerfile`).
4. Set Environment variables in the Render dashboard: `MONGODB_URI`, `MONGODB_DB_NAME`, `JWT_SECRET`, `CORS_ORIGINS`, etc.

The frontend can stay on Vercel; set `VITE_API_BASE` to the Render service URL.

If you'd like, I can also add a GitHub Actions workflow to automate deployment to Render and Vercel (requires adding API tokens as repo secrets).

## CI/CD: GitHub Actions (automatic deploy)

I added GitHub Actions workflows that will deploy on pushes to `main`:

- `.github/workflows/deploy-frontend.yml` — builds the frontend and deploys to Vercel using the `amondnet/vercel-action` action.
- `.github/workflows/deploy-backend.yml` — triggers a Render deployment via the Render API.

Required repository secrets (add these in GitHub → Settings → Secrets → Actions):

- `VERCEL_TOKEN` — your Vercel personal token
- `VERCEL_ORG_ID` — Vercel organization ID
- `VERCEL_PROJECT_ID` — Vercel project ID for the frontend
- `RENDER_API_KEY` — Render API key
- `RENDER_SERVICE_ID` — Render service ID (the backend service)

Notes:
- Vercel projects automatically deploy on GitHub pushes if you connect the repo in the Vercel dashboard; the workflow provided ensures the build step runs and uses the Vercel action to create a production deployment.
- The Render workflow uses the Render REST API to create a deployment for the specified service. Ensure your Render service is connected to this GitHub repo or configured to accept deploy requests.

After you add the secrets, push to `main` and the workflows will run automatically. You can monitor runs in the GitHub Actions tab of your repository.

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
