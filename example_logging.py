"""
Example demonstrating logging configuration usage with python-json-logger.
"""

from dotenv import load_dotenv
from logger_config import setup_logging
import logging

# Load environment variables from .env
load_dotenv()

# Setup logging (reads LOG_LEVEL, LOG_FORMAT, ENVIRONMENT from .env)
setup_logging()

# Get logger for this module
logger = logging.getLogger(__name__)


def process_data(items):
    """Example function with logging."""
    logger.info(f"Processing {len(items)} items", extra={'item_count': len(items)})
    
    for i, item in enumerate(items, 1):
        logger.debug(f"Processing item {i}/{len(items)}", extra={'item_num': i, 'item': item})
    
    logger.info("Processing complete", extra={'total_processed': len(items)})


def main():
    """Main function demonstrating various log levels."""
    logger.info("Application started")
    
    # Different log levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    
    # Logging with extra structured data
    logger.info(
        "User login attempt",
        extra={
            'user_id': 'user123',
            'ip_address': '192.168.1.1',
            'success': True
        }
    )
    
    # Processing example
    items = ['item1', 'item2', 'item3']
    process_data(items)
    
    # Error logging with exception info
    try:
        result = 10 / 0
    except ZeroDivisionError as e:
        logger.error("Division by zero error", exc_info=True)
    
    logger.info("Application finished")


if __name__ == "__main__":
    main()
