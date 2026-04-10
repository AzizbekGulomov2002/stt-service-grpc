# STT Service (Django + Celery + gRPC + Docker)

This project accepts audio files and returns **text transcriptions (STT)** asynchronously. The main change is an added **gRPC layer** between Celery and your inference backend, and a **Docker-compose** setup to run the full stack locally or on a server.

## Architecture

End-to-end flow:

1. The client uploads audio to `POST /api/transcribe-from-url/`.
2. The Django API enqueues a **Celery** task.
3. The Celery worker calls the **gRPC** server at `grpc-server:50051`.
4. The gRPC server receives raw audio bytes and forwards them to your **HTTP inference endpoint** (multipart upload).
5. The inference response’s `text` field is returned over gRPC to the worker and stored as the task result.
6. The client polls `GET /api/task-status/?task_id=...` for status and result.

## Why gRPC

- Less overhead than ad-hoc HTTP/JSON for internal service-to-service calls.
- Clear binary transport for audio (`bytes` in protobuf).
- Good fit for low-latency worker ↔ inference pipelines when combined with a robust backend.

## Performance comparison (observed)

These numbers were recorded as **operational observations** on a 10-minute mono audio sample:

| Setup | Approx. wall time |
|--------|-------------------|
| **Legacy path** (1×1, 10 min audio) | ~**10 minutes** |
| **After gRPC integration** (same 10 min audio) | ~**9 seconds** |

**Note:** Actual latency depends on hardware (CPU/GPU), model, batching, network, and how the inference service is deployed. Treat the table above as a **before/after comparison** for your stack, not a universal guarantee.

## Environment variables (`.env`)

Do **not** commit `.env`. Only `.env.example` is tracked in the repository.

Minimal `.env`:

```env
DJANGO_SECRET_KEY=replace_with_long_random_secret
DEBUG=False
ALLOWED_HOSTS=*

CELERY_BROKER_URL=redis://redis:6379/0

STT_GRPC_TARGET=grpc-server:50051
STT_GRPC_HOST=0.0.0.0
STT_GRPC_PORT=50051
STT_GRPC_WORKERS=8
STT_GRPC_TIMEOUT_SECONDS=600

INFERENCE_HTTP_ENDPOINT=https://your-inference-host/transcribe
MODEL_TOKEN=replace_with_real_model_token

CORS_ALLOWED_ORIGINS=http://localhost:8000
CSRF_TRUSTED_ORIGINS=http://localhost:8000
```

## Run with Docker

1. Create `.env`:

```bash
cp .env.example .env
```

2. Fill in required values (`DJANGO_SECRET_KEY`, `INFERENCE_HTTP_ENDPOINT`, `MODEL_TOKEN`, etc.).

3. Build and start:

```bash
docker compose up --build
```

Services:

- **web** — Django API on port `8000`
- **worker** — Celery worker
- **grpc-server** — gRPC STT service on port `50051`
- **redis** — Celery broker

## HTTP API

- **`POST /api/transcribe-from-url/`**  
  Multipart form field: `file=<audio_file>`

- **`GET /api/task-status/?task_id=<id>`**  
  Returns Celery state and result payload.

- **`GET /api/all-tasks-status/`**  
  Lists stored task results (from the results backend).

## gRPC service

Proto: `proto/stt.proto`

- **Service:** `stt.STTService`
- **RPC:** `Transcribe`
  - **Request:** `bytes audio`, `string filename`
  - **Response:** `string text`

## Security notes

- Keep `DJANGO_SECRET_KEY`, `MODEL_TOKEN`, and any API keys **only** in `.env` or a secrets manager.
- Never commit `.env`.
- Use `DEBUG=False` in production.

## Quick checks

List containers:

```bash
docker compose ps
```

Follow gRPC server logs:

```bash
docker compose logs -f grpc-server
```
