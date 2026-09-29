# Task Management System

A production-ready asynchronous Task and Productivity Management API built with FastAPI, PostgreSQL, SQLAlchemy (async), Alembic, and JWT Authentication.

---

## Project Structure

```text
task-management-system/
├── backend/
│   ├── app/
│   │   ├── core/           # Database, security, and configuration
│   │   ├── models/         # SQLAlchemy models (User, Task, Category, Tag, Comment, Activity)
│   │   ├── repositories/   # Data access layer
│   │   ├── routes/         # FastAPI route handlers
│   │   ├── schemas/        # Pydantic request/response schemas
│   │   ├── services/       # Core business logic and validations
│   │   └── main.py         # Application entry point & lifespan
│   ├── tests/              # Pytest asynchronous integration test suite
│   ├── alembic/            # Database schema migrations
│   ├── alembic.ini         # Alembic configuration
│   ├── requirements.txt    # Python dependencies
│   ├── pytest.ini          # Pytest settings
│   └── .env.example        # Environment variable template
├── frontend/               # Frontend application placeholder
│   └── .gitkeep
├── .gitignore
└── README.md
```

---

## Getting Started (Backend)

All backend operations should be run from within the `backend/` directory.

### 1. Environment Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy the example environment file and configure your database and JWT secret credentials:

```bash
cp .env.example .env
```

### 3. Database Migrations

Apply database migrations up to the latest revision:

```bash
alembic upgrade head
```

To inspect migration status:

```bash
alembic current
```

### 4. Running the Development Server

Start the FastAPI application with auto-reload:

```bash
uvicorn app.main:app --reload
```

The interactive OpenAPI documentation will be accessible at:
* Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## Running Automated Tests

Run the complete test suite from inside the `backend/` directory:

```bash
pytest -v
```

---

## Frontend

The `frontend/` directory is reserved for future frontend development.
