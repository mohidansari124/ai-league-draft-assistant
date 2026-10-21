#!/bin/bash
set -euo pipefail
cd /opt/draftwise
RELEASE=$1
DOMAIN=$(cat /srv/draftwise/domain)
docker build -t "draftwise:$RELEASE" .
docker network inspect draftwise >/dev/null 2>&1 || docker network create draftwise
# Import source observations idempotently before starting the application.
docker run --rm -v /srv/draftwise/database:/data "draftwise:$RELEASE" python backend/scripts/import_onetricks.py backend/app/data/onetricks_reviewed.json
# The named application container is the only service replaced on a release.
if docker container inspect app >/dev/null 2>&1; then docker stop app; docker rm app; fi
docker run -d --name app --network draftwise --restart unless-stopped --log-opt max-size=10m --log-opt max-file=3 \
  -e COOKIE_SECURE=true -e PUBLIC_TRAFFIC_LIMITS=true -e EXPLANATION_PROVIDER=template -e STATS_PROVIDER=opgg \
  -e "CORS_ORIGINS=https://$DOMAIN" -v /srv/draftwise/database:/data "draftwise:$RELEASE"
for attempt in $(seq 1 40); do
  docker exec app python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" && break || sleep 3
done
docker exec app python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"
if ! docker container inspect proxy >/dev/null 2>&1; then
  docker run -d --name proxy --network draftwise --restart unless-stopped --log-opt max-size=10m --log-opt max-file=3 \
    -p 80:80 -p 443:443 -e "DOMAIN=$DOMAIN" \
    -v /opt/draftwise/deploy/Caddyfile:/etc/caddy/Caddyfile:ro \
    -v /srv/draftwise/caddy:/data -v /srv/draftwise/caddy-config:/config caddy:2
fi
printf '%s\n' "$RELEASE" > /srv/draftwise/release
