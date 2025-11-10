# Job Matching & Analysis API

A FastAPI-based backend application for job matching, fraud analysis, and payment management with integration to third-party APIs.

## Technology Stack

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green.svg)
![Docker](https://img.shields.io/badge/Docker-28.4.0-blue.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-darkblue.svg)
![Stripe](https://img.shields.io/badge/Stripe-Payment-purple.svg)

## Features

- Job fraud analysis using Ruvia Trust API
- Secure payment processing with Stripe API
- Job aggregation from LinkedIn and Indeed feeds
- Intelligent job matching with multiple strategies
- Real-time updates using Observer pattern
- Modular architecture with design patterns

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
│   │   ├── jobs.py        # Job matching endpoints
│   │   ├── payments.py    # Payment endpoints
│   │   └── analysis.py    # Job analysis endpoints
│   └── services/
│       ├── ruvia_service.py              # Ruvia Trust API integration
│       ├── stripe_service.py             # Stripe API integration
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

6. Update `.env` with your API keys:
   - Stripe API keys
   - Ruvia Trust API key
   - LinkedIn API key
   - Indeed API key

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

### Jobs

- `POST /api/v1/jobs/match` - Match jobs based on user preferences
- `GET /api/v1/jobs/aggregate` - Aggregate jobs from LinkedIn and Indeed

### Payments

- `POST /api/v1/payments/intent` - Create Stripe payment intent
- `POST /api/v1/payments/webhook` - Handle Stripe webhook events
- `GET /api/v1/payments/user/{user_id}/credits` - Get user credit balance

### Analysis

- `POST /api/v1/analysis/analyze` - Analyze job posting for fraud and scoring
- `GET /api/v1/analysis/history/{user_id}` - Get analysis history

### Health

- `GET /health` - Health check endpoint
- `GET /` - Root endpoint

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

- `STRIPE_SECRET_KEY` - Stripe secret API key
- `STRIPE_PUBLISHABLE_KEY` - Stripe publishable API key
- `RUVIA_TRUST_API_KEY` - Ruvia Trust API key
- `LINKEDIN_API_KEY` - LinkedIn API key
- `INDEED_API_KEY` - Indeed API key
- `DATABASE_URL` - Database connection string

## Database

The application uses SQLite by default. The database is automatically initialized on first run with the following tables:

- `users` - User accounts and credit balances
- `job_analyses` - Job analysis results
- `payments` - Payment transaction records

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

## Development

### Running Tests

```bash
pytest
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

