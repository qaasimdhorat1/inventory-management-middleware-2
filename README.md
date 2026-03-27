# Inventory Management System — Middleware

Django REST API backend for an enterprise-grade Inventory Management System. Provides JWT-authenticated endpoints for user management, inventory CRUD operations, stock tracking with audit logging, and dashboard analytics.

## Technology Stack

- **Framework:** Django 6.0 with Django REST Framework
- **Authentication:** JWT via SimpleJWT (access + refresh tokens)
- **Database:** SQLite (development) / PostgreSQL (production)
- **Deployment:** Render with Gunicorn and WhiteNoise

## Architecture

This middleware follows a modular Django app structure with clear separation of concerns:

- **config/** — Project-level settings, URL routing, and WSGI configuration
- **accounts/** — User registration, authentication, profile management, and password changes
- **inventory/** — Category and inventory item CRUD, stock level management, audit logging, and dashboard statistics

The frontend communicates exclusively with this API layer. The database is accessed only through Django's ORM — never directly from the frontend.

## API Endpoints

### Authentication (`/api/auth/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register/` | Register a new user |
| POST | `/api/auth/login/` | Obtain JWT access and refresh tokens |
| POST | `/api/auth/token/refresh/` | Refresh an expired access token |
| GET | `/api/auth/profile/` | Retrieve authenticated user profile |
| PATCH | `/api/auth/profile/` | Update user profile |
| POST | `/api/auth/change-password/` | Change password with old password verification |

### Inventory (`/api/inventory/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/inventory/dashboard/` | Dashboard summary statistics |
| GET | `/api/inventory/categories/` | List user's categories |
| POST | `/api/inventory/categories/` | Create a category |
| GET/PUT/DELETE | `/api/inventory/categories/<id>/` | Retrieve, update, or delete a category |
| GET | `/api/inventory/items/` | List user's inventory items (supports search, filter, ordering) |
| POST | `/api/inventory/items/` | Create an inventory item |
| GET/PUT/DELETE | `/api/inventory/items/<id>/` | Retrieve, update, or delete an item |
| POST | `/api/inventory/items/<id>/stock/` | Update stock level with audit trail |
| GET | `/api/inventory/items/<id>/history/` | View stock change history |
| GET | `/api/inventory/alerts/low-stock/` | List items at or below low stock threshold |

## Setup and Installation

### Prerequisites

- Python 3.12+
- pip

### Local Development

1. Clone the repository:
```bash
   git clone https://github.com/qaasimdhorat1/inventory-management-system-middleware.git
   cd inventory-management-system-middleware
```

2. Create and activate a virtual environment:
```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
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

## Testing

The project includes 51 automated tests covering authentication, inventory CRUD, stock management, and edge cases.

Run the full test suite:
```bash
python manage.py test
```

Run tests for a specific app:
```bash
python manage.py test accounts
python manage.py test inventory
```

## CI/CD

A GitHub Actions pipeline runs automatically on every push to `main`:

1. **Lint** — Runs flake8 to enforce code quality and PEP 8 compliance
2. **Test** — Runs the full test suite against a clean database

## Security

- JWT authentication with short-lived access tokens (30 min) and rotating refresh tokens
- Password hashing via Django's built-in PBKDF2 algorithm
- Server-side validation on all endpoints
- Rate throttling (20 req/min anonymous, 60 req/min authenticated)
- CORS restricted to allowed frontend origins
- Production security headers: HSTS, XSS protection, content type sniffing prevention, clickjacking protection
- Environment-based configuration — secrets never committed to version control

## Key Technical Decisions

- **Django's built-in User model** was used rather than a custom user model, as the default fields (username, email, first/last name) meet all requirements without unnecessary complexity.
- **SQLite for development, PostgreSQL for production** — this allows rapid local development while using an enterprise-grade database in production.
- **Separate apps for accounts and inventory** — enforces separation of concerns and makes the codebase modular and maintainable.
- **Stock changes are tracked via an audit log** (StockChange model) rather than simply overwriting quantity values, providing a full history trail for enterprise compliance.
- **Automatic status calculation** — item status (in_stock, low_stock, out_of_stock) is computed automatically on save based on quantity and threshold, eliminating manual status management errors.