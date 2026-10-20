.PHONY: help backend frontend install-backend install-frontend dry-run build compose-up clean public-feed install-public public

help:
	@echo "TunaStarLink — Planet Hack"
	@echo ""
	@echo "  make install-backend   venv + pip"
	@echo "  make install-frontend  npm install"
	@echo "  make backend           FastAPI on :8010 (env from backend/.env.local)"
	@echo "  make frontend          Vite on :5174 → proxies /api to :8010"
	@echo "  make dry-run           one-shot generation with DRY_RUN=1"
	@echo "  make build             docker build"
	@echo "  make compose-up        docker compose up --build"
	@echo "  make public-feed       export art/ to the public television feed"
	@echo "  make install-public    npm install for public/"
	@echo "  make public            public television on :5175"

install-backend:
	cd backend && python3 -m venv .venv && . .venv/bin/activate && pip install -q -r requirements.txt

install-frontend:
	cd frontend && npm install --no-audit --no-fund

backend:
	@cd backend && \
	  if [ ! -d .venv ]; then python3 -m venv .venv; fi && \
	  . .venv/bin/activate && \
	  pip install -q -r requirements.txt && \
	  ART_STORAGE_PATH=$${ART_STORAGE_PATH:-../art} \
	  uvicorn main:app --reload --host 0.0.0.0 --port 8010

frontend:
	cd frontend && npm run dev

public-feed:
	@cd backend && \
	  if [ ! -d .venv ]; then python3 -m venv .venv && . .venv/bin/activate && pip install -q -r requirements.txt; else . .venv/bin/activate; fi && \
	  python ../scripts/export_public_feed.py

install-public:
	cd public && corepack enable && corepack prepare pnpm@9.15.9 --activate && pnpm install --frozen-lockfile

public:
	cd public && pnpm dev

dry-run:
	cd backend && \
	  if [ ! -d .venv ]; then python3 -m venv .venv; fi && \
	  . .venv/bin/activate && \
	  pip install -q -r requirements.txt && \
	  DRY_RUN=1 ART_STORAGE_PATH=../art python ../worker/run_once.py

build:
	docker build -t tuna-starlink-app:latest .

compose-up:
	docker compose up --build

clean:
	rm -rf backend/.venv frontend/node_modules frontend/dist backend/static
