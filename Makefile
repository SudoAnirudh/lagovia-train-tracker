.PHONY: check test-backend check-frontend dev-backend dev-frontend

check: test-backend check-frontend

test-backend:
	cd backend && venv/bin/pytest

check-frontend:
	cd frontend && npm run lint && npm run build

dev-backend:
	cd backend && venv/bin/uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev
