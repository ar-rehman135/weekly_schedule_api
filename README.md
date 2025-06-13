# Weekly Schedule API

A simple **Django REST API** to manage a **weekly schedule** with time slots for each day of the week.

The API provides full **CRUD** functionality and is protected with **JWT authentication**.

Swagger UI is provided for easy testing.

---

## Features

* ✅ Create, Read, Update, Delete TimeSlots
* ✅ Group TimeSlots by day in the list API
* ✅ Validate:

  * No overlapping timeslots on same day
  * Timeslots cannot cross midnight
* ✅ JWT Authentication (access + refresh tokens)
* ✅ Swagger UI for API documentation and testing

---

## Tech Stack

* Django
* Django REST Framework
* SimpleJWT
* drf-yasg (Swagger UI)

---

## Installation

1️⃣ Clone the repo:

```bash
git clone <repo-url>
cd weekly_schedule_api
```

2️⃣ Setup virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows
```

3️⃣ Install dependencies:

```bash
pip install -r requirements.txt
```

4️⃣ Apply migrations:

```bash
python manage.py migrate
```

5️⃣ Create superuser (for admin panel):

```bash
python manage.py createsuperuser
```

6️⃣ Run the server:

```bash
python manage.py runserver
```

---

## API Documentation (Swagger UI)

Access via:

```http
http://localhost:8000/swagger/
```

---

## Authentication (JWT)

All API endpoints are protected with **JWT Authentication**.

### 1️⃣ Obtain token:

```http
POST http://localhost:8000/api/token/

Request Body:
{
    "username": "<your-username>",
    "password": "<your-password>"
}

Response:
{
    "access": "<access-token>",
    "refresh": "<refresh-token>"
}
```

---

### 2️⃣ Refresh token:

```http
POST http://localhost:8000/api/token/refresh/

Request Body:
{
    "refresh": "<refresh-token>"
}

Response:
{
    "access": "<new-access-token>"
}
```

---

### 3️⃣ Use token:

For all API requests (including `/api/timeslots/`), add header:

```http
Authorization: Bearer <access-token>
```

Example curl:

```bash
curl -X GET "http://localhost:8000/api/timeslots/" \
  -H "Authorization: Bearer <access-token>" \
  -H "accept: application/json"
```

---

## Endpoints

| Method | Endpoint               | Description                     |
| ------ | ---------------------- | ------------------------------- |
| GET    | `/api/timeslots/`      | List grouped timeslots (by day) |
| POST   | `/api/timeslots/`      | Create a new timeslot           |
| GET    | `/api/timeslots/{id}/` | Retrieve a timeslot             |
| PUT    | `/api/timeslots/{id}/` | Update a timeslot               |
| DELETE | `/api/timeslots/{id}/` | Delete a timeslot               |

---

## Running Tests

Run unit tests:

```bash
python manage.py test schedule
```


