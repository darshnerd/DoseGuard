SERVER := darsh@hackclub.app
REMOTE := /root/DoseGuard

.PHONY: build test ship-db deploy logs restart

build:
	cd packages/web && npm ci && npm run build

test:
	cd packages/api && uv run pytest -q

ship-db:
	scp packages/api/doseguard.db $(SERVER):$(REMOTE)/packages/api/doseguard.db

deploy:
	cd $(REMOTE) && git pull --ff-only
	~/.local/bin/uv --directory $(REMOTE)/packages/api sync
	cd $(REMOTE)/packages/web && npm ci && npm run build
	pm2 reload doseguard-api

logs:
	pm2 logs doseguard-api

restart:
	pm2 restart doseguard-api
