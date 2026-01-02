#!/bin/bash

# Start Clash (Mihomo) in background
# We need a basic config for Clash to start API. 
# We can generate a minimal one or expect one at /app/config.yaml (application config) 
# BUT Clash needs its OWN config. 
# We'll generate a minimal config.yaml for Clash just to open the API port.

# Create config directory first
mkdir -p /root/.config/mihomo

cat <<EOF > /root/.config/mihomo/config.yaml
log-level: error
mode: global
mixed-port: 7890
external-controller: 0.0.0.0:9090
dns:
  enable: true
  listen: 0.0.0.0:53
  enhanced-mode: fake-ip
  nameserver:
    - 8.8.8.8
EOF

echo "Starting Mihomo..."
# Run clash in background
clash -d /root/.config/mihomo &

# Wait for API to be ready
echo "Waiting for Clash API..."
timeout 10 bash -c 'until curl -s http://127.0.0.1:9090/version > /dev/null; do sleep 1; done'
echo "Clash API is ready."

# Start FastAPI
echo "Starting Web Service..."
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
