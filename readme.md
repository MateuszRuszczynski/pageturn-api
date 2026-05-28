# 📚 PageTurn API — Library Management Service

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.0+-green.svg)](https://www.djangoproject.com/)
[![Docker](https://img.shields.io/badge/Docker-Enabled-blue.svg)](https://www.docker.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7.4-red.svg)](https://redis.io/)
[![Celery](https://img.shields.io/badge/Celery-5.6-green.svg)](https://docs.celeryq.dev/)
[![Stripe](https://img.shields.io/badge/Stripe-Integrated-purple.svg)](https://stripe.com/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

PageTurn API is a modern, fully containerized RESTful web service built with Django REST Framework for managing a library platform. It automates key library workflows including book tracking, user profiles, borrowing management, and overdue fine generation with integrated real-time Stripe payments, asynchronous background tasks, and Telegram notifications.

---

## 🛠️ Tech Stack & Architecture

* **Backend:** Python 3.11 / Django / Django REST Framework (DRF)
* **Database:** PostgreSQL (production-ready relational storage)
* **Caching & Broker:** Redis
* **Asynchronous Tasks:** Celery + Celery Beat (handling daily overdue verification)
* **Notifications:** Telegram Bot API
* **Payment Gateway:** Stripe API Integration
* **Code Quality & Linting:** Ruff (strict PEP 8 compliance, fast linter, and formatter)
* **Documentation:** OpenAPI 3.0 / drf-spectacular / ReDoc & Swagger UI
* **Containerization:** Docker / Docker Compose

---

## 🚀 Key Features

* **Users & Authentication:** Custom user model using `email` as the primary identifier. Secure JWT-based authentication (Access/Refresh tokens) via SimpleJWT.
* **Books Management:** Full CRUD operations for library books with inventory tracking and role-based permissions (Admin-only management, read-only for public).
* **Borrowings System:** Dynamic checkout process. Validates current book availability, updates inventory atomically, and calculates exact expected return dates.
* **Stripe Payment Integration:** Automated Stripe checkout session generation for regular rentals and fine management. Includes a robust local verification workflow for payment success/cancellation.
* **Overdue Fine Engine:** Celery Beat runs an automated daily schedule checking for overdue borrowings. If a user breaches the deadline, the system automatically changes statuses and assesses a financial penalty (`FINE_MULTIPLIER = 2.0`).
* **Telegram Notifications:** Real-time messages sent directly to a specified Telegram channel/chat when a new borrowing is created or when a book return is successfully processed.

---

## 📦 API Documentation & Endpoints

The API includes comprehensive, production-grade technical English descriptors, request bodies, and custom schema schemas under unified tags.

Once the application is running, you can access the interactive documentation at:
* **Swagger UI:** `http://localhost:8000/api/doc/swagger/`
* **ReDoc:** `http://localhost:8000/api/doc/redoc/`

### Primary Endpoint Modules
* `/api/users/` — Registration, profiles, and JWT token pairs (`/token/`, `/token/refresh/`).
* `/api/books/` — Catalog browsability and administrative asset management.
* `/api/borrowings/` — Operational checkout registers and custom book return handling (`id/return/`).
* `/api/payments/` — Stripe ledger logging, transaction history, and webhook success/cancel routing.

---

## ⚙️ Quick Start & Installation

### Installation
```bash
# Clone the repository
git clone https://github.com/MateuszRuszczynski/pageturn-api.git

# Prepare environment variables, populate .env with the required data
cp .env_sample .env
```
### Build & Run
```bash
# Build docker container
docker-compose up --build

# Populate the datebase with sample data
docker compose exec web python manage.py loaddata initial_data.json

# Create an administrator account to access locked endpoints
docker compose exec web python manage.py createsuperuser
```
The API will be run at http://localhost:8000
