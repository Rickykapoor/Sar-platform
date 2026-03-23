#!/bin/bash
set -e
echo "🚀 Starting SAR Platform services..."
docker compose up -d
echo "⏳ Waiting for services to be ready..."
sleep 30
echo "✅ All services started. Run ./infra/check_services.sh to verify."
