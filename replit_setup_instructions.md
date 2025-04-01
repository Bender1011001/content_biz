# Replit Setup Instructions

## Adding Secrets

You can add the secrets to your Replit project in two ways:

### Method 1: Add Each Secret Individually

1. Open your Replit project [https://replit.com/@andrewdarcy530/contentbiz](https://replit.com/@andrewdarcy530/contentbiz).
2. Click on the "Tools" icon in the left sidebar.
3. Select "Secrets".
4. For each key-value pair in `secrets.json`, add them individually:
   - Enter the key name (e.g., `DATABASE_URL`) in the "Key" field.
   - Enter the corresponding value in the "Value" field.
   - Click "Add new secret".
   - Repeat for all secrets.

### Method 2: Import JSON File

If your Replit account supports bulk import of secrets:

1. Open your Replit project.
2. Click on the "Tools" icon in the left sidebar.
3. Select "Secrets".
4. Look for an "Import" or "Import JSON" option (if available).
5. Upload or paste the contents of the `secrets.json` file.

## Running Your Project

After adding all secrets:

1. Click the "Run" button in Replit.
2. The `.replit` file we created will automatically:
   - Run database migrations with `alembic upgrade head`
   - Start the FastAPI server with `uvicorn main:app --host 0.0.0.0 --port $PORT`

## Testing

Once the application is running, test the deployment by:

1. Fill out the content brief form.
2. Use Stripe test card `4242 4242 4242 4242` with any future expiry date and any 3-digit CVC.
3. Check if the brief was submitted, payment processed, and email sent correctly.

## Production Readiness

For production with real clients:

1. Change Stripe keys from Test to Live in the Replit Secrets.
2. Consider upgrading from Gmail SMTP to SendGrid or another production email service.
