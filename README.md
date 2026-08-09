
<img width="1832" height="845" alt="image" src="https://github.com/user-attachments/assets/cfeb1c79-bd72-486b-8af0-781cdb1f2793" />

```
User
 ↓
Register
 ↓
Login
 ↓
JWT
 ↓
Authorization Header
 ↓
get_current_user()
 ↓
current_user
 ↓
owner_id
 ↓
User-specific Tasks
```

On a new PC
# 1. Create a virtual environment
```python -m venv venv```

# 2. Activate it
```venv\Scripts\activate```

# 3. Install everything
```pip install -r requirements.txt```

# 4. Create your .env
```DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/task_manager```
```SECRET_KEY=your_secret_key_here```
```ALGORITHM=HS256```
```ACCESS_TOKEN_EXPIRE_MINUTES=30```

(Change the database URL and secret key to match your setup.)

# 5. Run the project
```uvicorn main:app --reload```
