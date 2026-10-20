FROM node:24-bookworm-slim AS frontend
WORKDIR /build/frontend
RUN npm install -g pnpm@11.19.0
COPY frontend/package.json frontend/pnpm-lock.yaml frontend/pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile
COPY frontend/ ./
RUN pnpm build

FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.lock.txt /app/backend/requirements.lock.txt
RUN pip install --no-cache-dir -r backend/requirements.lock.txt
COPY backend/ /app/backend/
COPY --from=frontend /build/frontend/dist /app/frontend/dist
RUN useradd --uid 10001 --create-home appuser && mkdir -p /data /app/.cache && chown -R appuser:appuser /data /app/.cache
USER appuser
ENV DATABASE_PATH=/data/draftwise.sqlite3
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=3)" || exit 1
CMD ["python", "-m", "uvicorn", "app.main:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8000", "--no-proxy-headers"]
