# AI-Assisted Content Creation Service

An automated content creation platform that uses AI to generate high-quality content for businesses and creators. Clients submit briefs, the system processes them using AI, and delivers polished content back to the client.

## Features

- Brief submission via web form
- AI-powered content generation using CrewAI and OpenRouter
- Automated quality checks for grammar and coherence
- Payment processing with Stripe ($75 per post)
- Admin dashboard for content management
- Email delivery of finalized content

## Tech Stack

- **Backend**: FastAPI
- **Database**: PostgreSQL
- **AI Framework**: CrewAI with OpenRouter
- **Quality Checks**: spaCy and LanguageTool
- **Payment Processing**: Stripe
- **Frontend**: HTML, CSS, JavaScript

## Project Structure

```
content_biz/
├── alembic/              # Database migrations
├── app/
│   ├── api/              # API endpoints
│   ├── db/               # Database models and utilities
│   ├── schemas/          # Pydantic models
│   ├── services/         # Business logic
│   └── utils/            # Helper utilities
├── static/               # Static files (CSS, JS)
├── templates/            # HTML templates
├── tests/                # Unit and integration tests
├── .env.example          # Example environment variables
├── alembic.ini           # Alembic configuration
├── config.py             # Configuration settings
├── main.py               # Application entry point
└── requirements.txt      # Project dependencies
```

## Setup Instructions

### Prerequisites

- Python 3.9+
- PostgreSQL
- Stripe account (for payments)
- OpenRouter API key (for AI content generation)
- Serper API key (optional, for web research)

### Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd content_biz
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS/Linux
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Download spaCy model:
   ```
   python -m spacy download en_core_web_sm
   ```

5. Create a `.env` file (use `.env.example` as a template):
   ```
   cp .env.example .env
   ```

6. Set up the database:
   ```
   # Create a PostgreSQL database
   createdb content_db

   # Run migrations
   alembic upgrade head
   ```

### Running the Application

1. Start the application:
   ```
   python main.py
   ```

2. Access the application:
   - Web Form: http://localhost:8000/
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

## API Endpoints

- `POST /api/briefs/` - Submit a content brief
- `POST /api/payments/` - Process a payment
- `GET /api/content/{content_id}` - Retrieve generated content
- `POST /api/admin/content/{content_id}/approve` - Approve content for delivery

## Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `OPENROUTER_API_KEY`: API key for OpenRouter
- `STRIPE_API_KEY`: API key for Stripe
- `SERPER_API_KEY`: API key for Serper (optional)
- `CONTENT_PRICE`: Price per content piece (default: 75.0)
- `QUALITY_THRESHOLD`: Minimum quality score for auto-approval (default: 70.0)

## Development Workflow

1. Create a new feature branch
2. Make changes and add tests
3. Run tests: `pytest`
4. Submit a pull request

## License

[MIT License](LICENSE)
