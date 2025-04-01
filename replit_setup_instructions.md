# Setting Up Content Biz on Replit

This document provides step-by-step instructions for setting up and running the Content Biz application on Replit.

## 1. Initial Setup

### 1.1 Create a New Repl
- Create a new Repl on Replit.com
- Choose "Import from GitHub" and use the repository URL: `https://github.com/Bender1011001/content_biz`
- Select "Python" as the language

### 1.2 Configure Secrets
Add the following secrets in the Replit Secrets tab (lock icon in the sidebar):

- `DATABASE_URL`: Your PostgreSQL connection string (Replit provides a free PostgreSQL database)
- `OPENROUTER_API_KEY`: Your OpenRouter API key for AI model access
- `STRIPE_SECRET_KEY`: Your Stripe secret key (test key for development)
- `STRIPE_WEBHOOK_SECRET`: Your Stripe webhook secret
- `JWT_SECRET_KEY`: A secure random string for JWT token generation
- `EMAIL_HOST`: SMTP server host (e.g., smtp.gmail.com)
- `EMAIL_PORT`: SMTP server port (e.g., 587)
- `EMAIL_USERNAME`: Your email username
- `EMAIL_PASSWORD`: Your email password or app password
- `EMAIL_FROM`: The sender email address
- `QUALITY_THRESHOLD`: Quality threshold for content (e.g., 0.85)

## 2. Configure the Replit Environment

### 2.1 Create or Update `.replit` File
Create a `.replit` file in the root directory with the following content:

```
run = "python -m pip install --break-system-packages --no-cache-dir openai>=1.61.0 && python -m pip install --break-system-packages --no-cache-dir -r requirements.txt && python -m spacy download en_core_web_sm && alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 5000"
```

This command will:
1. Install OpenAI package (required by CrewAI)
2. Install all dependencies from requirements.txt
3. Download the spaCy language model
4. Run database migrations
5. Start the Uvicorn server

### 2.2 Update `requirements.txt`
Ensure your requirements.txt file has compatible versions. If you encounter dependency conflicts, you may need to adjust version constraints.

## 3. Database Setup

### 3.1 Configure Database Connection
- Get your Replit PostgreSQL connection string from the Replit database tab
- Add it as the `DATABASE_URL` secret

### 3.2 Run Migrations
The run command will automatically run migrations with `alembic upgrade head`.

## 4. Testing the Application

### 4.1 Basic Functionality Test
After clicking "Run", verify:
- The server starts without errors
- The web form loads at the root URL
- The database connection is successful

### 4.2 End-to-End Test
Test the complete workflow:
1. Submit a brief through the form
2. Make a test payment using Stripe test card (4242 4242 4242 4242)
3. Verify the CrewAI workflow executes
4. Check that the email is sent

## 5. Troubleshooting

### 5.1 Dependency Issues
If you encounter dependency conflicts:
- Try using `--no-cache-dir` flag for pip installations
- Adjust version constraints in requirements.txt
- Check for compatibility between crewai, fastapi, and pydantic versions

### 5.2 CrewAI Import Issues
If you see errors related to CrewAI imports:
- The project has been updated to use the decorator pattern for tools: `from crewai.tools import tool`
- Ensure you're using the latest code from the repository

### 5.3 Database Connection Issues
- Verify your DATABASE_URL secret is correctly formatted
- Check that the Replit PostgreSQL database is running

### 5.4 Logs
- Check the Replit console for error logs
- Look for specific error messages to diagnose issues

## 6. Production Considerations

### 6.1 Environment Variables
- For production, update your Stripe keys to live keys
- Consider using SendGrid for more reliable email delivery

### 6.2 Performance
- Monitor the application's performance on Replit
- Consider upgrading to a paid Replit plan for better resources if needed

### 6.3 Security
- Ensure all sensitive information is stored in Secrets
- Regularly rotate API keys and passwords
