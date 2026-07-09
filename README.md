# FastAPI User Service

Simple FastAPI project with:

- **G1** — User CRUD stored in **AWS RDS** (PostgreSQL) + **JWT** authentication
- **G2** — Avatar upload stored in **AWS S3**
- **G3** — Interactive Swagger UI at `/docs`

## Project structure

```text
app/
  api/          # Auth, users, avatar routes
  core/         # Config, DB, JWT/password helpers
  models/       # SQLAlchemy models
  schemas/      # Pydantic request/response schemas
  services/     # Business logic + S3 upload
  main.py       # FastAPI entrypoint
```

## Setup

### 1. Create virtualenv and install deps

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your AWS RDS and S3 values:

| Variable | Description |
|---|---|
| `DATABASE_URL` | `postgresql://USER:PASSWORD@RDS_ENDPOINT:5432/DB_NAME` |
| `SECRET_KEY` | Long random string for JWT signing |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | IAM credentials with S3 put access |
| `AWS_REGION` | e.g. `ap-southeast-1` |
| `S3_BUCKET_NAME` | Bucket for avatars |

### 3. AWS prerequisites

**RDS**

- Create a PostgreSQL RDS instance
- Allow inbound `5432` from your IP / app security group
- Create a database (name used in `DATABASE_URL`)

**S3**

- Create a bucket for avatars
- IAM user/role needs `s3:PutObject` on that bucket
- Optional: make objects public-read or serve via CloudFront

### 4. Run the API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open Swagger: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## API overview

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/api/users` | No | Register user |
| `POST` | `/api/auth/login` | No | Login → JWT (`username` + `password` form) |
| `GET` | `/api/users` | JWT | List users |
| `GET` | `/api/users/me` | JWT | Current user |
| `GET` | `/api/users/{id}` | JWT | Get user |
| `POST` | `/api/users/me/avatar` | JWT | Upload avatar to S3 |

## Try in Swagger

1. `POST /api/users` — create a user
2. `POST /api/auth/login` — get `access_token` (use **Authorize** button, paste token)
3. Call protected CRUD endpoints
4. `POST /api/users/me/avatar` — upload an image file

## Docker Compose (recommended for local)

Runs the API + Postgres (RDS stand-in) + MinIO (S3 stand-in):

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| API / Swagger | http://localhost:8000/docs |
| Postgres | `localhost:5433` (`app` / `app` / db `users`) |
| MinIO API | http://localhost:9000 |
| MinIO Console | http://localhost:9001 (`minioadmin` / `minioadmin`) |

Stop and remove containers:

```bash
docker compose down
```

Remove data volumes too:

```bash
docker compose down -v
```

### Point at real AWS instead

Edit `docker-compose.yml` `api.environment` (or use an `.env` file) and set:

- `DATABASE_URL` → your RDS endpoint
- `AWS_*` / `S3_BUCKET_NAME` → real IAM + bucket
- Clear `S3_ENDPOINT_URL` and `S3_PUBLIC_ENDPOINT_URL` (empty = real AWS S3)

## Local DB alternative (optional)

If you want to develop without Docker/RDS, point `DATABASE_URL` at a local Postgres:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/users
```
