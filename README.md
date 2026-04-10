# STT Service (Django + Celery + gRPC + Docker)

Bu loyiha audio faylni qabul qilib, STT (Speech-To-Text) natijasini asinxron tarzda qaytaradi.  
Asosiy o'zgarish: oldingi HTTP chain o'rniga gRPC qatlam qo'shildi va servis Docker orqali to'liq ko'tariladigan qilindi.

## Arxitektura

Data flow:

1. Client audio faylni `POST /api/transcribe-from-url/` endpointiga yuboradi.
2. Django API Celery task yaratadi.
3. Celery worker gRPC client orqali `grpc-server:50051` ga so'rov yuboradi.
4. gRPC server audio byte'larni oladi va tashqi inference endpointga yuboradi.
5. Inference javobidagi `text` gRPC orqali workerga, worker orqali task result sifatida qaytadi.
6. Client `GET /api/task-status/?task_id=...` orqali holatni oladi.

## Nima uchun gRPC

- HTTP JSON/multipart qo'shimcha overheadini kamaytiradi.
- Binary payload (`bytes`) transporti aniq va tez.
- Service-to-service communication uchun low-latency.
- Thread pool bilan parallel ishlashni yaxshiroq boshqaradi.

## Benchmark (taqqoslash)

Quyidagi natijalar amaliy ishlash kuzatuvi sifatida kiritildi:

- Eski holat (1x1, 10 minut audio): ~10 minut.
- gRPC integratsiyadan keyin (shu 10 minut audio): ~9 soniya.

Izoh: natija infratuzilma, model backend, GPU holati va tarmoqga qarab farq qilishi mumkin. README'dagi bu raqamlar maqsadli taqqoslash uchun keltirilgan.

## Muhit o'zgaruvchilari (.env)

`/.env` faylni gitga kiritmang. Repo ichida faqat `/.env.example` saqlanadi.

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

## Local ishga tushirish (Docker)

1. `.env` yarating:

```bash
cp .env.example .env
```

2. Kerakli qiymatlarni to'ldiring (`DJANGO_SECRET_KEY`, `INFERENCE_HTTP_ENDPOINT`, `MODEL_TOKEN`).

3. Build va run:

```bash
docker compose up --build
```

Bu quyidagi containerlarni ko'taradi:

- `web` (Django API, `:8000`)
- `worker` (Celery worker)
- `grpc-server` (gRPC STT server, `:50051`)
- `redis` (broker)

## API endpointlar

- `POST /api/transcribe-from-url/`  
  Form-data: `file=<audio_file>`

- `GET /api/task-status/?task_id=<id>`  
  Task status va result olish uchun.

- `GET /api/all-tasks-status/`  
  Barcha tasklar holatini olish uchun.

## gRPC servis

Proto fayl: `proto/stt.proto`

Service:

- `stt.STTService/Transcribe`
  - Request: `bytes audio`, `string filename`
  - Response: `string text`

## Xavfsizlik bo'yicha tavsiya

- `DJANGO_SECRET_KEY`, `MODEL_TOKEN` va endpoint key/tokenlarni faqat `.env`da saqlang.
- Hech qachon `.env`ni commit qilmang.
- Productionda `DEBUG=False` bo'lishi shart.

## Tez tekshirish

Containerlar ishga tushgach:

```bash
docker compose ps
```

gRPC server health uchun log tekshirish:

```bash
docker compose logs -f grpc-server
```
