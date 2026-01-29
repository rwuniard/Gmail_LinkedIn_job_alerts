# Logging Usage Guide

This project uses a custom `Log` class for flexible logging configuration with support for both JSON (structured) and text (human-readable) formats.

## Quick Start

### 1. Copy .env.example to .env

```bash
cp .env.example .env
```

### 2. Configure Logging in .env

```bash
# Set log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO

# Set format: json, text, or dual
LOG_FORMAT=dual

# Set environment: development or production
ENVIRONMENT=development
```

### 3. Use in Your Code

```python
from dotenv import load_dotenv
from logger_config import setup_logging
import logging

# Load environment variables
load_dotenv()

# Setup logging (reads from .env)
setup_logging()

# Get logger for your module
logger = logging.getLogger(__name__)

# Use it!
logger.info("Hello world")
logger.debug("Debugging info", extra={'user_id': 123})
logger.error("Something went wrong", exc_info=True)
```

## Configuration Options

### LOG_LEVEL

Controls which log messages are displayed:

| Level | When to Use | Example |
|-------|-------------|---------|
| `DEBUG` | Detailed diagnostic information | Variable values, function calls |
| `INFO` | General informational messages (default) | Process started, task completed |
| `WARNING` | Something unexpected but not an error | Deprecated feature used |
| `ERROR` | An error occurred but app continues | Failed to process one item |
| `CRITICAL` | Serious error, app may crash | Database connection lost |

### LOG_FORMAT

Controls output format:

| Format | Description | Use Case |
|--------|-------------|----------|
| `text` | Human-readable format to stderr | Local development, console debugging |
| `json` | JSON format to stdout | Production, CloudWatch, Prometheus |
| `dual` | Both formats (default) | Development with cloud deployment |

#### Text Format Output (stderr)

```
2026-01-26 14:30:22 - readgmail - INFO - Processing email
2026-01-26 14:30:23 - readgmail - DEBUG - Found 5 jobs
```

#### JSON Format Output (stdout)

```json
{"timestamp": "2026-01-26T22:30:22.123456Z", "level": "INFO", "logger": "readgmail", "message": "Processing email", "module": "readgmail", "function": "get_unread_messages", "line": 165}
{"timestamp": "2026-01-26T22:30:23.456789Z", "level": "DEBUG", "logger": "readgmail", "message": "Found 5 jobs", "module": "readgmail", "function": "parse_jobs", "line": 98, "job_count": 5}
```

### ENVIRONMENT

Controls log format detail:

| Environment | Format Style |
|-------------|--------------|
| `development` | Detailed with module names |
| `production` | Compact format |

## Adding Custom Fields

Use the `extra` parameter to add structured data to logs:

```python
logger.info(
    "Job alert processed",
    extra={
        'email_id': msg_id,
        'job_count': len(jobs),
        'sender': sender_email
    }
)
```

**JSON Output:**
```json
{
  "timestamp": "2026-01-26T22:30:22.123Z",
  "level": "INFO",
  "message": "Job alert processed",
  "email_id": "abc123",
  "job_count": 5,
  "sender": "jobs@linkedin.com"
}
```

## CloudWatch / Kubernetes Setup

For cloud environments:

### 1. Set Environment Variables

```bash
export LOG_LEVEL=INFO
export LOG_FORMAT=json
export ENVIRONMENT=production
```

Or in Kubernetes:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: gmail-client
spec:
  containers:
  - name: app
    image: gmail-client:latest
    env:
    - name: LOG_LEVEL
      value: "INFO"
    - name: LOG_FORMAT
      value: "json"
    - name: ENVIRONMENT
      value: "production"
```

### 2. CloudWatch Agent Configuration

The application logs to stdout in JSON format, which CloudWatch agents automatically capture:

```json
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/containers/*.log",
            "log_group_name": "/aws/gmail-client",
            "log_stream_name": "{instance_id}"
          }
        ]
      }
    }
  }
}
```

### 3. Query Logs in CloudWatch Insights

```sql
fields @timestamp, level, message, email_id, job_count
| filter level = "ERROR"
| sort @timestamp desc
| limit 20
```

## Programmatic Configuration

You can also configure logging programmatically:

```python
from logger_config import setup_logging

# Override .env settings
setup_logging(
    log_level='DEBUG',
    log_format='json',
    environment='production'
)
```

## Testing Output

### See Both Outputs

```bash
python readgmail.py
```

### See Only JSON (stdout)

```bash
python readgmail.py 1>json.log 2>/dev/null
cat json.log
```

### See Only Text (stderr)

```bash
python readgmail.py 2>text.log 1>/dev/null
cat text.log
```

## Best Practices

1. **Use appropriate log levels**
   - `INFO` for significant events (started, completed, found X items)
   - `DEBUG` for detailed diagnostic info
   - `ERROR` for failures with `exc_info=True`

2. **Add structured data**
   ```python
   logger.info("Processing", extra={'count': 5, 'type': 'job_alert'})
   ```

3. **Don't log sensitive data**
   - Avoid logging passwords, tokens, email content
   - Use IDs instead of full data

4. **Log exceptions properly**
   ```python
   try:
       # code
   except Exception as e:
       logger.exception("Failed to process")  # Includes traceback
   ```

5. **Use logger per module**
   ```python
   logger = logging.getLogger(__name__)  # Not a hardcoded string
   ```
