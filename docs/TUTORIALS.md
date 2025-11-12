# CodeGenie Tutorials

## Table of Contents
1. [Getting Started Tutorial](#getting-started-tutorial)
2. [Building a REST API](#building-a-rest-api)
3. [Autonomous Development Workflow](#autonomous-development-workflow)
4. [Multi-Agent Collaboration](#multi-agent-collaboration)
5. [Advanced Code Intelligence](#advanced-code-intelligence)
6. [Natural Language Programming](#natural-language-programming)

## Getting Started Tutorial

### Tutorial 1: Your First CodeGenie Project

**Duration:** 15 minutes  
**Level:** Beginner

#### Step 1: Initialize a New Project

```bash
mkdir my-first-project
cd my-first-project
codegenie init
```

CodeGenie will ask you some questions:

```
🧞 Welcome to CodeGenie!

What type of project are you building?
1. Web API
2. Web Application
3. CLI Tool
4. Library/Package
5. Data Science Project

Your choice: 1

Which framework would you like to use?
1. FastAPI (Python)
2. Express (Node.js)
3. Flask (Python)
4. Django (Python)

Your choice: 1

✅ Project initialized with FastAPI template
```

#### Step 2: Create Your First Endpoint

```
You: Create a hello world endpoint

CodeGenie: I'll create a simple hello world endpoint for you.

📝 Creating:
- src/main.py (FastAPI application)
- src/api/hello.py (Hello endpoint)
- tests/test_hello.py (Unit tests)

✅ Done! Your endpoint is ready at GET /hello
```

#### Step 3: Test the Endpoint

```
You: Run the tests

CodeGenie: Running tests...

✅ test_hello.py::test_hello_endpoint PASSED
✅ test_hello.py::test_hello_response_format PASSED

All tests passed! (2/2)
```

#### Step 4: Start the Server

```
You: Start the development server

CodeGenie: Starting FastAPI development server...

🚀 Server running at http://localhost:8000
📚 API docs at http://localhost:8000/docs

Press Ctrl+C to stop
```

#### Step 5: Add More Features

```
You: Add an endpoint that returns the current time

CodeGenie: I'll add a time endpoint.

✅ Created: src/api/time.py
✅ Updated: src/main.py (registered new route)
✅ Created: tests/test_time.py

Your new endpoint is ready at GET /time
```

**Congratulations!** You've created your first project with CodeGenie.

---

## Building a REST API

### Tutorial 2: Complete REST API with Authentication

**Duration:** 45 minutes  
**Level:** Intermediate

#### Overview

We'll build a complete REST API with:
- User authentication (JWT)
- CRUD operations for blog posts
- Database integration (PostgreSQL)
- Input validation
- Error handling
- Comprehensive tests

#### Step 1: Project Setup

```
You: Create a new FastAPI project with PostgreSQL database support

CodeGenie: Setting up FastAPI project with PostgreSQL...

✅ Created project structure
✅ Added SQLAlchemy ORM
✅ Configured PostgreSQL connection
✅ Set up Alembic for migrations
✅ Added environment configuration

Project structure:
├── src/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models/
│   ├── api/
│   └── services/
├── tests/
├── alembic/
└── requirements.txt
```

#### Step 2: Create User Model and Authentication

```
You: Create a User model with email, password, and username. Add JWT authentication.

CodeGenie: I'll create the user model and authentication system.

📋 Plan:
1. Create User model with password hashing
2. Implement JWT token generation and validation
3. Create registration endpoint
4. Create login endpoint
5. Add authentication middleware
6. Create tests

Executing...

✅ Created: src/models/user.py
   - User model with email, username, hashed_password
   - Password hashing using bcrypt
   - Email validation

✅ Created: src/services/auth.py
   - JWT token generation
   - Token validation
   - Password verification

✅ Created: src/api/auth.py
   - POST /auth/register
   - POST /auth/login
   - GET /auth/me (protected)

✅ Created: tests/test_auth.py
   - Registration tests
   - Login tests
   - Token validation tests

All tests passing! (12/12)
```

#### Step 3: Create Blog Post Model and CRUD

```
You: Create a BlogPost model with title, content, author, and timestamps. Add CRUD endpoints.

CodeGenie: Creating blog post system...

✅ Created: src/models/post.py
   - BlogPost model with relationships to User
   - Timestamps (created_at, updated_at)
   - Soft delete support

✅ Created: src/services/post.py
   - PostService with CRUD operations
   - Authorization checks
   - Pagination support

✅ Created: src/api/posts.py
   - GET /posts (list with pagination)
   - GET /posts/{id} (get single post)
   - POST /posts (create - requires auth)
   - PUT /posts/{id} (update - requires auth)
   - DELETE /posts/{id} (delete - requires auth)

✅ Created: tests/test_posts.py
   - CRUD operation tests
   - Authorization tests
   - Pagination tests

All tests passing! (18/18)
```

#### Step 4: Add Input Validation

```
You: Add comprehensive input validation using Pydantic

CodeGenie: Adding input validation...

✅ Created: src/schemas/user.py
   - UserCreate schema with email validation
   - UserResponse schema
   - UserUpdate schema

✅ Created: src/schemas/post.py
   - PostCreate schema (title: 1-200 chars, content: required)
   - PostResponse schema
   - PostUpdate schema
   - PostList schema with pagination

✅ Updated: All endpoints to use schemas
✅ Added: Custom validators for business rules

All tests passing! (24/24)
```

#### Step 5: Add Error Handling

```
You: Add comprehensive error handling with proper HTTP status codes

CodeGenie: Implementing error handling...

✅ Created: src/exceptions.py
   - Custom exception classes
   - Exception handlers
   - Error response schemas

✅ Updated: All endpoints with try-catch blocks
✅ Added: Logging for errors
✅ Created: tests/test_error_handling.py

Error handling covers:
- 400 Bad Request (validation errors)
- 401 Unauthorized (missing/invalid token)
- 403 Forbidden (insufficient permissions)
- 404 Not Found (resource not found)
- 409 Conflict (duplicate resources)
- 500 Internal Server Error (unexpected errors)

All tests passing! (32/32)
```

#### Step 6: Run and Test

```
You: Create a database migration and start the server

CodeGenie: Creating migration and starting server...

✅ Created migration: alembic/versions/001_initial.py
✅ Applied migration to database
✅ Starting server...

🚀 Server running at http://localhost:8000
📚 API Documentation: http://localhost:8000/docs

Try it out:
1. Register: POST /auth/register
2. Login: POST /auth/login
3. Create post: POST /posts (with token)
4. List posts: GET /posts
```

**Complete!** You now have a fully functional REST API with authentication.

---

## Autonomous Development Workflow

### Tutorial 3: Building a Feature Autonomously

**Duration:** 30 minutes  
**Level:** Advanced

#### Overview

Learn how to use CodeGenie's autonomous mode to build complex features with minimal supervision.

#### Step 1: Enable Autonomous Mode

```
You: /autonomous on

CodeGenie: Autonomous mode enabled.

In this mode, I'll:
- Break down complex tasks into steps
- Make implementation decisions automatically
- Execute multiple steps without asking
- Provide intervention points for review

You can interrupt at any time with Ctrl+C
```

#### Step 2: Define the Goal

```
You: Build a complete comment system for blog posts. Users should be able to comment on posts, reply to comments (nested), like comments, and edit/delete their own comments. Include moderation features for admins.

CodeGenie: Analyzing requirements...

📋 Autonomous Execution Plan (20 steps):

1. Design comment system architecture
2. Create Comment model with self-referential relationship
3. Create CommentLike model
4. Add database migrations
5. Implement CommentService with CRUD operations
6. Add nested comment support
7. Implement like/unlike functionality
8. Create comment API endpoints
9. Add authorization (users can only edit their comments)
10. Implement admin moderation endpoints
11. Add pagination for comments
12. Create comment schemas with validation
13. Implement soft delete for comments
14. Add comment count to posts
15. Create notification system for replies
16. Add rate limiting for comment creation
17. Implement spam detection
18. Create comprehensive tests
19. Add API documentation
20. Final integration and validation

⏱️ Estimated time: 35 minutes

[Intervention Point] Review plan? (y/n/modify): y

Starting execution in 3 seconds... (Press Ctrl+C to cancel)
```

#### Step 3: Monitor Execution

```
🔄 Step 1/20: Design comment system architecture
├─ ✅ Analyzed existing post system
├─ ✅ Designed comment model structure
├─ ✅ Planned API endpoints
└─ ✅ Defined authorization rules

💡 Decision: Using self-referential foreign key for nested comments
💡 Decision: Separate table for likes (scalability)

🔄 Step 2/20: Create Comment model
├─ ✅ Created src/models/comment.py
├─ ✅ Added relationships to User and Post
├─ ✅ Implemented parent_id for nesting
└─ ✅ Added timestamps and soft delete

🔄 Step 3/20: Create CommentLike model
├─ ✅ Created src/models/comment_like.py
├─ ✅ Added unique constraint (user_id, comment_id)
└─ ✅ Added cascade delete rules

[Intervention Point] Steps 1-3 complete. Continue? (y/n): y

🔄 Step 4/20: Add database migrations
...
```

#### Step 4: Intervention Point

```
🔄 Step 10/20: Implement admin moderation endpoints

⚠️ Decision Required:

I'm about to implement admin moderation with these actions:
1. Delete any comment
2. Hide/unhide comments
3. Ban users from commenting
4. View flagged comments

Should I also add:
A. Bulk moderation actions
B. Moderation logs/audit trail
C. Auto-moderation rules
D. All of the above
E. None (keep it simple)

Your choice: D

💡 Adding all advanced moderation features...
```

#### Step 5: Completion

```
✅ Step 20/20: Final integration and validation

🎉 Autonomous execution complete!

📊 Summary:
- Files created: 12
- Files modified: 8
- Tests created: 45
- All tests passing: ✅
- API endpoints added: 15
- Database migrations: 3

🔍 What was built:
✅ Complete comment system with nesting
✅ Like/unlike functionality
✅ User authorization
✅ Admin moderation panel
✅ Bulk moderation actions
✅ Audit logging
✅ Auto-moderation (spam detection)
✅ Rate limiting
✅ Notification system
✅ Comprehensive tests
✅ API documentation

⏱️ Actual time: 32 minutes

Would you like me to:
1. Start the server and demo the features
2. Show you the code
3. Run the tests
4. Generate documentation
```

**Amazing!** CodeGenie built a complete feature autonomously.

---

## Multi-Agent Collaboration

### Tutorial 4: Using Specialized Agents

**Duration:** 25 minutes  
**Level:** Intermediate

#### Overview

Learn how to leverage specialized agents for different aspects of development.

#### Step 1: Architecture Design

```
You: @architect Design a microservices architecture for an e-commerce platform

Architect Agent: Analyzing e-commerce requirements...

🏗️ Microservices Architecture Design

Services:
1. **User Service**
   - Authentication & authorization
   - User profiles
   - Tech: Python/FastAPI, PostgreSQL

2. **Product Service**
   - Product catalog
   - Inventory management
   - Tech: Python/FastAPI, PostgreSQL + Redis

3. **Order Service**
   - Order processing
   - Order history
   - Tech: Python/FastAPI, PostgreSQL

4. **Payment Service**
   - Payment processing
   - Transaction history
   - Tech: Python/FastAPI, PostgreSQL

5. **Notification Service**
   - Email/SMS notifications
   - Tech: Python/Celery, RabbitMQ

Communication:
- Synchronous: REST APIs via API Gateway
- Asynchronous: Event-driven with RabbitMQ
- Service discovery: Consul

Data:
- Database per service pattern
- Event sourcing for orders
- CQRS for product catalog

Infrastructure:
- Containerization: Docker
- Orchestration: Kubernetes
- API Gateway: Kong
- Monitoring: Prometheus + Grafana

Shall I create the service scaffolding?
```

#### Step 2: Security Review

```
You: @security Review the authentication implementation in src/services/auth.py

Security Agent: Performing security analysis...

🔍 Security Analysis Results

✅ Strengths:
1. Using bcrypt for password hashing (good)
2. JWT tokens with expiration
3. HTTPS enforced
4. Input validation present

🔴 Critical Issues:
1. **JWT Secret in Code** (Line 12)
   Risk: Secret key exposure
   Fix: Move to environment variable
   
2. **No Rate Limiting on Login** (Line 45)
   Risk: Brute force attacks
   Fix: Add rate limiting (5 attempts per minute)

🟡 Warnings:
1. **Short Token Expiration** (15 minutes)
   Recommendation: Add refresh token mechanism
   
2. **No Account Lockout**
   Recommendation: Lock account after 5 failed attempts

3. **Missing CSRF Protection**
   Recommendation: Add CSRF tokens for state-changing operations

Shall I implement these fixes automatically?
```

#### Step 3: Performance Optimization

```
You: @performance Analyze and optimize the product search endpoint

Performance Agent: Analyzing performance...

⚡ Performance Analysis

Current Performance:
- Average response time: 2.3s
- 95th percentile: 4.1s
- Throughput: 43 req/s

🔍 Bottlenecks Found:

1. **N+1 Query Problem** (Severity: High)
   Location: src/services/product.py:67
   Issue: Loading categories in loop
   Impact: 500ms per request
   Fix: Use JOIN or eager loading
   Expected improvement: 80% faster

2. **Missing Database Index** (Severity: High)
   Table: products
   Column: name (used in search)
   Impact: Full table scan on search
   Fix: Add GIN index for full-text search
   Expected improvement: 90% faster

3. **No Caching** (Severity: Medium)
   Issue: Repeated queries for same data
   Fix: Add Redis caching (TTL: 5 minutes)
   Expected improvement: 95% faster for cached results

4. **Inefficient Pagination** (Severity: Low)
   Issue: Using OFFSET (slow for large offsets)
   Fix: Cursor-based pagination
   Expected improvement: Consistent performance

📊 Projected Performance After Optimization:
- Average response time: 120ms (95% improvement)
- 95th percentile: 250ms (94% improvement)
- Throughput: 850 req/s (1900% improvement)

Shall I implement these optimizations?
```

#### Step 4: Coordinated Development

```
You: Build a payment processing feature with all best practices

CodeGenie: This requires multiple agents. Coordinating...

👥 Agent Coordination Plan:

1. @architect - Design payment system architecture
2. @developer - Implement core payment logic
3. @security - Add security measures and PCI compliance
4. @performance - Optimize for high throughput
5. @tester - Create comprehensive test suite
6. @documentation - Generate documentation

Starting coordinated execution...

---

[@architect] Designing payment system...
✅ Designed: Payment gateway integration pattern
✅ Designed: Transaction state machine
✅ Designed: Idempotency handling

[@developer] Implementing payment logic...
✅ Created: Payment model and service
✅ Implemented: Stripe integration
✅ Added: Webhook handling
✅ Implemented: Refund logic

[@security] Adding security measures...
✅ Implemented: PCI DSS compliance checks
✅ Added: Encryption for sensitive data
✅ Implemented: Fraud detection
✅ Added: Audit logging

[@performance] Optimizing...
✅ Added: Connection pooling
✅ Implemented: Async payment processing
✅ Added: Caching for payment methods
✅ Optimized: Database queries

[@tester] Creating tests...
✅ Created: Unit tests (25 tests)
✅ Created: Integration tests (15 tests)
✅ Created: End-to-end tests (8 tests)
✅ All tests passing!

[@documentation] Generating documentation...
✅ Created: API documentation
✅ Created: Integration guide
✅ Created: Security documentation
✅ Created: Troubleshooting guide

---

🎉 Payment processing feature complete!

All agents collaborated successfully.
Total time: 18 minutes
```

**Excellent!** Multiple agents worked together seamlessly.

---

## Advanced Code Intelligence

### Tutorial 5: Using Code Intelligence Features

**Duration:** 20 minutes  
**Level:** Advanced

#### Step 1: Codebase Analysis

```
You: Analyze my entire codebase and provide insights

CodeGenie: Analyzing codebase...

📊 Codebase Analysis Report

**Project Overview:**
- Language: Python
- Framework: FastAPI
- Total files: 87
- Total lines: 12,453
- Test coverage: 78%

**Architecture Patterns:**
✅ Repository pattern (consistent)
✅ Dependency injection (consistent)
✅ Service layer (consistent)
⚠️ Mixed: Some controllers have business logic

**Code Quality:**
- Complexity: Medium (avg cyclomatic complexity: 4.2)
- Maintainability index: 72/100 (Good)
- Technical debt: 8.5 hours

**Dependencies:**
- Total: 45 packages
- Outdated: 7 packages
- Security vulnerabilities: 2 (medium severity)

**Recommendations:**
1. Update vulnerable packages (requests, pillow)
2. Move business logic from controllers to services
3. Increase test coverage to 85%
4. Refactor 3 high-complexity functions
5. Add missing docstrings (23 functions)

Would you like me to address any of these?
```

#### Step 2: Impact Analysis

```
You: I want to change the User model to add a 'role' field. What will be affected?

CodeGenie: Analyzing impact...

🔍 Change Impact Analysis

**Proposed Change:**
Add 'role' field to User model (src/models/user.py)

**Direct Impact (5 files):**
1. src/models/user.py
   - Add role field
   - Add role enum
   - Update __init__ method

2. src/services/auth.py
   - Update registration to include role
   - Add role-based authorization

3. src/api/auth.py
   - Update registration endpoint
   - Add role to response schema

4. src/schemas/user.py
   - Add role to UserCreate schema
   - Add role to UserResponse schema

5. alembic/versions/
   - Create new migration

**Indirect Impact (12 files):**
- All endpoints using @require_auth decorator
- Authorization middleware
- User-related tests
- API documentation

**Risk Assessment:** Medium
- Breaking change: Yes (API schema changes)
- Database migration: Required
- Test updates: Required (estimated 15 tests)

**Recommendations:**
1. Create database migration first
2. Update schemas before endpoints
3. Add backward compatibility for existing users
4. Update all tests
5. Version the API (v2) for breaking changes

**Estimated effort:** 2-3 hours

Shall I implement this change with all necessary updates?
```

#### Step 3: Pattern Recognition

```
You: Find all instances of the repository pattern in my code

CodeGenie: Searching for repository pattern...

🔍 Repository Pattern Instances Found: 8

1. **UserRepository** (src/repositories/user.py)
   ✅ Implements: get, create, update, delete
   ✅ Uses: SQLAlchemy session
   ✅ Returns: Domain models
   
2. **PostRepository** (src/repositories/post.py)
   ✅ Implements: get, create, update, delete, list
   ✅ Uses: SQLAlchemy session
   ⚠️ Issue: Business logic in repository (line 45)
   
3. **CommentRepository** (src/repositories/comment.py)
   ✅ Implements: get, create, update, delete
   ⚠️ Issue: Missing list method
   ⚠️ Issue: Direct database access (should use session)

... (5 more repositories)

**Pattern Consistency:** 75%

**Issues Found:**
1. Inconsistent method naming (get_by_id vs find_by_id)
2. Some repositories have business logic
3. Missing base repository class
4. Inconsistent error handling

**Recommendations:**
1. Create BaseRepository class
2. Standardize method names
3. Move business logic to services
4. Add consistent error handling

Shall I refactor to improve consistency?
```

#### Step 4: Code Smell Detection

```
You: Find code smells and suggest improvements

CodeGenie: Analyzing code quality...

🔍 Code Smells Detected: 15

**High Priority (3):**

1. **God Class** (src/services/user_service.py)
   Lines: 450
   Methods: 28
   Issue: Too many responsibilities
   Suggestion: Split into UserService, UserProfileService, UserPreferenceService
   
2. **Long Method** (src/api/posts.py:create_post)
   Lines: 85
   Complexity: 12
   Issue: Does too much
   Suggestion: Extract validation, authorization, and notification logic
   
3. **Duplicate Code** (Found in 4 files)
   Pattern: Error handling code repeated
   Suggestion: Create error handling decorator

**Medium Priority (7):**

4. **Magic Numbers** (src/services/auth.py)
   Lines: 23, 45, 67
   Issue: Hardcoded values (15, 3600, 7)
   Suggestion: Use named constants

5. **Long Parameter List** (src/services/post_service.py:create_post)
   Parameters: 8
   Suggestion: Use parameter object or builder pattern

... (5 more)

**Low Priority (5):**
- Missing docstrings
- Inconsistent naming
- Unused imports

Would you like me to fix these automatically?
```

**Powerful!** Code intelligence provides deep insights.

---

## Natural Language Programming

### Tutorial 6: Building with Natural Language

**Duration:** 30 minutes  
**Level:** Beginner to Intermediate

#### Step 1: Describe Your Feature

```
You: I need a feature where users can create wishlists, add products to wishlists, share wishlists with other users, and get notifications when wishlist items go on sale.

CodeGenie: Let me understand your requirements...

📝 Requirements Analysis:

**Core Features:**
1. Users create wishlists (multiple per user)
2. Add/remove products to/from wishlists
3. Share wishlists with other users
4. Notifications for price drops

**Clarification Questions:**

1. Should wishlists be public, private, or both?
2. Can users collaborate on shared wishlists (both add items)?
3. What triggers a "sale" notification? (% discount, price threshold)
4. Should there be a limit on wishlists per user?
5. Can users comment on wishlist items?

Please answer these questions...
```

#### Step 2: Refine Requirements

```
You: 
1. Both public and private
2. Yes, collaborative wishlists
3. 10% or more discount
4. No limit
5. Yes, comments would be nice

CodeGenie: Perfect! Let me create a detailed plan...

📋 Implementation Plan:

**Database Models:**
1. Wishlist (name, description, is_public, owner_id)
2. WishlistItem (wishlist_id, product_id, added_by, notes)
3. WishlistShare (wishlist_id, user_id, permission)
4. WishlistComment (wishlist_item_id, user_id, comment)
5. PriceAlert (product_id, user_id, threshold_percentage)

**API Endpoints:**
- POST /wishlists (create)
- GET /wishlists (list user's wishlists)
- GET /wishlists/{id} (get wishlist)
- PUT /wishlists/{id} (update)
- DELETE /wishlists/{id} (delete)
- POST /wishlists/{id}/items (add item)
- DELETE /wishlists/{id}/items/{item_id} (remove item)
- POST /wishlists/{id}/share (share with user)
- GET /wishlists/shared (get shared wishlists)
- POST /wishlists/items/{id}/comments (add comment)
- GET /wishlists/items/{id}/comments (get comments)

**Background Jobs:**
- Price monitoring (check every hour)
- Send notifications for price drops

**Notifications:**
- Email notification
- In-app notification

Does this match your vision? (y/n/modify):
```

#### Step 3: Iterative Development

```
You: Yes, build it!

CodeGenie: Building wishlist feature...

✅ Created database models
✅ Created migrations
✅ Implemented wishlist service
✅ Created API endpoints
✅ Added authorization
✅ Implemented sharing logic
✅ Created notification system
✅ Added background job for price monitoring
✅ Created tests

🎉 Wishlist feature complete!

Try it out:
1. Create wishlist: POST /wishlists
2. Add item: POST /wishlists/{id}/items
3. Share: POST /wishlists/{id}/share

---

You: The notification emails look too plain. Make them more attractive.

CodeGenie: I'll improve the email templates...

✅ Created HTML email template
✅ Added product images
✅ Added "View Wishlist" button
✅ Added price comparison (old vs new)
✅ Added responsive design for mobile

📧 Email now includes:
- Product image
- Product name and description
- Old price vs New price (highlighted)
- Discount percentage (in red)
- "View Wishlist" button
- "Unsubscribe" link

---

You: Add a feature to suggest gift ideas based on wishlists

CodeGenie: Interesting! Let me add AI-powered gift suggestions...

✅ Created recommendation engine
✅ Analyzes wishlist items
✅ Finds similar products
✅ Considers price range
✅ Factors in user preferences
✅ Added GET /wishlists/{id}/suggestions endpoint

Gift suggestions now consider:
- Items in wishlist
- Price range of wishlist items
- User's past purchases
- Popular items in similar wishlists
- Seasonal trends

---

You: Perfect! Can you add analytics for wishlist owners?

CodeGenie: Adding analytics...

✅ Created analytics service
✅ Tracks wishlist views
✅ Tracks item additions by others
✅ Tracks shares
✅ Created analytics dashboard endpoint

Analytics include:
- Total views
- Unique visitors
- Most viewed items
- Share count
- Conversion rate (items purchased)
- Trending items

Available at: GET /wishlists/{id}/analytics
```

**Incredible!** Built a complete feature through conversation.

---

## Next Steps

### More Tutorials

- **Testing Strategies**: Learn advanced testing techniques
- **Deployment**: Deploy CodeGenie projects to production
- **Custom Agents**: Create your own specialized agents
- **Integration**: Integrate with external services
- **Performance**: Optimize for high-traffic applications

### Resources

- [User Guide](USER_GUIDE.md) - Comprehensive feature documentation
- [API Reference](API_REFERENCE.md) - Complete API documentation
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues and solutions
- [Examples](../examples/) - More example projects

### Community

- [Discord](https://discord.gg/codegenie) - Chat with other users
- [Forum](https://community.codegenie.dev) - Ask questions
- [GitHub](https://github.com/your-org/codegenie) - Contribute

Happy coding with CodeGenie! 🧞‍♂️
