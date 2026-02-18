# Gmail Quickstart - LinkedIn Job Alert Parser

A Python application that uses the Gmail API to read LinkedIn Job Alert emails and parse them into structured JSON format using Pydantic models.

## Features

- OAuth2 authentication with Google Gmail API
- Fetch unread LinkedIn Job Alert emails
- Parse job listings from email body (title, company, location, URL)
- Structured JSON output using Pydantic models
- Production-ready logging with **python-json-logger**
  - Dual output: JSON (stdout) + text (stderr)
  - CloudWatch/Kubernetes ready
  - Environment-based configuration
- Handles multipart email formats (plain text and HTML)
- Clean URLs with tracking parameters removed

## Requirements

- Python 3.12+
- Google Cloud project with Gmail API enabled
- OAuth 2.0 credentials

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd gmail_quickstart
   ```

2. Install dependencies using uv:
   ```bash
   uv sync
   ```

   Or add dependencies individually:
   ```bash
   uv add google-api-python-client google-auth-httplib2 google-auth-oauthlib pydantic beautifulsoup4 python-dotenv python-json-logger
   ```

   Or with pip:
   ```bash
   pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib pydantic beautifulsoup4 python-dotenv python-json-logger
   ```

3. Configure logging (optional):
   ```bash
   cp .env.example .env
   # Edit .env to customize LOG_LEVEL, LOG_FORMAT, ENVIRONMENT
   ```

## Google Cloud Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API:
   - Navigate to **APIs & Services > Library**
   - Search for "Gmail API" and enable it
4. Create OAuth 2.0 credentials:
   - Go to **APIs & Services > Credentials**
   - Click **Create Credentials > OAuth client ID**
   - Select **Desktop app** as the application type
   - Download the credentials and save as `credentials.json` in the project root

## Usage

Run the LinkedIn Job Alert parser:

```bash
uv run readgmail.py
```

Or with Python directly:

```bash
python readgmail.py
```

On first run, a browser window will open for Google authentication. After granting permissions, a `token.json` file will be created to store your credentials for future runs.

### Testing Logging

Test the logging configuration:

```bash
# Test JSON logging with different log levels
uv run python logger/example_logging.py
```

## Example Output

The application outputs structured JSON for each LinkedIn Job Alert email:

```json
{
  "id": "19c05dcea1a2afd7",
  "subject": "Your job alert for Director of Engineering in United States",
  "sender": "LinkedIn Job Alerts <jobalerts-noreply@linkedin.com>",
  "date": "Sun, 26 Jan 2026 10:00:00 -0800",
  "snippet": "New jobs match your preferences...",
  "jobs": [
    {
      "title": "Senior Director of Engineering",
      "company": "ClickUp",
      "location": "United States",
      "url": "https://www.linkedin.com/comm/jobs/view/4343659841"
    },
    {
      "title": "Director, Software Engineering",
      "company": "GoodLeap",
      "location": "San Francisco, CA",
      "url": "https://www.linkedin.com/comm/jobs/view/4366287547"
    }
  ]
}
```

## Project Structure

```
gmail_quickstart/
├── models/
│   ├── __init__.py              # Re-exports Job, LinkedInJobAlert
│   └── linkedin.py              # Pydantic models (Job, LinkedInJobAlert)
├── logger/
│   ├── __init__.py              # Re-exports setup_logging
│   ├── logger_config.py         # Logging configuration with python-json-logger
│   └── example_logging.py       # Example demonstrating logging usage
├── readgmail.py                 # Main GmailClient class
├── quickstart.py                # Original Gmail API quickstart example
├── .env                         # Environment variables (create from .env.example)
├── .env.example                 # Example environment configuration
├── credentials.json             # OAuth client credentials (from Google Cloud)
├── token.json                   # User access/refresh tokens (auto-generated)
├── pyproject.toml               # Project dependencies and metadata
├── README.md                    # This file
├── LOGGING_USAGE.md             # Detailed logging documentation
├── MIGRATION_COMPLETE.md        # Migration to python-json-logger summary
└── MIGRATION_TO_JSON_LOGGER.md # Detailed migration guide
```

## Pydantic Models

### Job
Represents a single job listing:
- `title`: Job title
- `company`: Company name (optional)
- `location`: Job location (optional)
- `url`: LinkedIn job URL

### LinkedInJobAlert
Represents a parsed LinkedIn Job Alert email:
- `id`: Gmail message ID
- `subject`: Email subject
- `sender`: Sender email address
- `date`: Email date
- `snippet`: Email preview snippet
- `jobs`: List of `Job` objects

## Configuration

### Scopes

The application uses read-only access:

```python
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
```

To change scopes, modify the `SCOPES` variable and delete `token.json` to re-authenticate.

### Query Filters

Modify the query in `get_unread_messages_from_LinkedIn_JobAlerts()` to filter different messages:

| Query | Description |
|-------|-------------|
| `is:unread` | Unread messages |
| `is:unread in:inbox` | Unread in inbox only |
| `is:unread from:example@gmail.com` | Unread from specific sender |
| `is:unread after:2024/01/01` | Unread after a date |

### Logging

The application uses **python-json-logger** for production-ready structured logging with flexible configuration via environment variables:

**Configuration (.env file):**

```bash
LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=dual         # json, text, or dual
ENVIRONMENT=development # development or production
```

**Logging Formats:**

| Format | Output | Use Case |
|--------|--------|----------|
| `json` | Structured JSON to stdout | CloudWatch, Kubernetes, production |
| `text` | Human-readable to stderr | Local development, debugging |
| `dual` | Both formats (default) | Development with cloud deployment |

**Example JSON output (for CloudWatch):**
```json
{"timestamp": "2026-01-26T22:30:22.123Z", "level": "INFO", "message": "Found LinkedIn Job Alerts", "total_alerts": 3, "total_jobs": 15}
```

**Example text output (for console):**
```
2026-01-26 14:30:22 - readgmail - INFO - Found LinkedIn Job Alerts
```

**Documentation:**
- [LOGGING_USAGE.md](LOGGING_USAGE.md) - Complete logging guide and best practices
- [MIGRATION_COMPLETE.md](MIGRATION_COMPLETE.md) - Summary of python-json-logger migration
- [MIGRATION_TO_JSON_LOGGER.md](MIGRATION_TO_JSON_LOGGER.md) - Detailed migration guide

## Dependencies

| Package | Purpose |
|---------|---------|
| `google-api-python-client` | Google API client library |
| `google-auth-httplib2` | HTTP transport for Google Auth |
| `google-auth-oauthlib` | OAuth2 authentication flow |
| `pydantic` | Data validation and JSON serialization |
| `beautifulsoup4` | HTML parsing (optional, for HTML emails) |
| `python-dotenv` | Load environment variables from .env file |
| `python-json-logger` | Production-ready structured JSON logging |

## Security Notes

- Never commit `credentials.json` or `token.json` to version control
- Add them to `.gitignore`
- The `token.json` contains sensitive refresh tokens that grant access to your Gmail

## Deploying to Kubernetes

For headless/background service deployment:

### 1. Prepare Credentials

Generate `token.json` locally by running the app once:

```bash
uv run python readgmail.py
```

### 2. Create Kubernetes Secrets

```bash
# Gmail credentials
kubectl create secret generic gmail-credentials \
  --from-file=token.json \
  --from-file=credentials.json

# Environment configuration (optional)
kubectl create configmap gmail-config \
  --from-literal=LOG_LEVEL=INFO \
  --from-literal=LOG_FORMAT=json \
  --from-literal=ENVIRONMENT=production
```

### 3. Configure Your Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gmail-client
spec:
  replicas: 1
  template:
    spec:
      containers:
      - name: app
        image: gmail-client:latest
        env:
        - name: LOG_LEVEL
          valueFrom:
            configMapKeyRef:
              name: gmail-config
              key: LOG_LEVEL
        - name: LOG_FORMAT
          valueFrom:
            configMapKeyRef:
              name: gmail-config
              key: LOG_FORMAT
        - name: ENVIRONMENT
          valueFrom:
            configMapKeyRef:
              name: gmail-config
              key: ENVIRONMENT
        volumeMounts:
        - name: credentials
          mountPath: /app/credentials.json
          subPath: credentials.json
        - name: credentials
          mountPath: /app/token.json
          subPath: token.json
      volumes:
      - name: credentials
        secret:
          secretName: gmail-credentials
```

The app automatically refreshes tokens, so as long as it runs periodically, credentials stay valid.

### CloudWatch Integration

Logs are automatically in JSON format (when `LOG_FORMAT=json`) and sent to stdout, making them compatible with:
- AWS CloudWatch Container Insights
- Fluentd/Fluent Bit
- Kubernetes logging drivers
- Any log aggregation system

## Troubleshooting

### Authentication Issues

**Problem:** "The file token.json stores invalid credentials"

**Solution:** Delete `token.json` and re-authenticate:
```bash
rm token.json
uv run python readgmail.py
```

### Scope Changes

**Problem:** Need to modify scopes (e.g., from readonly to modify)

**Solution:** 
1. Update `SCOPES` in `readgmail.py`
2. Delete `token.json`
3. Run the app to re-authenticate with new scopes

### No Jobs Found

**Problem:** Script runs but finds no jobs

**Solution:** Check that:
- You have unread LinkedIn Job Alert emails
- The sender is exactly `"LinkedIn Job Alerts"`
- Run with `LOG_LEVEL=DEBUG` to see detailed parsing info

### Logging Not Working

**Problem:** No logs appearing

**Solution:** Check your `.env` file:
```bash
LOG_LEVEL=INFO      # Not DEBUG if you want to see INFO logs
LOG_FORMAT=dual     # For both JSON and text output
```

## Additional Resources

- [Gmail API Documentation](https://developers.google.com/gmail/api)
- [python-json-logger GitHub](https://github.com/madzak/python-json-logger)
- [Pydantic Documentation](https://docs.pydantic.dev/)

## License

MIT
