# Example: FastAPI Blog API

This example demonstrates how to use CodeGenie to scaffold a complete FastAPI blog API from scratch.

## What You'll Build

A REST API with:
- User authentication (JWT)
- Blog post CRUD operations
- Comment system
- Like functionality
- PostgreSQL database
- Comprehensive tests
- API documentation

## Prerequisites

- CodeGenie installed
- Python 3.9+
- PostgreSQL (optional, will use SQLite for demo)

## Step-by-Step Guide

### Step 1: Start CodeGenie

```bash
# Create project directory
mkdir fastapi-blog
cd fastapi-blog

# Start CodeGenie
codegenie
```

### Step 2: Create the Project

```
You: Create a FastAPI blog API with user authentication, posts, comments, and likes. Use PostgreSQL for the database.

CodeGenie: I'll create a complete blog API for you.

📋 Execution Plan (15 steps):
1. Create project structure
2. Set up FastAPI application
3. Configure PostgreSQL database
4. Create User model with authentication
5. Implement JWT authentication
6. Create Post model
7. Create Comment model
8. Create Like model
9. Implement CRUD endpoints for posts
10. Implement comment endpoints
11. Implement like functionality
12. Add input validation
13. Add error handling
14. Create comprehensive tests
15. Generate API documentation

⏱️ Estimated time: 25 minutes

Proceed? (y/n): y

[CodeGenie executes the plan...]

✅ Project created successfully!
```

### Step 3: Review the Structure

```bash
tree -L 3
```

Expected structure:
```
fastapi-blog/
├── src/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── post.py
│   │   ├── comment.py
│   │   └── like.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── posts.py
│   │   ├── comments.py
│   │   └── likes.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── post.py
│   │   ├── comment.py
│   │   └── like.py
│   └── services/
│       ├── __init__.py
│       ├── auth.py
│       ├── post.py
│       ├── comment.py
│       └── like.py
├── tests/
│   ├── __init__.py
│   ├── test_auth.py
│   ├── test_posts.py
│   ├── test_comments.py
│   └── test_likes.py
├── alembic/
│   └── versions/
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

### Step 4: Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 5: Configure Database

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your database credentials
# For demo, SQLite is pre-configured
```

### Step 6: Run Migrations

```bash
# Create database tables
alembic upgrade head
```

### Step 7: Start the Server

```bash
uvicorn src.main:app --reload
```

### Step 8: Test the API

Visit http://localhost:8000/docs for interactive API documentation.

#### Register a User

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "johndoe",
    "password": "secretpassword"
  }'
```

#### Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "secretpassword"
  }'
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

#### Create a Post

```bash
TOKEN="your_access_token_here"

curl -X POST http://localhost:8000/posts \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "title": "My First Post",
    "content": "This is the content of my first blog post!"
  }'
```

#### Get All Posts

```bash
curl http://localhost:8000/posts
```

#### Add a Comment

```bash
curl -X POST http://localhost:8000/posts/1/comments \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "content": "Great post!"
  }'
```

#### Like a Post

```bash
curl -X POST http://localhost:8000/posts/1/like \
  -H "Authorization: Bearer $TOKEN"
```

### Step 9: Run Tests

```bash
pytest tests/ -v
```

Expected output:
```
tests/test_auth.py::test_register PASSED
tests/test_auth.py::test_login PASSED
tests/test_auth.py::test_get_current_user PASSED
tests/test_posts.py::test_create_post PASSED
tests/test_posts.py::test_get_posts PASSED
tests/test_posts.py::test_update_post PASSED
tests/test_posts.py::test_delete_post PASSED
tests/test_comments.py::test_create_comment PASSED
tests/test_comments.py::test_get_comments PASSED
tests/test_likes.py::test_like_post PASSED
tests/test_likes.py::test_unlike_post PASSED

======================== 11 passed in 2.34s ========================
```

## Key Features Demonstrated

### 1. Project Scaffolding
- Complete project structure
- Best practices for FastAPI
- Proper separation of concerns

### 2. Database Integration
- SQLAlchemy ORM
- Alembic migrations
- Relationship management

### 3. Authentication
- JWT token-based auth
- Password hashing with bcrypt
- Protected endpoints

### 4. Input Validation
- Pydantic schemas
- Request validation
- Response serialization

### 5. Error Handling
- Custom exceptions
- HTTP status codes
- Error responses

### 6. Testing
- Unit tests
- Integration tests
- Test fixtures

### 7. Documentation
- OpenAPI/Swagger docs
- Endpoint descriptions
- Request/response examples

## Extending the Example

Try these enhancements with CodeGenie:

```
You: Add pagination to the post listing endpoint

You: Add full-text search for posts

You: Implement email notifications for new comments

You: Add rate limiting to prevent spam

You: Create an admin panel for moderation
```

## Troubleshooting

### Database Connection Error

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Or use SQLite for development
# Edit .env: DATABASE_URL=sqlite:///./blog.db
```

### Import Errors

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Port Already in Use

```bash
# Use a different port
uvicorn src.main:app --reload --port 8001
```

## Next Steps

- Try the [React Todo App](../react_todo/) example
- Learn about [Refactoring](../../02_refactoring/) with CodeGenie
- Explore [Autonomous Development](../../04_autonomous/)

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [CodeGenie User Guide](../../../docs/USER_GUIDE.md)

