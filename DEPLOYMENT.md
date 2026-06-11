# Deployment

Caddy serves the built SPA and proxies `/api` to the FastAPI backend (uvicorn).
Both run under PM2. The SQLite DB is copied up from local, not git.

This was set up on a fresh Ubuntu 25 LXC (root). A clean box doesn't have the
native libraries PaddleOCR and OpenCV need, so they're installed explicitly
below — skip them and the API crashes on startup with `libGL.so.1` or
`libgomp.so.1` import errors.

## Server setup (once)

Node and npm are already on the box. Install the rest:

```bash
# Python toolchain (uv manages its own Python; pin 3.12 — PaddlePaddle has no 3.13 wheels)
curl -LsSf https://astral.sh/uv/install.sh | sh
uv python install 3.12

# Native libs for OpenCV + PaddlePaddle (the part a fresh Ubuntu is missing)
apt update
apt install -y libgl1 libglib2.0-0 libgomp1 libsm6 libxext6 libxrender1

# PM2 (process manager) and Caddy (reverse proxy; see caddyserver.com/docs/install for the apt repo)
npm install -g pm2
apt install -y caddy
systemctl disable --now caddy   # PM2 runs Caddy itself, so free ports 80/443
```

## Deploy

```bash
git clone https://github.com/darshnerd/DoseGuard.git /root/DoseGuard
cd /root/DoseGuard

uv --directory packages/api sync
cd packages/web && npm ci && npm run build && cd ../..

cp packages/api/.env.example packages/api/.env
sed -i "s|change-me|$(openssl rand -hex 32)|" packages/api/.env

pm2 start ecosystem.config.cjs
pm2 startup && pm2 save
```

Ship the DB from local: `make ship-db`.

On the **first** start the API downloads the PP-OCRv5 OCR models (to
`~/.paddlex`), so it takes a minute or two before it serves — watch
`pm2 logs doseguard-api` for `Application startup complete`.

Verify: `pm2 list`, `pm2 logs doseguard-api`, `curl -s https://doseguard.dino.icu/api/health`.

## Troubleshooting

- **`ImportError: libGL.so.1` / `libgomp.so.1`** — a native lib is missing; run
  the `apt install` line above.
- **Scan crashes the worker** (`ConvertPirAttribute2RuntimeAttribute ... onednn`,
  or a 502 with no Python traceback) — PaddlePaddle is unstable on some CPUs.
  What works, and is already set: `enable_mkldnn=False` in the `PaddleOCR(...)`
  call plus `FLAGS_use_mkldnn=0` in the API's PM2 env (`ecosystem.config.cjs`),
  and the **mobile** OCR models (`PP-OCRv5_mobile_det/rec`). The **server** models
  segfault on this CPU even with mkldnn off, so don't switch back to them here.

## Notes

- IPv6-only — no public IPv4 on the box.
- DB is shipped from local and persists across deploys; `make ship-db` to refresh.
- Pushes to `main` auto-deploy via GitHub Actions. Set repo secrets
  `SSH_HOST`, `SSH_USER`, `SSH_PORT`, `SSH_PRIVATE_KEY`.
```
