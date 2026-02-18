from readgmail import GmailClient
from dotenv import load_dotenv
from logger import setup_logging  
import logging

from messaging import Producer

load_dotenv()
# Setup logging
setup_logging()
# Get logger for this module
logger = logging.getLogger(__name__)


def main():
   
    READ_ONLY_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
    gmail_client = GmailClient(READ_ONLY_SCOPES)
    gmail_client.authenticate()
    unread_messages = gmail_client.get_unread_messages_from_LinkedIn_JobAlerts(max_results=20)
    for unread_message in unread_messages:
        logger.info("########################################################")
        print(unread_message.model_dump_json())
        with open(f"unread_messages_debug_{unread_message.id}.json", "w") as f:
            f.write(unread_message.model_dump_json())
        logger.info("--------------------------------")

# Send the unread messages to the ActiveMQ queue
main()