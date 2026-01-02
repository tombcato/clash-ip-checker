FROM python:3.10-slim-bookworm

WORKDIR /app
ENV PYTHONUNBUFFERED=1

# Install system dependencies
# Use Aliyun mirror to fix "Hash Sum mismatch" and connection issues
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's/security.debian.org\/debian-security/mirrors.aliyun.com\/debian-security/g' /etc/apt/sources.list.d/debian.sources && \
    apt-get update && \
    apt-get install -y \
    curl \
    gzip \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Mihomo (Clash Meta)
# Using a fixed release for stability. Adjust arch if needed (amd64 assumed)
RUN curl -L -o clash.gz https://github.com/MetaCubeX/mihomo/releases/download/v1.19.17/mihomo-linux-amd64-v1.19.17.gz && \
    gunzip clash.gz && \
    chmod +x clash && \
    mv clash /usr/local/bin/clash

# Verify installation
RUN clash -v

# Pre-download GeoIP and GeoSite databases to avoid runtime timeout
RUN mkdir -p /root/.config/mihomo && \
    curl -L -o /root/.config/mihomo/geoip.metadb https://github.com/MetaCubeX/meta-rules-dat/releases/download/latest/geoip.metadb && \
    curl -L -o /root/.config/mihomo/geosite.dat https://github.com/MetaCubeX/meta-rules-dat/releases/download/latest/geosite.dat && \
    curl -L -o /root/.config/mihomo/country.mmdb https://github.com/MetaCubeX/meta-rules-dat/releases/download/latest/country.mmdb

# Copy App
COPY . .

# Ensure entrypoint is executable
RUN sed -i 's/\r$//' entrypoint.sh && chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
