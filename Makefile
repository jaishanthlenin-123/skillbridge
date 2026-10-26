.PHONY: install test-backend test-ml test-frontend test lint run-backend run-ml run-frontend e2e clean

install:
	python -m venv .venv
	.venv/Scripts/pip install --upgrade pip
	.venv/Scripts/pip install -r backend/requirements.txt -r ml_service/requirements.txt
	cd frontend && npm install

test-backend:
	.venv/Scripts/pytest backend/tests/ -v

test-ml:
	.venv/Scripts/pytest ml_service/tests/ -v

test-frontend:
	cd frontend && npm run test

test: test-backend test-ml test-frontend

lint:
	cd frontend && npm run build

run-backend:
	.venv/Scripts/python backend/manage.py runserver 127.0.0.1:8000

run-ml:
	.venv/Scripts/uvicorn ml_service.app.main:app --port 8001 --reload

run-frontend:
	cd frontend && npm run dev

e2e:
	.venv/Scripts/python evaluation/run_evaluation.py
