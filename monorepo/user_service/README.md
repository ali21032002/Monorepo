User Management Service
=======================

Endpoints
- POST `/auth/register` {username, email, full_name?, password, is_admin?}
- POST `/auth/login` (OAuth2PasswordRequestForm: username, password) → {access_token, token_type}
- GET `/users/me` (Bearer)
- GET `/users` (admin only)
- GET `/users/{id}` (owner or admin)
- PUT `/users/{id}` (owner or admin)
- DELETE `/users/{id}` (owner or admin)

Local run (PowerShell)
```
cd monorepo\user_service
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
setx USER_DB_URL "sqlite:///./users.db"
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8002
```


