# Budget Django

A **personal finance & shared-expense tracking API** built with Django REST Framework. Supports both individual budget tracking (transactions + categories) and group expense rooms where members can log, split, and settle shared costs.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | Django 4.2.30 |
| API | Django REST Framework 3.16.1 |
| Auth | Token-based (`rest_framework.authtoken`) |
| Database | SQLite (default, swappable) |
| CORS | `django-cors-headers` (pre-configured for `localhost:3000`) |

---

## Project Structure

```
budgetDjango/
├── manage.py                  # Django CLI entry-point
├── requirements.txt           # Python dependencies
├── db.sqlite3                 # SQLite database (local dev)
├── myproject/                 # Django project config
│   ├── settings.py            # Settings, installed apps, middleware, DB, REST config
│   ├── urls.py                # Root URL conf — routes /api/ → myapp.urls
│   ├── wsgi.py                # WSGI application (production deployment)
│   └── asgi.py                # ASGI application (async deployment)
└── myapp/                     # Main application
    ├── models.py              # Data models: Transaction, Category, Room, RoomMembership, RoomExpense, ExpenseShare
    ├── serializers.py         # DRF serializers with validation, user context, and custom logic
    ├── views.py               # API views: auth, CRUD, room management, expense splitting, balances
    ├── urls.py                # App-level URL routing (all /api/... endpoints)
    ├── admin.py               # Django admin registrations
    ├── apps.py                # App config
    └── migrations/            # Database migrations (7 migrations)
```

---

## Setup

### Prerequisites
- Python 3.10+
- pip

### Installation

```bash
# Clone the repo
git clone <repo-url> && cd budgetDjango

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Apply migrations
python manage.py migrate

# Create a superuser for Django admin
python manage.py createsuperuser

# Start the dev server
python manage.py runserver
```

The API will be available at `http://127.0.0.1:8000/api/`.

---

## Quick Start — Create a User & Get a Token

```bash
# 1. Create a new user (returns user data + auth token)
curl -X POST http://127.0.0.1:8000/api/register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "email": "alice@example.com", "password": "mypassword123"}'

# 2. OR login with an existing user (returns just the token)
curl -X POST http://127.0.0.1:8000/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "mypassword123"}'

# 3. Save the token from the response and use it for authenticated requests
TOKEN="paste-your-token-here"

# 4. Test the token by fetching user info
curl http://127.0.0.1:8000/api/user/ \
  -H "Authorization: Token $TOKEN"

# 5. Create a category
curl -X POST http://127.0.0.1:8000/api/insertCategory/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token $TOKEN" \
  -d '{"Name": "Groceries", "Description": "Food & supplies", "TransactionDate": "2025-01-01T00:00:00Z"}'

# 6. Create a transaction
curl -X POST http://127.0.0.1:8000/api/transactions/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token $TOKEN" \
  -d '{"CategoryID": 1, "Amount": 1500.00, "Description": "Weekly groceries", "TransactionDate": "2025-01-15T10:30:00Z", "TransactionType": "debit"}'
```

---

## Data Models

### Transaction
Individual expense/income entries linked to a user.

| Field | Type | Description |
|-------|------|-------------|
| `UserID` | FK → `auth.User` | Owner of the transaction |
| `Amount` | Float | Transaction amount |
| `CategoryID` | FK → `Category` | Category this transaction belongs to |
| `Description` | CharField (255) | Optional note |
| `TransactionDate` | DateTime | When the transaction occurred |
| `TransactionType` | CharField (50) | `"credit"` or `"debit"` |

### Category
User-defined categories for classifying transactions.

| Field | Type | Description |
|-------|------|-------------|
| `UserID` | FK → `auth.User` | Owner |
| `Name` | CharField (255) | Category name (e.g. "Groceries") |
| `Description` | CharField (255) | Optional description |
| `TransactionDate` | DateTime | When created |

### Room
A shared expense room with password-protected access.

| Field | Type | Description |
|-------|------|-------------|
| `name` | CharField (120) | Room display name |
| `room_code` | CharField (12) | Unique invite code (auto-generated 6-char uppercase alphanumeric) |
| `password_hash` | CharField (255) | BCrypt-style hashed password |
| `created_by` | FK → `auth.User` | Room creator |
| `members` | M2M → `auth.User` (through `RoomMembership`) | All members |
| `created_at` | DateTime (auto) | Creation timestamp |

### RoomMembership
Junction table linking users to rooms.

| Field | Type | Description |
|-------|------|-------------|
| `room` | FK → `Room` | The room |
| `user` | FK → `auth.User` | The member |
| `joined_at` | DateTime (auto) | When they joined |

**Constraint:** `unique_together = (room, user)` — a user can only join a room once.

### RoomExpense
An expense logged inside a room, paid by one member.

| Field | Type | Description |
|-------|------|-------------|
| `room` | FK → `Room` | Parent room |
| `paid_by` | FK → `auth.User` | Who paid |
| `amount` | Float | Total amount |
| `description` | CharField (255) | Optional label |
| `created_at` | DateTime (auto) | When logged |

### ExpenseShare
Each member's share of a single `RoomExpense`.

| Field | Type | Description |
|-------|------|-------------|
| `expense` | FK → `RoomExpense` | Parent expense |
| `user` | FK → `auth.User` | Who owes |
| `share_amount` | Float | Amount they owe |

**Constraint:** `unique_together = (expense, user)` — one share per user per expense.

---

## API Reference

Base URL: `http://127.0.0.1:8000/api/`

### Authentication

All protected endpoints require:
```
Authorization: Token <your-token>
```

Tokens are returned by `POST /api/register/` and `POST /api/login/`.

---

### Auth Endpoints

#### `POST /api/register/`
Create a new user account.

**Request:**
```json
{
  "username": "john",
  "email": "john@example.com",
  "password": "securepass123"
}
```

**Response** (201):
```json
{
  "user": { "id": 1, "username": "john", "email": "john@example.com" },
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
}
```

---

#### `POST /api/login/`
Authenticate and receive a token.

**Request:**
```json
{
  "username": "john",
  "password": "securepass123"
}
```

**Response** (200):
```json
{ "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b" }
```

---

#### `POST /api/logout/` 🔒
Delete the current auth token (effectively logging out).

**Response** (200):
```json
{ "detail": "Successfully logged out." }
```

---

#### `POST /api/change-password/` 🔒
Change the authenticated user's password.

**Request:**
```json
{
  "old_password": "oldpass123",
  "new_password": "newpass456"
}
```

**Response** (200):
```json
{ "detail": "Password updated successfully." }
```

---

### User Endpoints

#### `GET /api/user/` 🔒
Return the current authenticated user's info.

**Response** (200):
```json
{
  "username": "john",
  "email": "john@example.com"
}
```

---

### Transaction Endpoints

#### `GET /api/transactions/` 🔒
List all transactions for the authenticated user (includes nested category data).

**Response** (200):
```json
[
  {
    "id": 1,
    "CategoryID": { "id": 1, "UserID": 1, "Name": "Groceries", "Description": "...", "TransactionDate": "..." },
    "Amount": 1500.00,
    "Description": "Weekly groceries",
    "TransactionDate": "2025-01-15T10:30:00Z",
    "TransactionType": "debit",
    "UserID": 1
  }
]
```

---

#### `POST /api/transactions/` 🔒
Create a new transaction.

**Request:**
```json
{
  "CategoryID": 1,
  "Amount": 1500.00,
  "Description": "Weekly groceries",
  "TransactionDate": "2025-01-15T10:30:00Z",
  "TransactionType": "debit"
}
```

---

#### `PUT /api/update/` 🔒
Update a transaction. Provide the transaction `id` in the request body.

---

#### `DELETE /api/remove/<pk>/` 🔒
Delete a transaction by its primary key.

---

### Category Endpoints

#### `GET /api/categories/` 🔒
List all categories for the authenticated user.

---

#### `POST /api/insertCategory/` 🔒
Create a new category.

**Request:**
```json
{
  "Name": "Groceries",
  "Description": "Food & household items",
  "TransactionDate": "2025-01-01T00:00:00Z"
}
```

---

#### `PUT /api/updateCategory/` 🔒
Update a category (provide `id` in request body).

---

#### `DELETE /api/removeCategory/<pk>/` 🔒
Delete a category.

---

### Shared Expense Rooms

#### `POST /api/rooms/create/` 🔒
Create a new expense room. The creator is automatically added as a member.

**Request:**
```json
{
  "name": "Trip to Goa",
  "password": "goa2025"
}
```

Optional: `"room_code": "MYCUSTOM"` (defaults to auto-generated 6-char code).

**Response** (201):
```json
{
  "id": 1,
  "name": "Trip to Goa",
  "room_code": "A3K9XZ",
  "created_by_username": "john",
  "created_at": "2025-06-12T10:00:00Z",
  "member_count": 1,
  "members": [
    { "id": 1, "username": "john", "email": "john@example.com", "joined_at": "..." }
  ]
}
```

---

#### `POST /api/rooms/join/` 🔒
Join an existing room using its code and password.

**Request:**
```json
{
  "room_code": "A3K9XZ",
  "password": "goa2025"
}
```

**Response** (200):
```json
{ "id": 1, "name": "Trip to Goa", "room_code": "A3K9XZ", ..., "joined": true }
```

`"joined": false` means you were already a member.

---

#### `GET /api/rooms/` 🔒
List all rooms the authenticated user is a member of.

---

#### `GET /api/rooms/<code>/` 🔒
Get details for a specific room (must be a member).

---

#### `POST /api/rooms/<code>/leave/` 🔒
Leave a room. You must be a member.

---

#### `GET /api/rooms/<code>/info/` (public)
Public room info — no auth required. Useful for invite previews.

**Response:**
```json
{
  "name": "Trip to Goa",
  "room_code": "A3K9XZ",
  "member_count": 3,
  "created_by": "john"
}
```

---

#### `GET /api/rooms/<code>/check/` 🔒
Check if the current user is a member of the room.

**Response (200):**
```json
{
  "is_member": true,
  "name": "Trip to Goa",
  "room_code": "A3K9XZ"
}
```

---

#### `GET /api/rooms/<code>/expenses/` 🔒
List all expenses in a room, ordered by most recent first. Each expense includes the payer and per-user shares.

---

#### `POST /api/rooms/<code>/expenses/` 🔒
Add an expense. The amount is automatically split among members.

**Equal split (default — among all members):**
```json
{
  "amount": 3000,
  "description": "Dinner at beach shack"
}
```

**Custom split among specific members:**
```json
{
  "amount": 3000,
  "description": "Dinner",
  "split_among": [1, 2]
}
```

**Custom per-user shares (must sum to amount):**
```json
{
  "amount": 3000,
  "description": "Dinner",
  "shares": { "1": 2000, "2": 1000 }
}
```

**Specify a different payer (defaults to current user):**
```json
{
  "amount": 3000,
  "paid_by": 2,
  "description": "Dinner"
}
```

---

#### `DELETE /api/rooms/<code>/expenses/<id>/` 🔒
Delete an expense from a room.

---

#### `GET /api/rooms/<code>/balances/` 🔒
Get per-member balance summary.

**Response:**
```json
{
  "room_code": "A3K9XZ",
  "total_spent": 6000.00,
  "balances": [
    { "user_id": 1, "username": "john",  "paid": 3000.00, "owed": 2000.00, "net": 1000.00 },
    { "user_id": 2, "username": "jane",  "paid": 3000.00, "owed": 2000.00, "net": 1000.00 },
    { "user_id": 3, "username": "bob",   "paid": 0.00,    "owed": 2000.00, "net": -2000.00 }
  ]
}
```

- `paid` = total amount this user paid for the room
- `owed` = sum of this user's shares across all expenses
- `net` = `paid - owed` (positive means others owe them, negative means they owe others)

---

## Django Admin

Access the admin panel at `http://127.0.0.1:8000/admin/`.

Registered models: `Transaction`, `Category`, `Room`, `RoomMembership`, `RoomExpense`, `ExpenseShare`.

```bash
# Create a superuser if one doesn't exist
python manage.py createsuperuser

# Or reset an existing superuser's password
python manage.py changepassword <username>
```

---

## Frontend

This API is designed to work with a frontend (React) running on `http://localhost:3000`. CORS is pre-configured in `settings.py`.

---

## Development Notes

- **Print statements** in views serve as lightweight request logging during development.
- **Room codes** are 6-character uppercase alphanumeric generated via `secrets.choice`. They are unique and collision-resistant.
- **Expense rounding**: When splitting equally, the last member absorbs any cent-level rounding differences so totals always match exactly.
- All room endpoints that require membership return **403 Permission Denied** if the user is not a member (except public `/info/`).
