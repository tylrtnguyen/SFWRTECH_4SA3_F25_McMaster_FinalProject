# Job Matching & Analysis API

A FastAPI-based backend application for job matching, fraud analysis, and payment management with integration to third-party APIs. Features user authentication (traditional email/password and OAuth), secure payment processing, and intelligent job analysis.

## Technology Stack

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.113.0-green.svg)
![Docker](https://img.shields.io/badge/Docker-28.4.0-blue.svg)
![Supabase](https://img.shields.io/badge/Supabase-Database-darkblue.svg)
![Stripe](https://img.shields.io/badge/Stripe-Payment-purple.svg)

## Features

- **User Authentication**: Traditional email/password and OAuth (Google, LinkedIn) authentication with JWT tokens
- **User Management**: Complete user account management with profile updates and credit tracking
- **Job Fraud Analysis**: Job fraud detection using Ruvia Trust API
- **Secure Payment Processing**: Stripe API integration for credit purchases with webhook support
- **Job Aggregation**: Job listings from LinkedIn and Indeed feeds
- **Intelligent Job Matching**: Multiple matching strategies (salary, location, skills, balanced)
- **Real-time Updates**: Observer pattern for live updates on credits, scores, and analysis completion
- **Modular Architecture**: Design patterns (Chain of Responsibility, Strategy, Observer, Singleton)

## Design Patterns Implemented

### Chain of Responsibility Pattern
Modular job analysis pipelines for running detection, scoring, and suggestions in order. The pipeline processes job postings through multiple handlers:
- Fraud Detection Handler
- Job Scoring Handler
- Suggestion Handler

### Strategy Pattern
Switch job matching algorithms based on user-selected priorities/goals:
- Salary Priority Strategy
- Location Priority Strategy
- Skills Match Strategy
- Balanced Strategy

### Observer Pattern
Live updates to widget/dashboard when scores or credits change. Observers can subscribe to events:
- Credits Changed
- Score Updated
- Job Analysis Complete
- Payment Complete

### Singleton Pattern
Manages shared DB/API/Stripe session for user accounts:
- DatabaseManager: Single database connection pool
- StripeManager: Single Stripe client instance
- APIConnectionManager: Shared HTTP client for API calls

## Project Structure

```
project/backend/
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker configuration
├── .env.example           # Environment variables template
├── app/
│   ├── core/
│   │   ├── config.py      # Application configuration
│   │   └── singleton.py   # Singleton pattern implementations
│   ├── models/
│   │   └── schemas.py     # Pydantic models
│   ├── patterns/
│   │   ├── chain_of_responsibility.py  # Chain of Responsibility
│   │   ├── strategy.py                 # Strategy pattern
│   │   └── observer.py                 # Observer pattern
│   ├── routers/
│   │   ├── users.py       # User authentication and management endpoints
│   │   ├── jobs.py        # Job matching endpoints
│   │   ├── payments.py    # Payment endpoints
│   │   └── analysis.py    # Job analysis endpoints
│   ├── core/
│   │   ├── auth.py        # Authentication utilities (JWT, password hashing)
│   │   └── dependencies.py # FastAPI dependencies
│   └── services/
│       ├── ruvia_service.py              # Ruvia Trust API integration
│       ├── stripe_service.py             # Stripe API integration
│       ├── oauth_service.py              # OAuth authentication (Google, LinkedIn)
│       └── job_aggregation_service.py    # LinkedIn/Indeed integration
```

## Installation

### Prerequisites

- Python 3.12 or higher
- Docker (optional)

### Local Development

1. Clone the repository
2. Navigate to the backend directory:
   ```bash
   cd project/backend
   ```

3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Create a `.env` file from `.env.example`:
   ```bash
   cp .env.example .env
   ```

6. Update `.env` with your API keys and configuration:
   - Supabase database URL and API key
   - Stripe API keys and webhook secret
   - Ruvia Trust API key
   - LinkedIn API key
   - Indeed API key
   - OAuth credentials (Google, LinkedIn)
   - JWT secret key

7. Run the application:
   ```bash
   uvicorn main:app --reload
   ```

The API will be available at `http://localhost:8000`

### Docker Deployment

1. Build the Docker image:
   ```bash
   cd project/backend
   docker build -t job-matching-api .
   ```

2. Run the container:
   ```bash
   docker run -p 8000:8000 --env-file .env job-matching-api
   ```

## API Endpoints

### Users

#### Authentication
- `POST /api/v1/users/register` - Register a new user with email/password
  - **Request Body**: `{ "email": "user@example.com", "password": "SecurePass123!" }`
  - **Validation**: 
    - Email must be valid format
    - Password must be at least 8 characters with 1 uppercase, 1 number, and 1 special character
  - **Response**: User details with 201 status code
  - **Error Format**: `{ "status_code": 422, "error_message": "...", "error_type": "email_validation_error" | "password_validation_error" }`

- `POST /api/v1/users/login` - Authenticate user with email/password
  - **Request Body**: `{ "email": "user@example.com", "password": "SecurePass123!" }`
  - **Response**: JWT access token with expiry time

- `POST /api/v1/users/oauth/login` - Authenticate user with OAuth provider (Google or LinkedIn)
  - **Request Body**: `{ "provider": "google" | "linkedin", "access_token": "...", "oauth_id": "..." }`
  - **Response**: JWT access token with expiry time

#### User Management
- `GET /api/v1/users/me` - Get current user profile (requires authentication)
- `PUT /api/v1/users/me` - Update current user profile (requires authentication)
- `DELETE /api/v1/users/me` - Delete current user account (requires authentication)
- `GET /api/v1/users/{user_id}` - Get user by ID (requires authentication)

### Jobs

- `POST /api/v1/jobs/match` - Match jobs based on user preferences
- `GET /api/v1/jobs/aggregate` - Aggregate jobs from LinkedIn and Indeed

### Payments

- `POST /api/v1/payments/intent` - Create Stripe payment intent for credit purchase
  - **Request Body**: `{ "user_id": "uuid", "amount": 999, "credits": 100 }`
  - **Credit Packages**: 
    - 100 credits for $9.99 (999 cents)
    - 500 credits for $39.99 (3999 cents)
    - 1000 credits for $69.99 (6999 cents)
  - **Response**: Payment intent with client secret for Stripe checkout

- `POST /api/v1/payments/webhook` - Handle Stripe webhook events
  - **Headers**: `stripe-signature` for webhook verification
  - **Processes**: `payment_intent.succeeded` events to update user credits

- `GET /api/v1/payments/user/{user_id}/credits` - Get user credit balance

### Analysis

- `POST /api/v1/analysis/analyze` - Analyze job posting for fraud and scoring (requires authentication)
  - **Request Body**: `{ "job_id": "uuid", "analysis_type": "api_based" }`
  - **Uses**: Chain of Responsibility pattern (Fraud Detection → Job Scoring → Suggestion Generation)
  - **Cost**: 2 credits per analysis

- `GET /api/v1/analysis/history/{user_id}` - Get analysis history (requires authentication)

### Health

- `GET /health` - Health check endpoint
- `GET /` - Root endpoint with API information

## API Documentation

Once the server is running, access the interactive API documentation:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Third-Party API Integrations

### Ruvia Trust API
Job fraud analysis service that detects fraudulent job postings based on various indicators.

### Stripe API
Secure payment processing and credit management system for purchasing analysis credits.

### LinkedIn/Indeed Feeds
Job aggregation from multiple sources to provide comprehensive job listings.

## Environment Variables

See `.env.example` for all required environment variables:

### Database (Supabase)
- `SUPABASE_DATABASE_URL` - Supabase project URL
- `SUPABASE_DATABASE_API_KEY` - Supabase anon/service role key

### Stripe
- `STRIPE_SECRET_KEY` - Stripe secret API key
- `STRIPE_PUBLISHABLE_KEY` - Stripe publishable API key
- `STRIPE_WEBHOOK_SECRET` - Stripe webhook signing secret
- `STRIPE_PRICE_ID_100` - Stripe Price ID for 100 credits package (optional)
- `STRIPE_PRICE_ID_500` - Stripe Price ID for 500 credits package (optional)
- `STRIPE_PRICE_ID_1000` - Stripe Price ID for 1000 credits package (optional)

### Authentication
- `SECRET_KEY` - JWT secret key for token signing (use a strong random string)
- `ALGORITHM` - JWT algorithm (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - JWT token expiry time (default: 30)

### OAuth
- `GOOGLE_CLIENT_ID` - Google OAuth client ID
- `GOOGLE_CLIENT_SECRET` - Google OAuth client secret
- `LINKEDIN_CLIENT_ID` - LinkedIn OAuth client ID
- `LINKEDIN_CLIENT_SECRET` - LinkedIn OAuth client secret
- `OAUTH_REDIRECT_URI` - OAuth redirect URI

### Third-Party APIs
- `RUVIA_TRUST_API_KEY` - Ruvia Trust API key
- `LINKEDIN_API_KEY` - LinkedIn API key
- `INDEED_API_KEY` - Indeed API key

## Database

The application uses **Supabase** (PostgreSQL) as the database. The database schema includes the following tables:

- `users` - User accounts with email, OAuth info, credits, and account status
- `credit_transactions` - Credit purchase and usage transaction records
- `jobs` - Job postings from various sources (LinkedIn, Indeed, manual)
- `job_analyses` - Job fraud analysis results and scores
- `job_matches` - Job matching results with scores and strategies
- `job_bookmarks` - User bookmarked jobs
- `logs` - Application logs with user actions and system events

### Database Setup

1. Create a Supabase project at [supabase.com](https://supabase.com)
2. Get your project URL and API key from the Supabase dashboard
3. Run the migration script to create tables:
   ```bash
   # Apply migration using Supabase SQL editor or CLI
   # See migrations/001_create_tables.sql
   ```
4. Update `.env` with your Supabase credentials

## Design Pattern Usage Examples

### Chain of Responsibility
```python
pipeline = JobAnalysisPipeline()
pipeline.add_handler(FraudDetectionHandler())
pipeline.add_handler(JobScoringHandler())
pipeline.add_handler(SuggestionHandler())
result = await pipeline.process(request)
```

### Strategy Pattern
```python
strategy = JobMatchingContext.get_strategy_by_name("salary")
context = JobMatchingContext(strategy)
matches = await context.execute_matching(user_preferences, jobs)
```

### Observer Pattern
```python
observer = CreditsObserver(user_id=1)
await user_event_subject.attach(observer)
await user_event_subject.credits_changed(user_id=1, old_credits=0, new_credits=100)
```

### Singleton Pattern
```python
db_manager = DatabaseManager.get_instance()
stripe_manager = StripeManager.get_instance()
api_manager = APIConnectionManager.get_instance()
```

## Authentication

### Traditional Authentication

Users can register with email and password. Password requirements:
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 number
- At least 1 special character

### OAuth Authentication

Users can authenticate using:
- **Google OAuth**: Sign in with Google account
- **LinkedIn OAuth**: Sign in with LinkedIn account

### JWT Tokens

After successful authentication, users receive a JWT access token:
- Token type: Bearer
- Default expiry: 30 minutes (configurable)
- Include in requests: `Authorization: Bearer <token>`

### Protected Endpoints

Most endpoints require authentication. Include the JWT token in the Authorization header:
```bash
curl -H "Authorization: Bearer <your_token>" http://localhost:8000/api/v1/users/me
```

## Credit System

Users start with 50 free credits. Credits can be purchased through Stripe:

- **100 Credits**: $9.99
- **500 Credits**: $39.99
- **1000 Credits**: $69.99

Credit usage:
- Job analysis: 2 credits per analysis
- Job matching: 3 credits per match

## Error Handling

### Validation Errors

Validation errors return a simplified format:
```json
{
  "status_code": 422,
  "error_message": "Invalid email format",
  "error_type": "email_validation_error"
}
```

Error types:
- `email_validation_error` - Email format validation
- `password_validation_error` - Password complexity validation
- `validation_error` - Other validation errors

### API Errors

Other API errors use standard FastAPI format:
```json
{
  "detail": "Error message here"
}
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_payments.py
```

### Code Formatting

```bash
black .
isort .
```

## License

This project is part of a software architecture course final project.

## Author

Tyler Thong Nguyen - 400610270

