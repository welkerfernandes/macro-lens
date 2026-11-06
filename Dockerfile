FROM rust:1.85-slim AS native
WORKDIR /native
COPY engines/trend .
RUN cargo build --release

FROM node:24-slim AS web
WORKDIR /web
COPY web/package*.json ./
RUN npm ci
COPY web .
RUN npm run build

FROM python:3.12-slim
WORKDIR /service
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --create-home service && chown service /service
COPY --chown=service:service app ./app
COPY --from=web --chown=service:service /app/frontend ./app/frontend
COPY --from=native /native/target/release/macro-trend /usr/local/bin/macro-trend
ENV NATIVE_ENGINE='["/usr/local/bin/macro-trend"]'
USER service
EXPOSE 8203
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8203"]
