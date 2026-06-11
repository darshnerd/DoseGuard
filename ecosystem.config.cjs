module.exports = {
  apps: [
    {
      name: "doseguard-api",
      cwd: "/root/DoseGuard/packages/api",
      script: "/root/.local/bin/uv",
      args: "run uvicorn app.main:app --host 127.0.0.1 --port 8000",
      interpreter: "none",
      env: { FLAGS_use_mkldnn: "0" },
    },
    {
      name: "caddy",
      script: "caddy",
      args: "run --config /root/DoseGuard/deploy/Caddyfile --adapter caddyfile",
      interpreter: "none",
    },
  ],
};
