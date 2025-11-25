# Piglist Web Application - Architecture & Planning Document

## Executive Summary

Piglist is a family gift-sharing web application that maintains the surprise element of gift-giving while coordinating purchases across family members. The app features real-time presence indicators, automatic gift URL scraping, category-based organization, and admin-controlled group rules.

## 1. Technology Stack

### Backend Framework
**Selected: FastAPI (Python)**
- **Rationale**: Modern async support perfect for real-time features
- Automatic API documentation with OpenAPI/Swagger
- Better performance for concurrent users and WebSocket connections
- Type hints and Pydantic for data validation
- Excellent for building APIs with HTMX frontend
- Native async/await support for web scraping and background tasks

### Database
**Selected: PostgreSQL**
- **Rationale**: 
  - Robust relational data (users, groups, gifts, categories)
  - JSONB support for flexible gift metadata from scraping
  - Excellent for complex queries (filtering by category, price, status)
  - Strong ACID compliance for purchase transactions
  - Free tier available on many platforms

### Real-Time Communication
**Selected: Socket.IO (with python-socketio for FastAPI)**
- **Rationale**:
  - Perfect for real-time presence indicators
  - Handles connection drops gracefully
  - Room-based messaging (one room per gift item)
  - Fallback mechanisms for older browsers
  - Works seamlessly with FastAPI via python-socketio ASGI integration
  - Async-native implementation

### Web Scraping
**Selected: BeautifulSoup4 + Requests (with httpx for async)**
- **Primary scraping**: Simple, reliable, handles most sites
- **Async support**: Use httpx for async HTTP requests with FastAPI
- **Backup**: Playwright for JavaScript-heavy sites (if needed)
- **Metadata extraction**: Open Graph tags, Schema.org markup

**Additional Tools**:
- `price-parser` - Extract prices from text
- `Pillow` - Image processing/optimization
- `httpx` - Async HTTP client for FastAPI

### Frontend
**Selected: HTMX + Alpine.js**
- **Rationale**:
  - Minimal JavaScript, maximum interactivity
  - Dynamic updates without full page reloads
  - Perfect pairing with FastAPI backend
  - Server-rendered with progressive enhancement
  - Alpine.js for client-side reactivity (dropdowns, modals, etc.)
  - HTMX for seamless AJAX interactions
  - Socket.IO client for real-time presence features
  - No build step required
  - Great developer experience

### CSS Framework
**Selected: Tailwind CSS**
- **Rationale**:
  - Modern, utility-first approach
  - Highly customizable
  - Excellent with HTMX (no JavaScript conflicts)
  - Small production bundle with PurgeCSS
  - Great documentation and community
  - Perfect for rapid prototyping

### Authentication
**Selected: FastAPI Security + Passlib (not Flask-Login)**
- **Note**: Flask-Login is Flask-specific and incompatible with FastAPI
- **FastAPI approach**:
  - OAuth2 with Password flow (built-in FastAPI security)
  - JWT tokens for stateless authentication
  - Passlib with bcrypt for password hashing
  - Session management via Redis
  - Secure cookie-based sessions for web app
  - API token support for future mobile apps

### Caching & Session Storage
**Selected: Redis**
- **Rationale**:
  - Session storage for authenticated users
  - Real-time presence tracking (TTL keys)
  - Rate limiting for scraping
  - Caching scraped gift data
  - Pub/sub for Socket.IO scaling
  - Works seamlessly with FastAPI via aioredis

### Task Queue
**Selected: Celery + Redis**
- **Use cases**:
  - Asynchronous web scraping
  - Scheduled tasks (clear old presence data)
  - Email notifications (if implemented)
  - Image processing
  - Background cleanup tasks
- **Integration**: Works well with FastAPI via celery worker processes

---

## 2. Database Schema Design

### Entity Relationship Diagram

```mermaid
erDiagram
    users ||--o{ group_members : "belongs to"
    users ||--o{ piglists : "owns"
    users ||--o{ gifts : "purchased by"
    users ||--o{ gift_presence : "viewing"
    users ||--o{ groups : "created by"
    
    groups ||--o{ group_members : "has"
    groups ||--o{ categories : "contains"
    groups ||--o{ piglists : "contains"
    
    categories ||--o{ gifts : "categorizes"
    
    piglists ||--o{ gifts : "contains"
    
    gifts ||--o{ gift_presence : "has viewers"
    
    users {
        int id PK
        string email UK
        string password_hash
        string display_name
        timestamp created_at
        timestamp last_login
        boolean is_active
    }
    
    groups {
        int id PK
        string name
        string invite_code UK
        int created_by FK
        timestamp created_at
        timestamp lock_date
        boolean is_locked
    }
    
    group_members {
        int id PK
        int group_id FK
        int user_id FK
        string role
        timestamp joined_at
    }
    
    categories {
        int id PK
        int group_id FK
        string name
        decimal spending_limit
        decimal max_item_price
        int display_order
        timestamp created_at
    }
    
    piglists {
        int id PK
        int user_id FK
        int group_id FK
        timestamp created_at
        timestamp updated_at
    }
    
    gifts {
        int id PK
        int piglist_id FK
        int category_id FK
        string url
        string title
        text description
        decimal price
        string image_url
        jsonb metadata
        string scrape_status
        string status
        int purchased_by FK
        timestamp purchased_at
        timestamp created_at
        timestamp updated_at
    }
    
    gift_presence {
        int id PK
        int gift_id FK
        int user_id FK
        timestamp started_at
        timestamp last_heartbeat
    }
```

### Core Tables

#### `users`
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

#### `groups`
```sql
CREATE TABLE groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    invite_code VARCHAR(50) UNIQUE NOT NULL,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    lock_date TIMESTAMP,
    is_locked BOOLEAN DEFAULT FALSE
);
```

#### `group_members`
```sql
CREATE TABLE group_members (
    id SERIAL PRIMARY KEY,
    group_id INTEGER REFERENCES groups(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) DEFAULT 'member', -- 'admin' or 'member'
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(group_id, user_id)
);
```

#### `categories`
```sql
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    group_id INTEGER REFERENCES groups(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    spending_limit DECIMAL(10, 2),
    max_item_price DECIMAL(10, 2),
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `piglists`
```sql
CREATE TABLE piglists (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    group_id INTEGER REFERENCES groups(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, group_id)
);
```

#### `gifts`
```sql
CREATE TABLE gifts (
    id SERIAL PRIMARY KEY,
    piglist_id INTEGER REFERENCES piglists(id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    url TEXT NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2),
    image_url TEXT,
    metadata JSONB, -- Store size, color, options, etc.
    scrape_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'success', 'failed', 'manual'
    status VARCHAR(20) DEFAULT 'available', -- 'available', 'purchased'
    purchased_by INTEGER REFERENCES users(id),
    purchased_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `gift_presence`
```sql
CREATE TABLE gift_presence (
    id SERIAL PRIMARY KEY,
    gift_id INTEGER REFERENCES gifts(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(gift_id, user_id)
);
```

### Indexes for Performance
```sql
CREATE INDEX idx_group_members_user ON group_members(user_id);
CREATE INDEX idx_group_members_group ON group_members(group_id);
CREATE INDEX idx_gifts_piglist ON gifts(piglist_id);
CREATE INDEX idx_gifts_category ON gifts(category_id);
CREATE INDEX idx_gifts_status ON gifts(status);
CREATE INDEX idx_gift_presence_gift ON gift_presence(gift_id);
CREATE INDEX idx_gift_presence_heartbeat ON gift_presence(last_heartbeat);
```

---

## 3. System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Client Browser                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   HTML/CSS   │  │   HTMX +     │  │  Socket.IO   │       │
│  │  (Tailwind)  │  │  Alpine.js   │  │   Client     │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Application                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   API        │  │  Socket.IO   │  │   Business   │       │
│  │   Routes     │  │  (python-    │  │   Logic      │       │
│  │              │  │  socketio)   │  │              │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Auth       │  │  Scraping    │  │   Models     │       │
│  │   (FastAPI   │  │  Service     │  │   (SQLAlch-  │       │
│  │   Security)  │  │  (httpx)     │  │   emy)       │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
┌─────────────────────────┐  ┌─────────────────────────┐
│      PostgreSQL         │  │        Redis            │
│   (Primary Database)    │  │  (Sessions, Cache,      │
│                         │  │   Presence Tracking)    │
└─────────────────────────┘  └─────────────────────────┘
                            │
                            ▼
                ┌─────────────────────────┐
                │    Celery Workers       │
                │  (Async Scraping)       │
                └─────────────────────────┘
```

### Component Breakdown

#### 1. **FastAPI Application Layer**
- **API Routes**: Handle HTTP requests, return HTML fragments for HTMX
- **Template Rendering**: Jinja2 templates for server-side rendering
- **WebSocket Handlers**: Socket.IO for real-time presence management
- **Middleware**: Authentication, CORS, rate limiting
- **Async Support**: Native async/await for concurrent operations

#### 2. **Business Logic Layer**
- **Gift Service**: Async CRUD operations, purchase logic
- **Scraping Service**: Async URL parsing with httpx, metadata extraction
- **Presence Service**: Real-time tracking via Socket.IO and Redis
- **Group Service**: Manage groups, invites, rules
- **Category Service**: Enforce spending limits and validation

#### 3. **Data Access Layer**
- **SQLAlchemy ORM**: Async database models and queries
- **aioredis**: Async Redis client for sessions and caching
- **Query Optimization**: Eager loading, caching strategies
- **Pydantic Models**: Request/response validation

#### 4. **External Services**
- **Web Scraping**: BeautifulSoup4 with httpx, Playwright fallback
- **Image Storage**: Local filesystem or S3-compatible storage
- **Email Service**: SMTP for notifications (optional)
- **CDN**: For static assets (Tailwind CSS, Alpine.js, HTMX)

---

## 4. Authentication & Authorization System

### User Registration Flow
1. User provides email and password via HTMX form
2. FastAPI validates email format and password strength (Pydantic)
3. Hash password with Passlib bcrypt (cost factor: 12)
4. Create user record in database
5. Generate JWT token or session cookie
6. Return success response to HTMX
7. Auto-login after registration

### Login Flow
1. User provides email and password via HTMX form
2. FastAPI verifies credentials against database
3. Generate JWT access token and refresh token
4. Store session in Redis (server-side) with user_id
5. Set secure, httpOnly cookie with session ID
6. Return success response, HTMX redirects to dashboard

### FastAPI Authentication Implementation
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for API endpoints
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# JWT settings
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await get_user_by_id(user_id)
    if user is None:
        raise credentials_exception
    return user
```

### Group Access Control
```python
from fastapi import Depends, HTTPException
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"    # Can modify group settings, categories, lock dates
    MEMBER = "member"  # Can view all piglists, manage own piglist
    ANONYMOUS = "anonymous"  # Limited access via invite link

# Access rules
# - Users can only view piglists within their groups
# - Users cannot see who purchased/is viewing their own gifts
# - Users can see purchase status of gifts in others' piglists
# - Admins can modify group settings and categories
# - After lock date, no modifications allowed (view-only)

async def require_group_member(
    group_id: int,
    current_user: User = Depends(get_current_user)
):
    """Dependency to ensure user is a member of the group"""
    is_member = await check_group_membership(current_user.id, group_id)
    if not is_member:
        raise HTTPException(status_code=403, detail="Not a member of this group")
    return current_user

async def require_group_admin(
    group_id: int,
    current_user: User = Depends(get_current_user)
):
    """Dependency to ensure user is an admin of the group"""
    is_admin = await check_group_admin(current_user.id, group_id)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
```

### Security Measures
- **Password Requirements**: Min 8 chars, mix of upper/lower/numbers (Pydantic validation)
- **Token Expiration**: 30 min access tokens, 7 day refresh tokens
- **CSRF Protection**: Double-submit cookie pattern for HTMX requests
- **Rate Limiting**: slowapi (FastAPI rate limiter) to prevent brute force
- **SQL Injection**: Parameterized queries via SQLAlchemy ORM
- **XSS Protection**: Jinja2 auto-escaping, CSP headers
- **CORS**: Configured for same-origin requests only

---

## 5. Real-Time Presence System Architecture

### Technology: Socket.IO with Redis Adapter

### Presence Tracking Flow

```
User Opens Gift Detail Page
         │
         ▼
┌─────────────────────────┐
│  Client emits           │
│  'join_gift_view'       │
│  {gift_id: 123}         │
└─────────────────────────┘
         │
         ▼
┌─────────────────────────┐
│  Server checks if       │
│  gift already has       │
│  active viewer          │
└─────────────────────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
  YES        NO
    │         │
    │         ▼
    │    ┌─────────────────────────┐
    │    │  Join Socket.IO room    │
    │    │  'gift_123'             │
    │    │  Store in Redis:        │
    │    │  gift:123:viewer = uid  │
    │    │  TTL: 5 minutes         │
    │    └─────────────────────────┘
    │         │
    │         ▼
    │    ┌─────────────────────────┐
    │    │  Broadcast to all       │
    │    │  'gift_123_occupied'    │
    │    └─────────────────────────┘
    │         │
    ▼         ▼
┌─────────────────────────┐
│  Client receives        │
│  presence status        │
│  Updates UI             │
└─────────────────────────┘
```

### Heartbeat Mechanism
```javascript
// Client-side heartbeat every 30 seconds
setInterval(() => {
    socket.emit('heartbeat', {gift_id: currentGiftId});
}, 30000);
```

### Cleanup Strategy
1. **On disconnect**: Remove presence immediately
2. **Heartbeat timeout**: Clear presence after 60 seconds without heartbeat
3. **Scheduled cleanup**: Celery task every 5 minutes to clear stale entries
4. **Redis TTL**: Automatic expiration after 5 minutes

### Redis Data Structure
```
# Active viewer
gift:123:viewer = "user_456"
TTL: 300 seconds

# Heartbeat timestamp
gift:123:heartbeat = "1700000000"
TTL: 300 seconds
```

### Socket.IO Events
```python
# Client → Server
'join_gift_view'     # User opens gift page
'leave_gift_view'    # User closes gift page
'heartbeat'          # Keep-alive signal

# Server → Client
'gift_occupied'      # Someone is viewing
'gift_available'     # No one viewing
'viewer_count'       # Number of viewers (if allowing multiple)
```

---

## 6. Web Scraping Implementation Strategy

### Scraping Architecture

#### Primary Scraper (BeautifulSoup4)
```python
def scrape_gift_url(url: str) -> dict:
    """
    Extract gift metadata from URL
    Returns: {
        'title': str,
        'price': float,
        'image_url': str,
        'description': str,
        'metadata': dict  # size, color, etc.
    }
    """
    # 1. Fetch page content
    # 2. Try Open Graph tags first
    # 3. Fall back to Schema.org markup
    # 4. Parse price with price-parser
    # 5. Extract images
    # 6. Return structured data
```

#### Fallback Scraper (Playwright)
For JavaScript-heavy sites (React SPAs, etc.)
```python
async def scrape_with_playwright(url: str) -> dict:
    """
    Use headless browser for dynamic content
    """
    # 1. Launch browser
    # 2. Navigate to URL
    # 3. Wait for content to load
    # 4. Extract data
    # 5. Close browser
```

### Metadata Extraction Priority

1. **Open Graph Tags** (Most reliable)
   ```html
   <meta property="og:title" content="Product Name">
   <meta property="og:image" content="image.jpg">
   <meta property="og:description" content="...">
   <meta property="product:price:amount" content="29.99">
   ```

2. **Schema.org Markup** (Structured data)
   ```html
   <script type="application/ld+json">
   {
     "@type": "Product",
     "name": "Product Name",
     "offers": {"price": "29.99"}
   }
   </script>
   ```

3. **HTML Parsing** (Fallback)
   - Common CSS selectors for e-commerce sites
   - Price patterns: `$XX.XX`, `XX,XX €`, etc.
   - Image selection: largest image, product-specific classes

### Scraping Service Design

```python
class GiftScraperService:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 ...'
        })
    
    def scrape(self, url: str) -> dict:
        # Try primary scraper
        try:
            return self._scrape_with_bs4(url)
        except Exception:
            # Fall back to Playwright
            return self._scrape_with_playwright(url)
    
    def _scrape_with_bs4(self, url: str) -> dict:
        # Implementation
        pass
    
    async def _scrape_with_playwright(self, url: str) -> dict:
        # Implementation
        pass
```

### Async Scraping with Celery

```python
@celery.task
def scrape_gift_async(gift_id: int, url: str):
    """
    Background task to scrape gift URL
    """
    scraper = GiftScraperService()
    try:
        data = scraper.scrape(url)
        # Update gift record
        gift = Gift.query.get(gift_id)
        gift.title = data['title']
        gift.price = data['price']
        gift.image_url = data['image_url']
        gift.metadata = data['metadata']
        gift.scrape_status = 'success'
        db.session.commit()
    except Exception as e:
        gift.scrape_status = 'failed'
        db.session.commit()
        # Notify user to fill manually
```

### Rate Limiting & Caching
- **Rate limit**: Max 10 scrapes per minute per user
- **Cache**: Store scraped data for 24 hours (same URL)
- **Retry logic**: 3 attempts with exponential backoff
- **Timeout**: 30 seconds per scrape attempt

### Manual Fallback UI
If scraping fails:
```
┌─────────────────────────────────────┐
│  Automatic scraping failed          │
│  Please fill in the details:        │
│                                     │
│  Title: [________________]          │
│  Price: [________________]          │
│  Image URL: [________________]      │
│  Description: [________________]    │
│                                     │
│  [Save Gift]                        │
└─────────────────────────────────────┘
```

---

## 7. API Endpoints & Routes

### Public Routes (No Auth Required)
```
GET  /                          # Landing page
GET  /register                  # Registration form
POST /register                  # Create account
GET  /login                     # Login form
POST /login                     # Authenticate
GET  /join/{invite_code}        # Join group via invite
```

### Authenticated Routes
```
GET  /dashboard                 # User dashboard (list of groups)
GET  /logout                    # End session

# Group Management
GET  /groups/create             # Create group form
POST /groups/create             # Create new group
GET  /groups/{group_id}         # Group overview
GET  /groups/{group_id}/settings # Admin settings (if admin)
POST /groups/{group_id}/settings # Update settings
GET  /groups/{group_id}/invite  # Generate invite link

# Category Management (Admin only)
POST /groups/{group_id}/categories        # Create category
PUT  /groups/{group_id}/categories/{id}   # Update category
DELETE /groups/{group_id}/categories/{id} # Delete category

# Piglist Views
GET  /groups/{group_id}/piglists          # All piglists in group
GET  /groups/{group_id}/piglists/{user_id} # Specific user's piglist
GET  /groups/{group_id}/my-piglist        # Current user's piglist

# Gift Management
GET  /groups/{group_id}/gifts/add         # Add gift form
POST /groups/{group_id}/gifts             # Create gift
GET  /groups/{group_id}/gifts/{gift_id}   # Gift details
PUT  /groups/{group_id}/gifts/{gift_id}   # Update gift
DELETE /groups/{group_id}/gifts/{gift_id} # Delete gift
POST /groups/{group_id}/gifts/{gift_id}/purchase # Mark as purchased
```

### API Endpoints (AJAX/JSON)
```
POST /api/gifts/scrape          # Scrape URL for metadata
GET  /api/gifts/{id}/status     # Check gift status
POST /api/gifts/{id}/purchase   # Purchase gift
GET  /api/groups/{id}/stats     # Group statistics

# Real-time presence (Socket.IO)
WS   /socket.io                 # WebSocket connection
```

### Route Protection
```python
from functools import wraps
from flask_login import current_user

def group_member_required(f):
    @wraps(f)
    def decorated_function(group_id, *args, **kwargs):
        if not is_group_member(current_user.id, group_id):
            abort(403)
        return f(group_id, *args, **kwargs)
    return decorated_function

def group_admin_required(f):
    @wraps(f)
    def decorated_function(group_id, *args, **kwargs):
        if not is_group_admin(current_user.id, group_id):
            abort(403)
        return f(group_id, *args, **kwargs)
    return decorated_function
```

---

## 8. UI/UX Design Considerations

### Key Pages & Wireframes

#### 1. Dashboard (After Login)
```
┌───────────────────────────────────────────────────────────┐
│  Piglist                                      [Profile ▼] │
├───────────────────────────────────────────────────────────┤
│                                                           │
│  Your Groups                            [+ Create Group]  │
│                                                           │
│  ┌────────────────────┐  ┌────────────────────┐           │
│  │ Smith Family       │  │ Extended Family    │           │
│  │ 5 members          │  │ 12 members         │           │
│  │ Lock: Dec 20       │  │ Lock: Dec 24       │           │
│  │ [View Group]       │  │ [View Group]       │           │
│  └────────────────────┘  └────────────────────┘           │
│                                                           │
│  Join a Group                                             │
│  [Enter Invite Code]                                      │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

#### 2. Group Overview
```
┌───────────────────────────────────────────────────────────┐
│  ← Back to Dashboard          Smith Family    [Settings]  │
├───────────────────────────────────────────────────────────┤
│                                                           │
│  Members (5)                                              │
│  👤 John (You)  👤 Jane  👤 Mom  👤 Dad  👤 Sister      │
│                                                           │
│  [View All Piglists]  [My Piglist]                        │
│                                                           │
│  Categories                                               │
│  ┌───────────────────────────────────────────────────┐    │
│  │ From Parents    │ $200 limit │ $50 max item       │    │
│  │ From Siblings   │ $100 limit │ $30 max item       │    │
│  │ From Relatives  │ $50 limit  │ $25 max item       │    │
│  └───────────────────────────────────────────────────┘    │
│                                                           │
│  Lock Date: December 20, 2024                             │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

#### 3. All Piglists View
```
┌───────────────────────────────────────────────────────────┐
│  ← Back                  Smith Family Piglists            │
├───────────────────────────────────────────────────────────┤
│                                                           │
│  Filter: [All Members ▼]  [All Categories ▼]              │
│                                                           │
│  Jane's Piglist                                           │
│  ┌────────────────────────────────────────────────────┐   │
│  │ From Parents ($150 / $200)                         │   │
│  │ ┌──────────┐ ┌──────────┐ ┌──────────┐             │   │
│  │ │ Item 1   │ │ Item 2   │ │ Item 3   │             │   │
│  │ │ $45      │ │ $60      │ │ $45      │             │   │
│  │ │ ✓ Bought │ │⚠️ Viewing│ │          │            │   │
│  │ └──────────┘ └──────────┘ └──────────┘             │   │
│  │                                                    │   │
│  │ From Siblings ($80 / $100)                         │   │
│  │ ┌──────────┐ ┌──────────┐                          │   │
│  │ │ Item 4   │ │ Item 5   │                          │   │
│  │ │ $30      │ │ $50      │                          │   │
│  │ └──────────┘ └──────────┘                          │   │
│  └────────────────────────────────────────────────────┘   │
│                                                           │
│  Mom's Piglist                                            │
│  [Similar layout...]                                      │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

#### 4. My Piglist (Edit Mode)
```
┌───────────────────────────────────────────────────────────┐
│  ← Back                  My Piglist                [+ Add]│
├───────────────────────────────────────────────────────────┤
│                                                           │
│  From Parents ($150 / $200)                               │
│  ┌────────────────────────────────────────────────────┐   │
│  │ ┌──────────┐ ┌──────────┐ ┌──────────┐             │   │
│  │ │ Item 1   │ │ Item 2   │ │ Item 3   │             │   │
│  │ │ $45      │ │ $60      │ │ $45      │             │   │
│  │ │ [Edit]   │ │ [Edit]   │ │ [Edit]   │             │   │
│  │ │ [Delete] │ │ [Delete] │ │ [Delete] │             │   │
│  │ └──────────┘ └──────────┘ └──────────┘             │   │
│  └────────────────────────────────────────────────────┘   │
│                                                           │
│  From Siblings ($80 / $100)                               │
│  [Similar layout...]                                      │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

#### 5. Add Gift Modal
```
┌───────────────────────────────────────────────────────────┐
│  Add Gift to Piglist                            [✕ Close] │
├───────────────────────────────────────────────────────────┤
│                                                           │
│  Category: [From Parents ▼]                               │
│                                                           │
│  Gift URL:                                                │
│  [https://amazon.com/product/...]    [Fetch Details]      │
│                                                           │
│  ┌───────────────────────────────────────────────────┐    │
│  │ 🔄 Fetching gift details...                       │    │
│  └───────────────────────────────────────────────────┘    │
│                                                           │
│  OR fill manually:                                        │
│                                                           │
│  Title: [_____________________________________]           │
│  Price: [$_______]                                        │
│  Image URL: [_____________________________________]       │
│  Description: [_____________________________________]     │
│                                                           │
│  [Cancel]                                  [Add Gift]     │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

#### 6. Gift Detail View (Other's Gift)
```
┌───────────────────────────────────────────────────────────┐
│  ← Back to Jane's Piglist                                 │
├───────────────────────────────────────────────────────────┤
│                                                           │
│  ┌─────────────────┐                                      │
│  │                 │  Wireless Headphones                 │
│  │   [Image]       │  $59.99                              │
│  │                 │                                      │
│  │                 │  Category: From Parents              │
│  └─────────────────┘                                      │
│                                                           │
│  Description:                                             │
│  High-quality wireless headphones with noise              │
│  cancellation...                                          │
│                                                           │
│  Options: Black, Size: One Size                           │
│                                                           │
│  ⚠️ Someone is currently viewing this item                │
│                                                           │
│  [View on Website]  [Mark as Purchased]                   │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

### Visual Design Elements

#### Color Scheme
- **Primary**: Warm, festive colors (red, green, gold)
- **Secondary**: Neutral grays for backgrounds
- **Accent**: Blue for interactive elements
- **Status Colors**:
  - Green: Available
  - Yellow: Being viewed (warning)
  - Red: Purchased
  - Gray: Locked/disabled

#### Gift Tile States
```
┌────────────┐  ┌────────────┐  ┌────────────┐
│            │  │ ⚠️         │  │ ✓          │
│  [Image]   │  │  [Image]   │  │  [Image]   │
│            │  │            │  │            │
│ Item Name  │  │ Item Name  │  │ Item Name  │
│ $XX.XX     │  │ $XX.XX     │  │ $XX.XX     │
└────────────┘  └────────────┘  └────────────┘
  Available      Being Viewed     Purchased
```

#### Responsive Design
- **Desktop**: Multi-column grid layout
- **Tablet**: 2-column layout
- **Mobile**: Single column, stacked cards

---

## 9. Security & Privacy Considerations

### Data Privacy
1. **Gift Visibility Rules**:
   - Users CANNOT see who purchased their gifts
   - Users CANNOT see who is viewing their gifts
   - Users CAN see purchase status of others' gifts
   - Users CAN see who is viewing others' gifts

2. **Personal Information**:
   - Minimal data collection (email, name only)
   - No payment information stored
   - No tracking of external purchases

3. **Group Privacy**:
   - Groups are invite-only
   - Invite codes are unique and non-guessable (UUID)
   - No public group directory

### Security Measures

#### 1. Authentication Security
```python
# Password requirements
MIN_PASSWORD_LENGTH = 8
REQUIRE_UPPERCASE = True
REQUIRE_LOWERCASE = True
REQUIRE_DIGIT = True

# Session security
SESSION_COOKIE_SECURE = True  # HTTPS only
SESSION_COOKIE_HTTPONLY = True  # No JS access
SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
```

#### 2. Input Validation
- **URL validation**: Check for valid HTTP/HTTPS URLs
- **Price validation**: Positive numbers, max 2 decimals
- **Text sanitization**: Strip HTML tags, prevent XSS
- **File uploads**: Validate image types, size limits

#### 3. Rate Limiting
```python
# Flask-Limiter configuration
RATELIMIT_STORAGE_URL = "redis://localhost:6379"

# Limits
@limiter.limit("5 per minute")  # Login attempts
@limiter.limit("10 per minute")  # Gift scraping
@limiter.limit("100 per hour")  # General API calls
```

#### 4. CSRF Protection
- Flask-WTF CSRF tokens on all forms
- Validate tokens on POST/PUT/DELETE requests
- Exempt Socket.IO endpoints (use session auth)

#### 5. SQL Injection Prevention
- Use SQLAlchemy ORM (parameterized queries)
- Never concatenate user input into SQL
- Validate all input types

#### 6. XSS Prevention
- Jinja2 auto-escaping enabled
- Content Security Policy headers
- Sanitize user-generated content

#### 7. Secure Headers
```python
# Flask-Talisman or manual headers
SECURE_HEADERS = {
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'SAMEORIGIN',
    'X-XSS-Protection': '1; mode=block',
    'Content-Security-Policy': "default-src 'self'; img-src 'self' https:; script-src 'self' 'unsafe-inline'"
}
```

### Compliance Considerations
- **GDPR** (if EU users): Right to deletion, data export
- **CCPA** (if CA users): Privacy policy, opt-out
- **Terms of Service**: User agreement, liability limits
- **Privacy Policy**: Data collection, usage, retention

---

## 10. Deployment & Scaling Strategy

### Development Environment

#### VS Code Dev Containers Setup

**Overview**: VS Code Dev Containers provide a consistent, reproducible development environment across multiple machines using Docker. This eliminates "works on my machine" issues and ensures all team members have identical development setups.

**Benefits**:
- Consistent environment across Windows, macOS, and Linux
- No need to install Python, PostgreSQL, Redis locally
- Pre-configured debugging and extensions
- Easy onboarding for new developers
- Isolated from host system

#### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop) installed and running
- [VS Code](https://code.visualstudio.com/) with [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
- Git for version control

#### Project Structure for Dev Containers
```
piglist/
├── .devcontainer/
│   ├── devcontainer.json       # VS Code dev container configuration
│   ├── docker-compose.yml      # Multi-service orchestration
│   ├── Dockerfile              # Custom Python environment
│   └── postCreateCommand.sh    # Setup script after container creation
├── .vscode/
│   ├── launch.json             # Debug configurations
│   ├── settings.json           # Workspace settings
│   └── extensions.json         # Recommended extensions
├── app/                        # Application code
├── requirements.txt            # Python dependencies
├── requirements-dev.txt        # Development dependencies
└── README.md
```

#### Complete Dev Container Configuration

**`.devcontainer/devcontainer.json`**:
```json
{
  "name": "Piglist Development",
  "dockerComposeFile": "docker-compose.yml",
  "service": "app",
  "workspaceFolder": "/workspace",
  
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-python.vscode-pylance",
        "ms-python.black-formatter",
        "ms-python.flake8",
        "ms-python.isort",
        "charliermarsh.ruff",
        "ms-azuretools.vscode-docker",
        "mtxr.sqltools",
        "mtxr.sqltools-driver-pg",
        "cweijan.vscode-redis-client",
        "tamasfe.even-better-toml",
        "redhat.vscode-yaml",
        "usernamehw.errorlens",
        "eamodio.gitlens",
        "github.copilot"
      ],
      "settings": {
        "python.defaultInterpreterPath": "/usr/local/bin/python",
        "python.linting.enabled": true,
        "python.linting.pylintEnabled": false,
        "python.linting.flake8Enabled": true,
        "python.formatting.provider": "black",
        "python.testing.pytestEnabled": true,
        "python.testing.unittestEnabled": false,
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
          "source.organizeImports": true
        },
        "[python]": {
          "editor.defaultFormatter": "ms-python.black-formatter",
          "editor.tabSize": 4
        },
        "files.exclude": {
          "**/__pycache__": true,
          "**/*.pyc": true,
          "**/.pytest_cache": true
        }
      }
    }
  },
  
  "forwardPorts": [8000, 5432, 6379, 5555],
  "portsAttributes": {
    "8000": {
      "label": "FastAPI",
      "onAutoForward": "notify"
    },
    "5432": {
      "label": "PostgreSQL"
    },
    "6379": {
      "label": "Redis"
    },
    "5555": {
      "label": "Celery Flower"
    }
  },
  
  "postCreateCommand": "bash .devcontainer/postCreateCommand.sh",
  
  "remoteUser": "vscode",
  
  "features": {
    "ghcr.io/devcontainers/features/git:1": {}
  }
}
```

**Note**: GitHub CLI is installed directly in the Dockerfile rather than as a feature.

**`.devcontainer/docker-compose.yml`**:
```yaml
version: '3.8'

services:
  app:
    build:
      context: ..
      dockerfile: .devcontainer/Dockerfile
    volumes:
      - ..:/workspace:cached
      - venv:/workspace/.venv
    command: sleep infinity
    environment:
      - DATABASE_URL=postgresql+asyncpg://piglist:piglist_dev_pass@db:5432/piglist_dev
      - REDIS_URL=redis://redis:6379/0
      - PYTHONUNBUFFERED=1
      - ENVIRONMENT=development
    depends_on:
      - db
      - redis
    networks:
      - piglist-network

  db:
    image: postgres:15-alpine
    restart: unless-stopped
    volumes:
      - postgres-data:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=piglist
      - POSTGRES_PASSWORD=piglist_dev_pass
      - POSTGRES_DB=piglist_dev
    ports:
      - "5432:5432"
    networks:
      - piglist-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U piglist"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes:
      - redis-data:/data
    ports:
      - "6379:6379"
    networks:
      - piglist-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  celery-worker:
    build:
      context: ..
      dockerfile: .devcontainer/Dockerfile
    command: celery -A app.celery worker --loglevel=info
    volumes:
      - ..:/workspace:cached
    environment:
      - DATABASE_URL=postgresql+asyncpg://piglist:piglist_dev_pass@db:5432/piglist_dev
      - REDIS_URL=redis://redis:6379/0
      - PYTHONUNBUFFERED=1
    depends_on:
      - db
      - redis
    networks:
      - piglist-network

  celery-flower:
    build:
      context: ..
      dockerfile: .devcontainer/Dockerfile
    command: celery -A app.celery flower --port=5555
    volumes:
      - ..:/workspace:cached
    environment:
      - DATABASE_URL=postgresql+asyncpg://piglist:piglist_dev_pass@db:5432/piglist_dev
      - REDIS_URL=redis://redis:6379/0
    ports:
      - "5555:5555"
    depends_on:
      - redis
      - celery-worker
    networks:
      - piglist-network

volumes:
  postgres-data:
  redis-data:
  venv:

networks:
  piglist-network:
    driver: bridge
```

**`.devcontainer/Dockerfile`**:
```dockerfile
FROM python:3.11-slim

# Install system dependencies including GitHub CLI
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    postgresql-client \
    redis-tools \
    && curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt-get update \
    && apt-get install -y gh \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && apt-get update \
    && apt-get install -y sudo \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# Set working directory
WORKDIR /workspace

# Install Python dependencies
COPY requirements.txt ./
COPY requirements-dev.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-dev.txt

# Install Playwright and its dependencies
RUN pip install playwright

# Install Playwright system dependencies and browsers
# Set NODE_TLS_REJECT_UNAUTHORIZED=0 to bypass SSL certificate validation during download
RUN apt-get update && apt-get install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*

# Install Chromium with SSL verification disabled for corporate proxies
RUN NODE_TLS_REJECT_UNAUTHORIZED=0 playwright install chromium || \
    (echo "Warning: Playwright browser installation failed. Browsers can be installed later with 'playwright install chromium'" && true)

USER $USERNAME
```

**Key Features**:
- **GitHub CLI**: Installed for git operations and GitHub integration
- **Playwright**: Fully configured with Chromium browser and all system dependencies
- **SSL Handling**: Includes workaround for corporate proxy environments
- **Non-root User**: Runs as `vscode` user for security

**`.devcontainer/postCreateCommand.sh`**:
```bash
#!/bin/bash

echo "🚀 Setting up Piglist development environment..."

# Wait for database to be ready
echo "⏳ Waiting for PostgreSQL..."
until pg_isready -h db -U piglist; do
  sleep 1
done

echo "✅ PostgreSQL is ready!"

# Wait for Redis to be ready
echo "⏳ Waiting for Redis..."
until redis-cli -h redis ping; do
  sleep 1
done

echo "✅ Redis is ready!"

# Install Python dependencies in virtual environment
echo "📦 Installing Python dependencies..."
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt -r requirements-dev.txt

# Initialize database
echo "🗄️ Initializing database..."
alembic upgrade head || echo "⚠️ No migrations found yet"

# Create initial data (optional)
# python scripts/seed_data.py

echo "✨ Development environment is ready!"
echo ""
echo "📝 Quick Start Commands:"
echo "  - Start FastAPI: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo "  - Run tests: pytest"
echo "  - Format code: black ."
echo "  - Lint code: flake8 ."
echo "  - Database migrations: alembic revision --autogenerate -m 'description'"
echo ""
echo "🌐 Services:"
echo "  - FastAPI: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - Celery Flower: http://localhost:5555"
echo "  - PostgreSQL: localhost:5432"
echo "  - Redis: localhost:6379"
```

**Note**: This script runs automatically after the container is created.

**`.vscode/launch.json`**:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI: Debug",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload",
        "--host",
        "0.0.0.0",
        "--port",
        "8000"
      ],
      "jinja": true,
      "justMyCode": false,
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    },
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal",
      "justMyCode": false
    },
    {
      "name": "Python: Pytest",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": [
        "-v",
        "-s"
      ],
      "console": "integratedTerminal",
      "justMyCode": false
    }
  ]
}
```

**`.vscode/settings.json`**:
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.terminal.activateEnvironment": true,
  "sqltools.connections": [
    {
      "name": "Piglist Dev DB",
      "driver": "PostgreSQL",
      "server": "localhost",
      "port": 5432,
      "database": "piglist_dev",
      "username": "piglist",
      "password": "piglist_dev_pass"
    }
  ]
}
```

#### Setup Instructions for Multiple Machines

**Initial Setup (First Time)**:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/piglist.git
   cd piglist
   ```

2. **Open in VS Code**:
   ```bash
   code .
   ```

3. **Reopen in Container**:
   - VS Code will detect the `.devcontainer` folder
   - Click "Reopen in Container" when prompted
   - Or: Press `F1` → "Dev Containers: Reopen in Container"

4. **Wait for setup**:
   - Docker will build the images (first time takes 5-10 minutes)
   - `postCreateCommand.sh` will run automatically
   - All services will start (FastAPI, PostgreSQL, Redis, Celery)

5. **Verify setup**:
   ```bash
   # Check Python version
   python --version
   
   # Check database connection
   psql -h db -U piglist -d piglist_dev
   
   # Check Redis connection
   redis-cli -h redis ping
   
   # Start FastAPI
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Access services**:
   - FastAPI: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Celery Flower: http://localhost:5555

**Switching Between Machines**:

The beauty of dev containers is that your environment is defined in code. To work on a different machine:

1. **Install prerequisites** (Docker Desktop, VS Code, Dev Containers extension)
2. **Clone the repository**
3. **Open in container** (VS Code handles everything else)

All dependencies, configurations, and services are automatically set up identically.

**Syncing Changes**:

When team members update the dev container configuration:

1. **Pull latest changes**:
   ```bash
   git pull origin main
   ```

2. **Rebuild container**:
   - Press `F1` → "Dev Containers: Rebuild Container"
   - This ensures you have the latest dependencies and configurations

#### Common Development Tasks

**Running the Application**:
```bash
# Development server with hot reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or use the VS Code debugger (F5)
```

**Database Migrations**:
```bash
# Create a new migration
alembic revision --autogenerate -m "Add user table"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

**Running Tests**:
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_users.py

# Run with VS Code Test Explorer (Testing sidebar)
```

**Code Quality**:
```bash
# Format code
black .

# Sort imports
isort .

# Lint code
flake8 .

# Type checking
mypy app/
```

**Celery Tasks**:
```bash
# Start Celery worker (already running in container)
celery -A app.celery worker --loglevel=info

# Monitor tasks with Flower
# Visit http://localhost:5555
```

**Database Access**:
```bash
# Connect to PostgreSQL
psql -h db -U piglist -d piglist_dev

# Or use VS Code SQLTools extension (Ctrl+Shift+P → "SQLTools: Connect")
```

**Redis Access**:
```bash
# Connect to Redis CLI
redis-cli -h redis

# Or use VS Code Redis extension
```

#### Troubleshooting

**Container won't start**:
```bash
# Check Docker is running
docker ps

# View container logs
docker-compose -f .devcontainer/docker-compose.yml logs

# Rebuild from scratch
docker-compose -f .devcontainer/docker-compose.yml down -v
# Then: F1 → "Dev Containers: Rebuild Container"
```

**Database connection issues**:
```bash
# Check if PostgreSQL is running
docker-compose -f .devcontainer/docker-compose.yml ps

# Check database logs
docker-compose -f .devcontainer/docker-compose.yml logs db

# Reset database
docker-compose -f .devcontainer/docker-compose.yml down -v
docker-compose -f .devcontainer/docker-compose.yml up -d db
```

**Port already in use**:
```bash
# Find process using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill the process or change port in docker-compose.yml
```

**Slow performance on Windows**:
- Ensure WSL 2 is enabled (not WSL 1)
- Store project files in WSL filesystem, not Windows filesystem
- Increase Docker Desktop memory allocation (Settings → Resources)

**Extensions not installing**:
- Press `F1` → "Developer: Reload Window"
- Or manually install from Extensions sidebar

**Python interpreter not found**:
```bash
# Activate virtual environment
source .venv/bin/activate

# Set interpreter in VS Code
# F1 → "Python: Select Interpreter" → Choose .venv/bin/python
```

#### Environment Variables

Create a `.env` file in the project root (not committed to git):

```bash
# .env
DATABASE_URL=postgresql+asyncpg://piglist:piglist_dev_pass@db:5432/piglist_dev
REDIS_URL=redis://redis:6379/0
SECRET_KEY=your-secret-key-here
ENVIRONMENT=development
DEBUG=True

# Optional
SENTRY_DSN=
EMAIL_HOST=
EMAIL_PORT=
```

Add to `.gitignore`:
```
.env
.env.local
```

#### Benefits of This Setup

1. **Consistency**: Everyone has identical development environment
2. **Isolation**: No conflicts with host system Python/packages
3. **Portability**: Works on Windows, macOS, Linux
4. **Onboarding**: New developers productive in minutes
5. **Services**: PostgreSQL, Redis, Celery pre-configured
6. **Debugging**: Full VS Code debugging support
7. **Extensions**: Automatically installs recommended tools
8. **Hot Reload**: FastAPI auto-reloads on code changes
9. **Testing**: Pytest configured and ready
10. **Database Tools**: Direct access to PostgreSQL and Redis

#### Alternative: Local Setup (Without Containers)
```
If you prefer not to use containers:
- Python 3.11+
- PostgreSQL 15 (local installation)
- Redis 7 (local installation)
- Create virtual environment: python -m venv .venv
- Install dependencies: pip install -r requirements.txt
- Configure DATABASE_URL and REDIS_URL in .env
- Run migrations: alembic upgrade head
- Start server: uvicorn app.main:app --reload
```

### Production Deployment Options

#### Option 1: Traditional VPS (DigitalOcean, Linode)
```
Stack:
- Ubuntu 22.04 LTS
- Nginx (reverse proxy, static files)
- Gunicorn (WSGI server, 4 workers)
- PostgreSQL (managed database)
- Redis (managed or self-hosted)
- Supervisor (process management)
- Let's Encrypt (SSL certificates)

Estimated Cost: $20-40/month
```

#### Option 2: Platform as a Service (Heroku, Render)
```
Stack:
- Heroku Dynos (web + worker)
- Heroku Postgres (hobby tier)
- Heroku Redis (hobby tier)
- Automatic SSL
- Git-based deployment

Estimated Cost: $25-50/month
```

#### Option 3: Containerized (Docker + Cloud)
```
Stack:
- Docker containers
- AWS ECS / Google Cloud Run
- RDS PostgreSQL
- ElastiCache Redis
- CloudFront CDN
- S3 for static files

Estimated Cost: $30-60/month
```

### Recommended: Render.com (Easiest Start)
```yaml
# render.yaml
services:
  - type: web
    name: piglist-web
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: piglist-db
          property: connectionString
      - key: REDIS_URL
        fromDatabase:
          name: piglist-redis
          property: connectionString

  - type: worker
    name: piglist-worker
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: celery -A app.celery worker

databases:
  - name: piglist-db
    databaseName: piglist
    plan: starter

  - name: piglist-redis
    plan: starter
```

### Scaling Considerations

#### Phase 1: MVP (0-100 users)
- Single web server
- Shared database
- Basic monitoring

#### Phase 2: Growth (100-1000 users)
- Multiple web workers
- Database connection pooling
- Redis caching layer
- CDN for static assets
- Application monitoring (Sentry)

#### Phase 3: Scale (1000+ users)
- Load balancer
- Database read replicas
- Separate Celery workers
- Advanced caching strategies
- Performance monitoring (New Relic)

### Monitoring & Logging
```python
# Application monitoring
- Sentry (error tracking)
- Logging (structured JSON logs)
- Health check endpoint (/health)
- Uptime monitoring (UptimeRobot)

# Metrics to track
- Response times
- Error rates
- Active users
- Gift scraping success rate
- WebSocket connections
```

### Backup Strategy
```
Database Backups:
- Automated daily backups (managed service)
- Point-in-time recovery
- 30-day retention

Redis Backups:
- RDB snapshots every 6 hours
- AOF for durability

User-uploaded Images:
- S3 versioning enabled
- Cross-region replication (optional)
```

### CI/CD Pipeline
```yaml
# GitHub Actions example
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: pytest
      
  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Render
        run: curl -X POST ${{ secrets.RENDER_DEPLOY_HOOK }}
```

---

## 11. Comprehensive Development Roadmap

This roadmap provides a detailed, step-by-step guide for developing, implementing, and testing all aspects of the Piglist project from start to finish. Each phase includes specific tasks, implementation details, testing requirements, and deliverables.

---

### Phase 0: Project Foundation (Week 1) ✅

#### 0.1 Development Environment Setup ✅
**Status**: Complete - Dev container is configured and operational

**Completed Tasks**:
- ✅ Initialize Git repository
- ✅ Set up VS Code Dev Container with Docker Compose
- ✅ Configure PostgreSQL 15, Redis 7, and Celery services
- ✅ Install all Python dependencies (FastAPI, SQLAlchemy, etc.)
- ✅ Configure VS Code extensions (Python, Black, Flake8, etc.)
- ✅ Set up GitHub CLI integration
- ✅ Configure Playwright with Chromium browser

**Verification**:
```bash
docker-compose ps  # All services running
pg_isready -h db -U piglist  # PostgreSQL ready
redis-cli -h redis ping  # Redis responding
python --version  # Python 3.11
```

**Deliverables**:
- ✅ Working dev container environment
- ✅ All services accessible (FastAPI, PostgreSQL, Redis, Celery, Flower)
- ✅ Complete documentation in PiglistArchitecture.md

#### 0.2 Project Structure & Configuration ✅
**Completed Tasks**:
- ✅ Review and finalize application directory structure
- ✅ Enhance configuration management with Pydantic Settings
- ✅ Update `.env.example` file with all required variables
- ✅ Configure structured logging system
- ✅ Set up comprehensive error handling middleware

**Implementation**:
```python
# app/core/config.py - Enhance existing configuration
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    APP_NAME: str = "Piglist"
    
    # Celery
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    
    # Optional Services
    SENTRY_DSN: Optional[str] = None
    EMAIL_HOST: Optional[str] = None
    EMAIL_PORT: Optional[int] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

**Testing**:
```bash
python -c "from app.core.config import settings; print(settings.DATABASE_URL)"
```

**Deliverables**:
- ✅ Enhanced configuration system
- ✅ Comprehensive `.env.example`
- ✅ Logging configuration
- ✅ Error handling middleware

**Implementation Notes:**
Created comprehensive error handling system with custom exception classes (`app/core/exceptions.py`) for different HTTP status codes. Implemented request ID middleware (`app/middleware/request_id.py`) that generates unique UUIDs for each request and adds X-Request-ID headers. Built error handler middleware (`app/middleware/error_handler.py`) that catches exceptions and returns structured JSON responses with request context. Configured structured JSON logging (`app/core/logging.py`) with custom formatter supporting extra fields like request_id and user_id. All middleware integrated into main application and tested with `/test/error` endpoint.

---

#### 0.3 Database Setup & Migrations ✅
**Completed Tasks**:
- ⏳ Initialize Alembic for database migrations (deferred to Phase 1)
- ⏳ Configure Alembic for async PostgreSQL (deferred to Phase 1)
- ✅ Create base SQLAlchemy models and session management
- ✅ Set up database connection pooling
- ✅ Create database health check function
- ⏳ Create initial migration structure (deferred to Phase 1)

**Implementation**:
```bash
# Initialize Alembic
alembic init alembic

# Edit alembic.ini to use async driver
sqlalchemy.url = postgresql+asyncpg://user:pass@localhost/dbname
```

```python
# app/db/session.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

**Testing**:
```bash
# Create and apply first migration
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head

# Verify tables created
psql -h db -U piglist -d piglist_dev -c "\dt"
```

**Deliverables**:
- ⏳ Alembic configured for async operations (deferred to Phase 1)
- ✅ Database connection working with pooling
- ⏳ Migration system functional (will be set up in Phase 1)
- ✅ Base models and session management

**Implementation Notes:**
Configured async SQLAlchemy engine (`app/db/base.py`) with production-ready connection pooling: pool_pre_ping for connection verification, pool_size=10 for persistent connections, max_overflow=20 for handling load spikes, pool_recycle=3600 to prevent stale connections, and pool_timeout=30 for connection acquisition. Created AsyncSessionLocal factory with expire_on_commit=False for better performance. Implemented get_db() dependency that yields async sessions with automatic commit/rollback handling. Added check_db_connection() health check function that tests connectivity with SELECT 1 query. Enhanced health endpoint to report database status. Alembic initialization intentionally deferred to Phase 1 for efficiency - will be initialized with User model so first migration contains actual schema.

---

### Phase 1: Core Authentication & User Management (Week 2)

#### 1.1 User Model & Authentication System
**Tasks**:
- [ ] Create User SQLAlchemy model with all fields
- [ ] Implement password hashing with Passlib/bcrypt
- [ ] Create Pydantic schemas for user operations
- [ ] Build user registration endpoint with validation
- [ ] Build user login endpoint with JWT generation
- [ ] Implement token refresh mechanism

**Implementation**: See detailed code in architecture document sections 4 and 12

**Testing Strategy**:
```python
# tests/test_auth.py
@pytest.mark.asyncio
async def test_user_registration_success(client: AsyncClient):
    response = await client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "SecurePass123!",
        "display_name": "Test User"
    })
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "test@example.com"

@pytest.mark.asyncio
async def test_user_registration_duplicate_email(client: AsyncClient):
    # Register first user
    await client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "SecurePass123!",
        "display_name": "Test User"
    })
    
    # Try to register again with same email
    response = await client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "DifferentPass123!",
        "display_name": "Another User"
    })
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_user_login_success(client: AsyncClient):
    # Register user first
    await client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "SecurePass123!",
        "display_name": "Test User"
    })
    
    # Login
    response = await client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "SecurePass123!"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

@pytest.mark.asyncio
async def test_user_login_invalid_credentials(client: AsyncClient):
    response = await client.post("/api/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "WrongPassword123!"
    })
    assert response.status_code == 401
```

**Deliverables**:
- [ ] User model with secure password storage
- [ ] Registration endpoint with email validation
- [ ] Login endpoint with JWT tokens
- [ ] Comprehensive authentication tests (>90% coverage)
- [ ] API documentation for auth endpoints

#### 1.2 Authentication Middleware & Protected Routes
**Tasks**:
- [ ] Create `get_current_user` dependency
- [ ] Implement token validation and refresh
- [ ] Add Redis session management
- [ ] Create logout functionality
- [ ] Build user profile endpoints

**Testing Strategy**:
```python
@pytest.mark.asyncio
async def test_protected_route_without_token(client: AsyncClient):
    response = await client.get("/api/users/me")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_protected_route_with_valid_token(client: AsyncClient, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = await client.get("/api/users/me", headers=headers)
    assert response.status_code == 200
    assert "email" in response.json()

@pytest.mark.asyncio
async def test_protected_route_with_expired_token(client: AsyncClient):
    expired_token = create_expired_token()
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = await client.get("/api/users/me", headers=headers)
    assert response.status_code == 401
```

**Deliverables**:
- [ ] Authentication middleware functional
- [ ] Protected routes working correctly
- [ ] Session management with Redis
- [ ] Token refresh mechanism
- [ ] Integration tests for auth flow

---

### Phase 2: Group Management System (Week 3)

#### 2.1 Group Models & Basic Operations
**Tasks**:
- [ ] Create Group and GroupMember models
- [ ] Implement unique invite code generation
- [ ] Build group creation endpoint
- [ ] Build join group endpoint (via invite code)
- [ ] Create group listing endpoint
- [ ] Implement group details endpoint

**Testing Strategy**:
```python
@pytest.mark.asyncio
async def test_create_group(client: AsyncClient, auth_headers):
    response = await client.post("/api/groups",
        headers=auth_headers,
        json={"name": "Smith Family"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Smith Family"
    assert "invite_code" in data
    assert len(data["invite_code"]) >= 16  # Secure invite code

@pytest.mark.asyncio
async def test_join_group_with_valid_invite(client: AsyncClient, other_user_headers, group_invite_code):
    response = await client.post(f"/api/groups/join/{group_invite_code}",
        headers=other_user_headers
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Successfully joined group"

@pytest.mark.asyncio
async def test_join_group_with_invalid_invite(client: AsyncClient, auth_headers):
    response = await client.post("/api/groups/join/invalid_code",
        headers=auth_headers
    )
    assert response.status_code == 404
```

**Deliverables**:
- [ ] Group and GroupMember models
- [ ] Group CRUD operations
- [ ] Secure invite code system
- [ ] Group membership management
- [ ] Comprehensive group tests

#### 2.2 Group Authorization & Admin Features
**Tasks**:
- [ ] Implement `require_group_member` dependency
- [ ] Implement `require_group_admin` dependency
- [ ] Build group settings management (admin only)
- [ ] Implement lock date functionality
- [ ] Create member management endpoints (add/remove/promote)

**Testing Strategy**:
```python
@pytest.mark.asyncio
async def test_non_member_cannot_access_group(client: AsyncClient, auth_headers):
    response = await client.get("/api/groups/1", headers=auth_headers)
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_member_can_view_group(client: AsyncClient, member_headers, group_id):
    response = await client.get(f"/api/groups/{group_id}", headers=member_headers)
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_non_admin_cannot_modify_settings(client: AsyncClient, member_headers, group_id):
    response = await client.put(f"/api/groups/{group_id}/settings",
        headers=member_headers,
        json={"lock_date": "2024-12-25T00:00:00"}
    )
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_admin_can_modify_settings(client: AsyncClient, admin_headers, group_id):
    response = await client.put(f"/api/groups/{group_id}/settings",
        headers=admin_headers,
        json={"lock_date": "2024-12-25T00:00:00"}
    )
    assert response.status_code == 200
```

**Deliverables**:
- [ ] Role-based access control (RBAC)
- [ ] Admin-only endpoints protected
- [ ] Group settings management
- [ ] Lock date enforcement
- [ ] Authorization tests

---

### Phase 3: Category & Piglist Management (Week 4)

#### 3.1 Category System
**Tasks**:
- [ ] Create Category model
- [ ] Implement category CRUD operations (admin only)
- [ ] Add spending limit validation logic
- [ ] Create category ordering system
- [ ] Build category assignment for gifts

**Testing Strategy**:
```python
@pytest.mark.asyncio
async def test_create_category(client: AsyncClient, admin_headers, group_id):
    response = await client.post(f"/api/groups/{group_id}/categories",
        headers=admin_headers,
        json={
            "name": "From Parents",
            "spending_limit": 200.00,
            "max_item_price": 50.00,
            "display_order": 1
        }
    )
    assert response.status_code == 201
    assert response.json()["name"] == "From Parents"

@pytest.mark.asyncio
async def test_spending_limit_enforcement(client: AsyncClient, auth_headers, category_id):
    # Add gifts totaling $180
    for i in range(3):
        await client.post("/api/gifts",
            headers=auth_headers,
            json={
                "category_id": category_id,
                "title": f"Gift {i}",
                "price": 60.00,
                "url": f"https://example.com/gift{i}"
            }
        )
    
    # Try to add gift that exceeds $200 limit
    response = await client.post("/api/gifts",
        headers=auth_headers,
        json={
            "category_id": category_id,
            "title": "Expensive Gift",
            "price": 30.00,  # Would make total $210
            "url": "https://example.com/expensive"
        }
    )
    assert response.status_code == 400
    assert "spending limit" in response.json()["detail"].lower()
```

**Deliverables**:
- [ ] Category model and CRUD
- [ ] Spending limit enforcement
- [ ] Max item price validation
- [ ] Category ordering
- [ ] Category tests

#### 3.2 Piglist System
**Tasks**:
- [ ] Create Piglist model (one per user per group)
- [ ] Implement automatic piglist creation on group join
- [ ] Build piglist viewing endpoints
- [ ] Add filtering by category and user
- [ ] Implement privacy rules (can't see own gift viewers)

**Testing Strategy**:
```python
@pytest.mark.asyncio
async def test_piglist_auto_created_on_group_join(client: AsyncClient, auth_headers, group_invite_code):
    # Join group
    await client.post(f"/api/groups/join/{group_invite_code}", headers=auth_headers)
    
    # Check piglist was created
    response = await client.get("/api/piglists/my", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) > 0

@pytest.mark.asyncio
async def test_cannot_view_own_gift_viewers(client: AsyncClient, auth_headers, own_gift_id):
    response = await client.get(f"/api/gifts/{own_gift_id}/viewers", headers=auth_headers)
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_can_view_others_gift_viewers(client: AsyncClient, auth_headers, other_gift_id):
    response = await client.get(f"/api/gifts/{other_gift_id}/viewers", headers=auth_headers)
    assert response.status_code == 200
```

**Deliverables**:
- [ ] Piglist model and endpoints
- [ ] One piglist per user per group constraint
- [ ] Privacy rules enforced
- [ ] Filtering and sorting
- [ ] Piglist tests

---

### Phase 4: Gift Management & Web Scraping (Weeks 5-6)

#### 4.1 Gift Model & Manual Entry
**Tasks**:
- [ ] Create Gift model with JSONB metadata
- [ ] Implement manual gift creation
- [ ] Add gift editing (own gifts only)
- [ ] Add gift deletion (own gifts only)
- [ ] Create gift detail view
- [ ] Implement gift purchase tracking

**Deliverables**:
- [ ] Gift model with all fields
- [ ] Gift CRUD operations
- [ ] Ownership validation
- [ ] Purchase tracking
- [ ] Gift management tests

#### 4.2 Web Scraping Service
**Tasks**:
- [ ] Create scraping service with BeautifulSoup4
- [ ] Implement Open Graph tag extraction
- [ ] Add Schema.org markup parsing
- [ ] Create Playwright fallback for JS sites
- [ ] Implement price parsing with price-parser
- [ ] Add image URL extraction

**Implementation**: See detailed scraping service code in architecture document section 6

**Testing Strategy**:
```python
@pytest.mark.asyncio
async def test_scrape_amazon_product():
    scraper = GiftScraperService()
    result = await scraper.scrape_url("https://www.amazon.com/dp/B08N5WRWNW")
    assert result['scrape_status'] == 'success'
    assert result['title']
    assert result['price'] is not None
    assert result['image_url']

@pytest.mark.asyncio
async def test_scrape_with_open_graph():
    scraper = GiftScraperService()
    result = await scraper.scrape_url("https://example.com/product-with-og-tags")
    assert result['title']
    assert result['description']

@pytest.mark.asyncio
async def test_scrape_invalid_url():
    scraper = GiftScraperService()
    result = await scraper.scrape_url("https://invalid-url-404.com")
    assert result['scrape_status'] == 'failed'
```

**Deliverables**:
- [ ] Web scraping service
- [ ] Multiple extraction strategies
- [ ] Price parsing
- [ ] Image extraction
- [ ] Scraping tests with real URLs

#### 4.3 Async Scraping with Celery
**Tasks**:
- [ ] Configure Celery with Redis broker
- [ ] Create async scraping task
- [ ] Implement retry logic with exponential backoff
- [ ] Add scraping status tracking
- [ ] Create manual fallback UI for failed scrapes
- [ ] Set up Flower for task monitoring

**Implementation**: See Celery configuration in architecture document

**Testing Strategy**:
```python
@pytest.mark.asyncio
async def test_async_scraping_task(celery_worker):
    gift_id = 1
    url = "https://example.com/product"
    
    task = scrape_gift_url.delay(gift_id, url)
    result = task.get(timeout=30)
    
    assert result['scrape_status'] in ['success', 'failed']
    
    # Verify gift was updated in database
    gift = await get_gift_by_id(gift_id)
    assert gift.scrape_status == result['scrape_status']
```

**Deliverables**:
- [ ] Celery configured and running
- [ ] Async scraping tasks
- [ ] Retry logic implemented
- [ ] Task monitoring with Flower
- [ ] Celery tests

---

### Phase 5: Real-Time Presence System (Week 7)

#### 5.1 Socket.IO Integration
**Tasks**:
- [ ] Set up python-socketio with FastAPI
- [ ] Create WebSocket connection handlers
- [ ] Implement room-based messaging
- [ ] Add connection/disconnection handlers
- [ ] Create client-side Socket.IO integration

**Deliverables**:
- [ ] Socket.IO integrated with FastAPI
- [ ] Connection handling
- [ ] Room management
- [ ] Basic event system
- [ ] Connection tests

#### 5.2 Gift Presence Tracking
**Tasks**:
- [ ] Create GiftPresence model
- [ ] Implement join/leave gift view events
- [ ] Add heartbeat mechanism (30s client, 60s timeout)
- [ ] Create presence cleanup Celery task
- [ ] Store presence data in Redis with TTL
- [ ] Build real-time viewer count updates

**Implementation**: See detailed presence service code in architecture document section 5

**Testing Strategy**:
```python
@pytest.mark.asyncio
async def test_presence_tracking():
    sio1 = socketio.AsyncClient()
    sio2 = socketio.AsyncClient()
    
    await sio1.connect('http://localhost:8000')
    await sio2.connect('http://localhost:8000')
    
    # User 1 joins gift view
    await sio1.emit('join_gift_view', {'gift_id': 1, 'user_id': 1})
    await asyncio.sleep(0.5)
    
    # User 2 should see user 1 is viewing
    viewers = []
    @sio2.on('gift_viewers_updated')
    def handle_viewers(data):
        viewers.append(data)
    
    await asyncio.sleep(1)
    assert len(viewers) > 0
    assert viewers[0]['viewer_count'] == 1
    
    await sio1.disconnect()
    await sio2.disconnect()

@pytest.mark.asyncio
async def test_heartbeat_timeout():
    # Join gift view
    # Stop sending heartbeats
    # Wait 60+ seconds
    # Verify presence was cleared
    pass
```

**Deliverables**:
- [ ] Real-time presence tracking
- [ ] Redis-based presence storage
- [ ] Heartbeat mechanism
- [ ] Automatic cleanup
- [ ] Real-time tests

---

### Phase 6: Frontend Development with HTMX (Weeks 8-9)

#### 6.1 Base Templates & Layout
**Tasks**:
- [ ] Set up Jinja2 template system
- [ ] Create base layout with Tailwind CSS
- [ ] Add HTMX and Alpine.js CDN links
- [ ] Create navigation components
- [ ] Implement responsive design
- [ ] Add flash message system

**Deliverables**:
- [ ] Base template system
- [ ] Tailwind CSS integrated
- [ ] HTMX and Alpine.js setup
- [ ] Responsive navigation
- [ ] Template tests

#### 6.2 Authentication Pages
**Tasks**:
- [ ] Create login page with HTMX form
- [ ] Create registration page
- [ ] Add client-side validation
- [ ] Implement error handling and display
- [ ] Add success notifications
- [ ] Create password reset flow (optional)

**Deliverables**:
- [ ] Login and registration pages
- [ ] HTMX form handling
- [ ] Client-side validation
- [ ] Error messages
- [ ] UI tests

#### 6.3 Dashboard & Group Views
**Tasks**:
- [ ] Create user dashboard with group cards
- [ ] Build group overview page
- [ ] Implement piglist grid view
- [ ] Add gift cards with status indicators
- [ ] Create modals with Alpine.js
- [ ] Add filtering and sorting

**Deliverables**:
- [ ] Dashboard with group cards
- [ ] Group overview page
- [ ] Modal dialogs
- [ ] HTMX partial updates
- [ ] Frontend tests

#### 6.4 Gift Management UI
**Tasks**:
- [ ] Create gift addition form with URL input
- [ ] Build gift grid/list view
- [ ] Add gift detail modal
- [ ] Implement purchase button
- [ ] Show real-time presence indicators
- [ ] Add gift editing interface

**Implementation**: See detailed HTML/JavaScript code in architecture document section 8

**Deliverables**:
- [ ] Gift addition form
- [ ] Gift cards with images
- [ ] Real-time presence indicators
- [ ] Purchase functionality
- [ ] Gift detail views

---

### Phase 7: Testing & Quality Assurance (Week 10)

#### 7.1 Unit Tests
**Tasks**:
- [ ] Write tests for all models
- [ ] Test all service functions
- [ ] Test authentication flows
- [ ] Test authorization rules
- [ ] Achieve >80% code coverage

**Testing Commands**:
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_auth.py -v

# Run tests matching pattern
pytest -k "test_user" -v
```

**Deliverables**:
- [ ] Comprehensive unit tests
- [ ] >80% code coverage
- [ ] Coverage report
- [ ] Test documentation

#### 7.2 Integration Tests
**Tasks**:
- [ ] Test complete user flows
- [ ] Test group creation and joining
- [ ] Test gift lifecycle (create, scrape, purchase)
- [ ] Test real-time features
- [ ] Test error scenarios

**Deliverables**:
- [ ] End-to-end integration tests
- [ ] Multi-user scenarios
- [ ] Error handling tests
- [ ] Integration test suite

#### 7.3 Performance Testing
**Tasks**:
- [ ] Load test API endpoints with Locust
- [ ] Test concurrent WebSocket connections
- [ ] Optimize slow database queries
- [ ] Add missing database indexes
- [ ] Profile slow endpoints

**Performance Targets**:
- API response time: <200ms (p95)
- WebSocket latency: <100ms
- Database queries: <50ms
- Concurrent users: 100+

**Deliverables**:
- [ ] Performance benchmarks
- [ ] Optimized queries
- [ ] Load test results
- [ ] Performance report

---

### Phase 8: Security & Compliance (Week 11)

#### 8.1 Security Hardening
**Tasks**:
- [ ] Implement rate limiting with slowapi
- [ ] Add CSRF protection for forms
- [ ] Configure secure headers
- [ ] Set up CORS properly
- [ ] Implement input sanitization
- [ ] Add SQL injection prevention checks
- [ ] Configure HTTPS/TLS

**Implementation**: See security configuration in architecture document section 9

**Deliverables**:
- [ ] Rate limiting implemented
- [ ] Security headers configured
- [ ] CORS properly set up
- [ ] Input validation
- [ ] Security tests passing

#### 8.2 Security Audit
**Tasks**:
- [ ] Run OWASP ZAP scan
- [ ] Check for SQL injection vulnerabilities
- [ ] Test XSS prevention
- [ ] Verify CSRF protection
- [ ] Review authentication flows
- [ ] Check for sensitive data exposure
- [ ] Test authorization boundaries

**Deliverables**:
- [ ] Security audit report
- [ ] Vulnerabilities fixed
- [ ] Security documentation
- [ ] Penetration test results

---

### Phase 9: Deployment & DevOps (Week 12)

#### 9.1 Production Configuration
**Tasks**:
- [ ] Create production Dockerfile
- [ ] Set up environment variables
- [ ] Configure production database (managed PostgreSQL)
- [ ] Set up Redis for production
- [ ] Configure Celery workers
- [ ] Set up logging and monitoring

**Implementation**: See deployment configuration in architecture document section 10

**Deliverables**:
- [ ] Production Docker configuration
- [ ] Environment variables documented
- [ ] Production-ready setup
- [ ] Deployment guide

#### 9.2 CI/CD Pipeline
**Tasks**:
- [ ] Set up GitHub Actions workflow
- [ ] Configure automated testing
- [ ] Add linting and formatting checks
- [ ] Set up automated deployment
- [ ] Configure staging environment
- [ ] Add deployment notifications

**Deliverables**:
- [ ] CI/CD pipeline configured
- [ ] Automated testing on PRs
- [ ] Automated deployment
- [ ] Staging environment

#### 9.3 Monitoring & Logging
**Tasks**:
- [ ] Set up Sentry for error tracking
- [ ] Configure structured logging
- [ ] Set up health check endpoints
- [ ] Add performance monitoring
- [ ] Create alerting rules
- [ ] Set up uptime monitoring

**Deliverables**:
- [ ] Error tracking with Sentry
- [ ] Structured logging
- [ ] Health check endpoints
- [ ] Monitoring dashboard
- [ ] Alert configuration

---

### Phase 10: Documentation & Launch (Week 13)

#### 10.1 Documentation
**Tasks**:
- [ ] Write comprehensive API documentation
- [ ] Create user guide with screenshots
- [ ] Document deployment process
- [ ] Write developer setup guide
- [ ] Create troubleshooting guide
- [ ] Document all environment variables

**Deliverables**:
- [ ] Complete API documentation
- [ ] User manual
- [ ] Developer documentation
- [ ] Deployment guide
- [ ] Troubleshooting guide

#### 10.2 Beta Testing
**Tasks**:
- [ ] Recruit 5-10 beta testers
- [ ] Create feedback form
- [ ] Monitor usage and errors
- [ ] Fix critical bugs
- [ ] Gather feature requests
- [ ] Conduct user interviews

**Deliverables**:
- [ ] Beta testing completed
- [ ] Critical bugs fixed
- [ ] User feedback collected
- [ ] Feature backlog created

#### 10.3 Launch Preparation
**Tasks**:
- [ ] Final security review
- [ ] Performance optimization
- [ ] Create backup strategy
- [ ] Set up monitoring alerts
- [ ] Prepare support documentation
- [ ] Create marketing materials

**Deliverables**:
- [ ] Production-ready application
- [ ] Backup and recovery plan
- [ ] Support documentation
- [ ] Marketing materials

#### 10.4 Launch
**Tasks**:
- [ ] Deploy to production
- [ ] Monitor for issues (24/7 for first week)
- [ ] Respond to user feedback
- [ ] Create launch announcement
- [ ] Share on social media
- [ ] Monitor analytics

**Deliverables**:
- [ ] Live production application
- [ ] Launch announcement
- [ ] Initial user base
- [ ] Launch metrics

---

### Post-Launch: Maintenance & Enhancements

#### Ongoing Tasks (Continuous)
- [ ] Monitor application performance
- [ ] Respond to user support requests
- [ ] Fix bugs as reported
- [ ] Regular security updates
- [ ] Database backups and maintenance
- [ ] Dependency updates
- [ ] Performance optimization

#### Future Enhancements (Backlog)
- [ ] Mobile app development (React Native/Flutter)
- [ ] Amazon wishlist import integration
- [ ] Email notifications system
- [ ] Gift recommendations based on history
- [ ] Social sharing features
- [ ] Multi-language support (i18n)
- [ ] Advanced analytics for admins
- [ ] Gift price tracking over time
- [ ] Bulk gift import
- [ ] Gift exchange matching algorithm

---

### Development Timeline Summary

| Phase | Duration | Key Deliverables | Status |
|-------|----------|------------------|--------|
| Phase 0: Foundation | Week 1 | Dev environment, project structure | ✅ Complete |
| Phase 1: Authentication | Week 2 | User auth, JWT, protected routes | 🔄 Next |
| Phase 2: Groups | Week 3 | Group management, invites, roles | ⏳ Pending |
| Phase 3: Categories | Week 4 | Categories, piglists, limits | ⏳ Pending |
| Phase 4: Gifts | Weeks 5-6 | Gift CRUD, web scraping, Celery | ⏳ Pending |
| Phase 5: Real-time | Week 7 | Socket.IO, presence tracking | ⏳ Pending |
| Phase 6: Frontend | Weeks 8-9 | HTMX UI, templates, interactions | ⏳ Pending |
| Phase 7: Testing | Week 10 | Unit, integration, performance tests | ⏳ Pending |
| Phase 8: Security | Week 11 | Security hardening, audit | ⏳ Pending |
| Phase 9: Deployment | Week 12 | Production setup, CI/CD | ⏳ Pending |
| Phase 10: Launch | Week 13 | Documentation, beta, launch | ⏳ Pending |

**Total Estimated Time**: 13 weeks (3 months) for full-time development

**For Part-Time Development**: 20-26 weeks (5-6 months)

**Current Progress**: Phase 0 complete, ready to begin Phase 1

---

### Success Metrics

**Development Metrics**:
- Code coverage: >80%
- API response time: <200ms (p95)
- Test pass rate: 100%
- Security vulnerabilities: 0 critical/high

**Launch Metrics**:
- Initial users: 50+
- User retention (week 1): >70%
- Critical bugs: <5
- Uptime: >99.5%

**Post-Launch Metrics** (Month 1):
- Active users: 100+
- Groups created: 50+
- Gifts added: 500+
- User satisfaction: >4.0/5.0

---

## 12. Required Python Packages

### Core Dependencies
```txt
# requirements.txt

# Web Framework
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6

# Database
sqlalchemy[asyncio]==2.0.25
asyncpg==0.29.0
alembic==1.13.1

# Redis & Caching
redis==5.0.1
aioredis==2.0.1

# Web Scraping
beautifulsoup4==4.12.2
httpx==0.26.0
playwright==1.40.0
price-parser==0.3.4
lxml==4.9.3

# Task Queue
celery==5.3.4
flower==2.0.1

# Real-time (Socket.IO for FastAPI)
python-socketio==5.10.0
python-engineio==4.8.0

# Templates
jinja2==3.1.3

# Security & Authentication
passlib[bcrypt]==1.7.4
python-jose[cryptography]==3.3.0
slowapi==0.1.9

# Image Processing
Pillow==10.1.0

# Utilities
python-dotenv==1.0.0
email-validator==2.1.0
pydantic==2.5.3
pydantic-settings==2.1.0

# Production Server
gunicorn==21.2.0

# Monitoring (optional)
sentry-sdk[fastapi]==1.39.2
```

### Development Dependencies

```txt
# requirements-dev.txt

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
httpx==0.26.0  # For testing FastAPI endpoints

# Code Quality
black==23.12.0
flake8==6.1.0
isort==5.13.2
mypy==1.7.1

# Development Tools
ipython==8.18.1
ipdb==0.13.13
```

**Key Additions**:
- **flower**: Web-based monitoring tool for Celery
- **pytest-asyncio**: For testing async code
- **isort**: Import sorting
- **ipython/ipdb**: Interactive debugging tools

---

## 13. Key Implementation Questions to Consider

### Business Logic Questions
1. **Gift Deletion**: Can users delete gifts after someone has viewed them?
2. **Purchase Reversal**: Can someone "un-purchase" a gift if they change their mind?
3. **Category Changes**: What happens to existing gifts if a category is deleted?
4. **Lock Date Behavior**: Can admins extend the lock date after it's passed?
5. **Group Deletion**: What happens to all piglists if a group is deleted?
6. **Duplicate Gifts**: Should the system detect if multiple people add the same URL?

### Technical Questions
1. **Image Storage**: Local filesystem or cloud storage (S3)?
2. **Email Service**: Which provider (SendGrid, Mailgun, AWS SES)?
3. **Domain Name**: What domain will you use?
4. **SSL Certificate**: Let's Encrypt or paid certificate?
5. **Analytics**: Do you want usage analytics (Google Analytics, Plausible)?
6. **Mobile App**: Future consideration for native mobile apps?

### UX Questions
1. **Notifications**: Email notifications for purchases, new gifts, etc.?
2. **Gift Sorting**: How should gifts be sorted (price, date added, category)?
3. **Search**: Should users be able to search across all piglists?
4. **Filters**: What filtering options (price range, category, status)?
5. **Gift Notes**: Can users add private notes to gifts they're considering?
6. **Wishlist Import**: Import from Amazon/other wishlists?

---

## 14. Next Steps

### Immediate Actions
1. **Review this document** and provide feedback on any sections
2. **Answer the key questions** in Section 13
3. **Choose your deployment platform** (Render, Heroku, VPS)
4. **Set up development environment**:
   ```bash
   # Create project structure
   mkdir piglist && cd piglist
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

5. **Initialize database**:
   ```bash
   # Create PostgreSQL database
   createdb piglist_dev
   
   # Run migrations
   flask db init
   flask db migrate -m "Initial schema"
   flask db upgrade
   ```

### Decision Points
Before starting development, decide on:
- [ ] Deployment platform
- [ ] Domain name
- [ ] Image storage solution
- [ ] Email service provider
- [ ] Analytics requirements
- [ ] Mobile app timeline

---

## 15. Estimated Timeline & Costs

### Development Time
- **Solo Developer**: 10-14 weeks (part-time)
- **Full-time**: 6-8 weeks
- **With Team**: 4-6 weeks

### Ongoing Costs (Monthly)
- **Hosting**: $20-50
- **Database**: $10-25 (included in some platforms)
- **Redis**: $10-20 (included in some platforms)
- **Domain**: $1-2/month ($12-24/year)
- **Email Service**: $0-10 (free tier usually sufficient)
- **Monitoring**: $0-20 (free tiers available)
- **Total**: $30-100/month

### One-Time Costs
- **Domain Registration**: $12-24/year
- **SSL Certificate**: $0 (Let's Encrypt)
- **Development Tools**: $0 (all open source)

---