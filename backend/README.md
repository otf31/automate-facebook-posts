# Backend API - Automate Facebook Posts

FastAPI backend API for managing user subscriptions using JWT tokens. This service provides endpoints to register users, update subscriptions, and verify subscription status.

## Features

- 🔐 JWT (JSON Web Tokens) authentication
- 👤 User management with roles (super_admin, user)
- ⏱️ Subscription system with temporal expiration
- 🗄️ PostgreSQL database with SQLModel
- 🔄 Database migrations with Alembic
- 🚀 RESTful API with FastAPI
- 🏥 Health check endpoint

## Requirements

- Python >= 3.13
- PostgreSQL (version 12 or higher) or Podman with podman-compose
- [uv](https://github.com/astral-sh/uv) (package manager)

## Installation

1. Clone the repository and navigate to the backend directory:

```bash
cd backend
```

2. Install dependencies using `uv`:

```bash
uv sync
```

3. Create a `.env` file in the `backend` directory with the following variables:

```env
APP_NAME=autofbpost-api

ADMIN_EMAIL=admin@example.com
SUPER_ADMIN_ID=your_admin_id
SUPER_ADMIN_PASSWORD=your_admin_password

POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DBNAME=autofbpost
JWT_SECRET_KEY=your_very_secure_jwt_secret_key
JWT_ALGORITHM=HS256
ENV=development
```

4. Start the PostgreSQL database using Podman Compose:

```bash
podman compose up -d
```

This will start a PostgreSQL container with the database already created. The database will be available at `localhost:5432`.

5. Run Alembic migrations:

```bash
uv run alembic upgrade head
```

To stop the database container:

```bash
podman compose down
```

To stop and remove volumes (this will delete all data):

```bash
podman compose down -v
```

## Usage

### Development

To run the server in development mode:

```bash
uv run fastapi dev
```

The server will be available at `http://localhost:8000`

### Production

To run in production mode, make sure `ENV=production` in your `.env.prod` file:

```bash
uv run fastapi run
```

In production mode, the API documentation (Swagger/ReDoc) will be disabled for security.

## Endpoints

### `POST /register-update`

Register a new user or update an existing user's subscription.

**Authentication required:** Super Admin id and password

**Body:**
```json
{
  "super_admin_id": "super_admin_machine_id",
  "super_admin_password": "super_admin_password",
  "machine_id": "user_machine_id",
  "user_id": "user_id",
  "days": 0,
  "hours": 0,
  "minutes": 30,
  "comment": "Optional comment"
}
```

**Response:**
```json
{
  "id": "uuid",
  "machine_id": "user_machine_id",
  "user_id": "user_id",
  "jwt": "generated_jwt_token",
  "previous_jwt": "previous_token",
  "role": "user",
  "is_disabled": false,
  "comment": "Optional comment"
}
```

### `GET /check-subscription`

Check if a user has an active subscription.

**Query parameters:**
- `machine_id` (string): User's machine ID

**Success response:**
```
"user_machine_id"
```

**Possible errors:**
- `401 Unauthorized`: User not found, disabled, no subscription, subscription expired, or invalid credentials

### `GET /health`

Health check endpoint to verify the service status.

**Response:**
```json
{
  "status": "ok"
}
```

## Project Structure

```
backend/
├── alembic/              # Database migrations
│   ├── versions/         # Migration files
│   └── env.py           # Alembic configuration
├── alembic.ini          # Alembic configuration
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application and endpoints
│   ├── config.py        # Configuration and environment variables
│   ├── database.py      # Database configuration
│   ├── models.py        # SQLModel models
│   └── startup.py      # Startup functions (super admin creation)
├── podman-compose.yml   # Podman Compose configuration for development
├── pyproject.toml       # Project dependencies and configuration
└── README.md           # This file
```

## Data Models

### User

Main model representing a user in the system.

- `id`: Unique UUID of the user
- `machine_id`: Unique machine ID (indexed, unique)
- `user_id`: User ID
- `password`: User password (only used by super administrators)
- `jwt`: Current JWT token (optional)
- `previous_jwt`: Previous JWT token (optional)
- `role`: User role (`super_admin` or `user`)
- `is_disabled`: Indicates if the user is disabled
- `comment`: Optional comment

## Development

### Database Migrations

To create a new migration:

```bash
uv run alembic revision --autogenerate -m "migration description"
```

To apply migrations:

```bash
uv run alembic upgrade head
```

To revert the last migration:

```bash
uv run alembic downgrade -1
```

### Linting

The project uses `ruff` for linting. To run it:

```bash
uv run ruff check .
```

To format the code:

```bash
uv run ruff format .
```

## Security

- JWT tokens are generated with a configurable secret key
- In production mode, API documentation is disabled
- Only super administrators can register/update users
- Database connections in production require SSL

## Notes

- On application startup, a super admin user is automatically created if it doesn't exist
- JWT tokens include user information and have a configurable expiration date
- The system saves the previous JWT token when a subscription is updated

## Main Dependencies

- **FastAPI**: Modern and fast web framework
- **SQLModel**: ORM based on SQLAlchemy and Pydantic
- **Alembic**: Database migration tool
- **PyJWT**: JWT implementation in Python
- **psycopg2**: PostgreSQL adapter for Python
- **Pydantic Settings**: Configuration management from environment variables

## License

This project is part of the "Automate Facebook Posts" monorepo.
