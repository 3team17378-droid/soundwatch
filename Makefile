.PHONY: setup backend frontend test docker
setup:
	python scripts/init_env.py
	python -m pip install -r backend/requirements.txt
	cd backend && alembic upgrade head
	cd frontend && pnpm install
backend:
	cd backend && uvicorn app.main:app --reload --no-access-log
frontend:
	cd frontend && pnpm dev
test:
	cd backend && pytest --cov=app && ruff check .
	cd frontend && pnpm test && pnpm typecheck && pnpm build
docker:
	docker compose up --build --wait
