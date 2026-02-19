# Environment Variables Setup

## Quick Start

1. **Copy the example file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` and add your actual API keys:**
   - Get your OpenAI API key from: https://platform.openai.com/api-keys
   - Get your Groq API key from: https://console.groq.com/keys
   - Get your Gemini API key from: https://makersuite.google.com/app/apikey

3. **Run the application:**
   ```bash
   python flask_server.py
   ```

## Required Environment Variables

### API Keys (at least one required)
- `OPENAI_API_KEY` - Your OpenAI API key
- `GROQ_API_KEY` - Your Groq API key  
- `GEMINI_API_KEY` - Your Google Gemini API key

### Configuration
- `AI_PROVIDER` - Which provider to use: `"groq"`, `"openai"`, `"gemini"`, or `"fallback"`
- `OWNER_NAME` - Your name (default: "Vishnu")

### Optional Email Configuration
- `EMAIL_ENABLED` - Enable/disable email features (`True` or `False`)
- `SMTP_SERVER` - SMTP server address (default: `smtp.gmail.com`)
- `SMTP_PORT` - SMTP port (default: `587`)
- `SENDER_EMAIL` - Email address to send from
- `APP_PASSWORD` - App-specific password for email
- `OWNER_EMAIL` - Owner email address
- `DEFAULT_RECIPIENT` - Default email recipient

## For Netlify Deployment

Set all environment variables in Netlify dashboard:
1. Go to your site dashboard
2. Navigate to **Site settings > Environment variables**
3. Add each variable from `.env.example`

See `NETLIFY_DEPLOYMENT.md` for detailed deployment instructions.
