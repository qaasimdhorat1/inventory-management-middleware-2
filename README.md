# Inventory Management System — Middleware

Django REST API backend for an enterprise-grade Inventory Management System. Provides JWT-authenticated endpoints for user management, inventory CRUD operations, stock tracking with audit logging, and dashboard analytics.

## Live Deployment

- **API:** [https://inventory-management-middleware-2.onrender.com](https://inventory-management-middleware-2.onrender.com)
- **Frontend:** [https://inventory-management-frontend-2-45qc.onrender.com](https://inventory-management-frontend-2-45qc.onrender.com)
- **Frontend Repository:** [https://github.com/qaasimdhorat1/inventory-management-frontend-2](https://github.com/qaasimdhorat1/inventory-management-frontend-2)

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Framework | Django 6.0 | Web framework |
| API | Django REST Framework | RESTful endpoint design |
| Authentication | SimpleJWT | JWT access + refresh token management |
| Database (Dev) | SQLite | Lightweight local development |
| Database (Prod) | PostgreSQL | Enterprise-grade persistent storage |
| Server | Gunicorn | Production WSGI HTTP server |
| Static Files | WhiteNoise | Efficient static file serving |
| CI/CD | GitHub Actions | Automated linting and testing |
| Deployment | Render | Cloud platform hosting |

## Architecture

This middleware follows a **three-layer enterprise architecture** with clear separation of concerns. The frontend communicates exclusively with this REST API layer. The database is accessed only through Django's ORM — never directly from the frontend.
```
┌─────────────────────────────────────────────────────┐
│                    Frontend (React)                  │
│         Communicates via REST API only               │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP/HTTPS (JSON)
                       ▼
┌─────────────────────────────────────────────────────┐
│               Middleware (This Repo)                 │
│                                                     │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │  accounts/   │  │  inventory/  │  │  config/   │ │
│  │  - Auth      │  │  - Items     │  │  - Settings│ │
│  │  - Profiles  │  │  - Categories│  │  - URLs    │ │
│  │  - JWT       │  │  - Stock Mgmt│  │  - WSGI   │ │
│  │             │  │  - Audit Log │  │            │ │
│  │             │  │  - Dashboard │  │            │ │
│  └─────────────┘  └──────────────┘  └────────────┘ │
└──────────────────────┬──────────────────────────────┘
                       │ Django ORM
                       ▼
┌─────────────────────────────────────────────────────┐
│            Database (PostgreSQL / SQLite)            │
└─────────────────────────────────────────────────────┘
```

### App Structure

- **config/** — Project-level settings, URL routing, and WSGI configuration. Environment-based configuration using `python-dotenv` for secure secret management.
- **accounts/** — User registration, JWT authentication (login, token refresh), profile retrieval and editing, and password changes with old password verification.
- **inventory/** — Category and inventory item CRUD, stock level management with audit logging, low-stock alerts, dashboard statistics, and search/filter/ordering capabilities.

## API Endpoints

### Authentication (`/api/auth/`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|:---:|
| POST | `/api/auth/register/` | Register a new user | No |
| POST | `/api/auth/login/` | Obtain JWT access and refresh tokens | No |
| POST | `/api/auth/token/refresh/` | Refresh an expired access token | No |
| GET | `/api/auth/profile/` | Retrieve authenticated user profile | Yes |
| PATCH | `/api/auth/profile/` | Update user profile fields | Yes |
| POST | `/api/auth/change-password/` | Change password with old password verification | Yes |

### Inventory (`/api/inventory/`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|:---:|
| GET | `/api/inventory/dashboard/` | Dashboard summary statistics | Yes |
| GET | `/api/inventory/categories/` | List user's categories | Yes |
| POST | `/api/inventory/categories/` | Create a category | Yes |
| GET/PUT/DELETE | `/api/inventory/categories/<id>/` | Retrieve, update, or delete a category | Yes |
| GET | `/api/inventory/items/` | List user's inventory items (search, filter, ordering) | Yes |
| POST | `/api/inventory/items/` | Create an inventory item | Yes |
| GET/PUT/DELETE | `/api/inventory/items/<id>/` | Retrieve, update, or delete an item | Yes |
| POST | `/api/inventory/items/<id>/stock/` | Update stock level with audit trail | Yes |
| GET | `/api/inventory/items/<id>/history/` | View stock change history for an item | Yes |
| GET | `/api/inventory/alerts/low-stock/` | List items at or below low stock threshold | Yes |

## Data Models

### User (Django built-in)
Uses Django's default User model with fields: `username`, `email`, `first_name`, `last_name`, `password`.

### Category
| Field | Type | Description |
|-------|------|-------------|
| name | CharField | Category name (unique per user) |
| description | TextField | Optional category description |
| user | ForeignKey | Owner (authenticated user) |
| created_at | DateTimeField | Auto-set on creation |

### InventoryItem
| Field | Type | Description |
|-------|------|-------------|
| name | CharField | Item name |
| sku | CharField | Unique stock-keeping unit (auto-generated) |
| description | TextField | Optional item description |
| category | ForeignKey | Associated category |
| quantity | IntegerField | Current stock level (validated ≥ 0) |
| unit_price | DecimalField | Price per unit |
| low_stock_threshold | IntegerField | Threshold for low-stock alerts |
| status | CharField | Auto-calculated: `in_stock`, `low_stock`, `out_of_stock` |
| user | ForeignKey | Owner (authenticated user) |
| created_at | DateTimeField | Auto-set on creation |
| updated_at | DateTimeField | Auto-updated on save |

### StockChange (Audit Log)
| Field | Type | Description |
|-------|------|-------------|
| item | ForeignKey | Related inventory item |
| change_type | CharField | `addition`, `removal`, or `adjustment` |
| quantity_changed | IntegerField | Amount changed |
| previous_quantity | IntegerField | Stock level before change |
| new_quantity | IntegerField | Stock level after change |
| reason | TextField | Reason for the stock change |
| changed_by | ForeignKey | User who made the change |
| created_at | DateTimeField | Auto-set on creation |

## Setup and Installation

### Prerequisites

- Python 3.12+
- pip

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/qaasimdhorat1/inventory-management-middleware-2.git
cd inventory-management-middleware-2
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate    # Linux/Mac
venv\Scripts\activate       # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root:
```
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

5. Run migrations and start the server:
```bash
python manage.py migrate
python manage.py runserver
```

The API will be available at `http://localhost:8000/api/`.

### Production Deployment (Render)

The application is deployed on Render with the following configuration:

- **Build Command:** `./build.sh` (installs dependencies, collects static files, runs migrations)
- **Start Command:** `gunicorn config.wsgi:application`
- **Database:** PostgreSQL (Render managed)

Environment variables configured on Render:

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string (set automatically by Render) |
| `SECRET_KEY` | Django secret key (randomly generated, never committed) |
| `DEBUG` | Set to `False` in production |
| `ALLOWED_HOSTS` | Render domain |
| `CORS_ALLOWED_ORIGINS` | Frontend deployment URL |
| `PYTHON_VERSION` | Python runtime version |

## Testing

The project includes **51 automated tests** covering authentication, inventory CRUD, stock management, and edge cases.

Run the full test suite:
```bash
python manage.py test
```

Run tests for a specific app:
```bash
python manage.py test accounts
python manage.py test inventory
```

### Test Coverage

**Accounts (18 tests):**
- User registration with valid and invalid data
- Login with correct and incorrect credentials
- JWT token refresh
- Profile retrieval and updates
- Password change with verification
- Unauthenticated access rejection

**Inventory (33 tests):**
- Category CRUD operations
- Inventory item CRUD operations
- Stock level updates (addition, removal, adjustment)
- Stock change audit log verification
- Low-stock alert endpoint
- Dashboard statistics accuracy
- Search, filtering, and ordering
- Validation (negative stock prevention, duplicate SKU handling)
- Cross-user data isolation (users cannot access other users' data)

## CI/CD

A GitHub Actions pipeline runs automatically on every push to `main`:

1. **Lint** — Runs `flake8` to enforce code quality and PEP 8 compliance
2. **Test** — Runs the full test suite of 51 tests against a clean database

The pipeline configuration is located at `.github/workflows/ci.yml`.

## Security

- **Authentication:** JWT with short-lived access tokens (30 minutes) and rotating refresh tokens (24 hours)
- **Password Storage:** Django's built-in PBKDF2 hashing algorithm with salt
- **Server-side Validation:** All input validated at the serializer and model level before database operations
- **Rate Throttling:** 20 requests/minute for anonymous users, 60 requests/minute for authenticated users
- **CORS:** Restricted to explicitly allowed frontend origins only
- **Data Isolation:** Users can only access their own data — enforced at the queryset level in every view
- **Production Security Headers:**
  - HSTS (HTTP Strict Transport Security) with 1-year max-age, subdomains, and preload
  - XSS protection filter enabled
  - Content-type sniffing prevention
  - Clickjacking protection via X-Frame-Options DENY
  - SSL redirect enforced
  - Secure session and CSRF cookies
- **Environment-based Configuration:** Secrets (SECRET_KEY, DATABASE_URL) managed via environment variables and never committed to version control

## Key Technical Decisions

| Decision | Rationale |
|----------|-----------|
| **Django's built-in User model** | Default fields (username, email, first/last name) meet all requirements without unnecessary complexity. Avoids migration issues from custom user models. |
| **SQLite (dev) / PostgreSQL (prod)** | Enables rapid local development while using an enterprise-grade database in production. `dj-database-url` handles seamless switching via the `DATABASE_URL` environment variable. |
| **Separate apps (accounts, inventory)** | Enforces separation of concerns and makes the codebase modular. Each app has its own models, serializers, views, URLs, and tests. |
| **Audit log via StockChange model** | Stock changes are tracked with full history (who, what, when, why) rather than simply overwriting quantity values. Supports enterprise compliance and traceability. |
| **Automatic status calculation** | Item status (`in_stock`, `low_stock`, `out_of_stock`) is computed on save based on quantity and threshold, eliminating manual status management errors. |
| **Token-based authentication (JWT)** | Stateless authentication suitable for a decoupled frontend/backend architecture. Refresh token rotation prevents token reuse attacks. |
| **Pagination and throttling** | Default pagination (10 items/page) and rate limiting ensure the API remains performant and resistant to abuse at scale. |

## Repository Migration

This repository (`inventory-management-middleware-2`) is a migrated copy of the original private repository (`inventory-management-system-middleware`). The migration was necessary due to GitHub account verification issues that prevented the original private repositories from being made public for submission. All commit history has been fully preserved using Git bundle files to transfer the complete history from the original repository to this public one.

## Use of AI

AI tools (Claude by Anthropic) were used as a development aid during this assignment. AI assisted with code scaffolding, debugging, writing tests, drafting documentation (including this README), and deployment configuration. All AI-generated code was reviewed, understood, and adapted to fit the project requirements. 
