# ensure you're on main and up-to-date
git checkout -B main
git pull origin main --rebase || true

# create an empty commit to trigger workflows (no code changes required)
git commit --allow-empty -m "ci: trigger deployment to Vercel + Render"

# push to GitHub
git push origin main