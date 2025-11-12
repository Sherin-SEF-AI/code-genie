# Example: Extract Service Layer

This example demonstrates how to use CodeGenie to refactor a monolithic controller into a clean service layer architecture.

## Problem

You have a controller with business logic mixed in:

```python
# api/users.py (BEFORE)
@router.post("/users")
async def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    # Business logic in controller - BAD!
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = bcrypt.hashpw(user_data.password.encode(), bcrypt.gensalt())
    
    user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Send welcome email
    send_email(user.email, "Welcome!", "Thanks for joining!")
    
    # Log user creation
    logger.info(f"User created: {user.email}")
    
    return user
```

## Solution

Extract business logic into a service layer.

## Step-by-Step with CodeGenie

### Step 1: Analyze Current Code

```
You: Analyze the user controller and suggest improvements

CodeGenie: Analyzing api/users.py...

🔍 Issues Found:
1. Business logic in controller (lines 5-25)
2. Direct database access in controller
3. Multiple responsibilities (validation, hashing, email, logging)
4. Hard to test
5. Violates Single Responsibility Principle

💡 Recommendations:
1. Extract service layer
2. Use dependency injection
3. Separate concerns
4. Add proper error handling

Shall I refactor this code?
```

### Step 2: Request Refactoring

```
You: Yes, refactor to use a service layer with dependency injection

CodeGenie: I'll refactor to use a clean service layer architecture.

📋 Refactoring Plan:
1. Create UserService class
2. Move business logic to service
3. Update controller to use service
4. Add dependency injection
5. Update tests
6. Verify all tests pass

Executing...
```

### Step 3: Review Changes

```
CodeGenie: Refactoring complete!

📝 Changes Made:

✅ Created: services/user_service.py

class UserService:
    def __init__(self, db: Session, email_service: EmailService):
        self.db = db
        self.email_service = email_service
    
    async def create_user(self, user_data: UserCreate) -> User:
        # Check if user exists
        if await self.user_exists(user_data.email):
            raise UserAlreadyExistsError(user_data.email)
        
        # Hash password
        hashed_password = self._hash_password(user_data.password)
        
        # Create user
        user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        # Send welcome email
        await self.email_service.send_welcome_email(user)
        
        logger.info(f"User created: {user.email}")
        
        return user
    
    async def user_exists(self, email: str) -> bool:
        return self.db.query(User).filter(User.email == email).first() is not None
    
    def _hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

✅ Updated: api/users.py

@router.post("/users")
async def create_user(
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service)
):
    try:
        user = await user_service.create_user(user_data)
        return user
    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e))

✅ Created: dependencies.py

def get_user_service(
    db: Session = Depends(get_db),
    email_service: EmailService = Depends(get_email_service)
) -> UserService:
    return UserService(db, email_service)

✅ Updated: tests/test_users.py

def test_create_user():
    # Now easy to test with mocked dependencies
    mock_db = Mock()
    mock_email = Mock()
    service = UserService(mock_db, mock_email)
    
    user = await service.create_user(user_data)
    
    assert user.email == user_data.email
    mock_email.send_welcome_email.assert_called_once()

Running tests...
✅ All 15 tests passed

📊 Improvements:
- Separation of concerns ✅
- Testability improved ✅
- Dependency injection ✅
- Single responsibility ✅
- Easier to maintain ✅
```

## Benefits

### Before Refactoring
- ❌ Business logic in controller
- ❌ Hard to test
- ❌ Multiple responsibilities
- ❌ Tight coupling
- ❌ Difficult to reuse logic

### After Refactoring
- ✅ Clean separation of concerns
- ✅ Easy to test with mocks
- ✅ Single responsibility
- ✅ Loose coupling via DI
- ✅ Reusable service logic

## Running the Example

```bash
# Navigate to example directory
cd examples/02_refactoring/extract_service/

# View before code
cat before/api/users.py

# Start CodeGenie
codegenie

# Follow the refactoring steps
# (See transcript.md for full conversation)

# View after code
cat after/services/user_service.py
cat after/api/users.py

# Run tests
pytest tests/
```

## Key Takeaways

1. **Service Layer Pattern**: Separates business logic from controllers
2. **Dependency Injection**: Makes code testable and flexible
3. **Single Responsibility**: Each class has one clear purpose
4. **Testability**: Easy to mock dependencies in tests

## Next Steps

Try these related refactorings:

```
You: Extract a repository layer for database access

You: Add caching to the user service

You: Implement the command pattern for user operations

You: Add event sourcing for user changes
```

## Resources

- [Service Layer Pattern](https://martinfowler.com/eaaCatalog/serviceLayer.html)
- [Dependency Injection](https://en.wikipedia.org/wiki/Dependency_injection)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)

