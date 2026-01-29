import os
import json
import logging
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
import re
from typing import List
from bs4 import BeautifulSoup
from models.linkedin import Job, LinkedInJobAlert
from logger_config import setup_logging

# Load environment variables from .env file
load_dotenv()

# Setup logging with configuration from .env (now using python-json-logger)
setup_logging()

# Get logger for this module
logger = logging.getLogger(__name__)


class GmailClient:

    def __init__(self, scopes):
        self.credentials = None
        self.read_only_scopes = scopes
        logger.info("GmailClient initialized", extra={'scopes': scopes})


    def authenticate(self):
        """Authenticate with Gmail API using OAuth2."""
        logger.info("Starting authentication process")
        
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists("token.json"):
            self.credentials = Credentials.from_authorized_user_file("token.json", self.read_only_scopes)
            logger.debug("Credentials loaded from token.json")
        
        # If there are no (valid) credentials available, let the user log in.
        if not self.credentials or not self.credentials.valid:
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                logger.info("Refreshing expired credentials")
                self.credentials.refresh(Request())
                logger.debug("Credentials refreshed successfully")
            else:
                logger.info("Running OAuth flow for new credentials")
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", self.read_only_scopes
                )
                self.credentials = flow.run_local_server(port=0)
                
                # Save the credentials for the next run
                with open("token.json", "w") as token:
                    token.write(self.credentials.to_json())
                logger.info("New credentials created and saved to token.json")
        
        logger.info("Authentication successful")


    def __parse_jobs_from_body(self, body: str) -> List[Job]:
        """Parse job listings from LinkedIn Job Alert plain text email body."""
        logger.debug("Parsing jobs from email body", extra={'body_length': len(body)})
        jobs = []
        
        # Split by the separator line
        sections = re.split(r'-{20,}', body)
        
        for section in sections:
            lines = [line.strip() for line in section.strip().split('\n') if line.strip()]
            
            if len(lines) < 4:
                continue
            
            # Find the "View job:" line and extract URL
            url = None
            view_job_idx = None
            for i, line in enumerate(lines):
                if line.startswith("View job:"):
                    url = line.replace("View job:", "").strip()
                    view_job_idx = i
                    break
            
            if not url or not url.startswith("https://www.linkedin.com/comm/jobs/view"):
                continue
            
            # Lines before "View job:" contain job info
            # Pattern: Title, Company, Location, [optional metadata]
            job_lines = lines[:view_job_idx]
            
            if len(job_lines) >= 3:
                title = job_lines[0]
                company = job_lines[1]
                location = job_lines[2]
                
                logger.debug("Found job", extra={'title': title, 'company': company, 'location': location})
                
                jobs.append(Job(
                    title=title,
                    company=company,
                    location=location,
                    url=url.split('?')[0]  # Clean URL, remove tracking params
                ))
        
        logger.debug(f"jobs:\n {jobs}")
        return jobs


    def __get_message_body(self, payload):
        """
        Extract the body from a Gmail message payload.
        Args:
            payload: The payload of the message.
        Returns:
            The body of the message.
        """
        body = ""
        
        if "body" in payload and payload["body"].get("data"):
            # Simple message - body is directly in payload
            body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")
        
        elif "parts" in payload:
            # Multipart message - need to find the text part
            for part in payload["parts"]:
                mime_type = part.get("mimeType", "")
                
                if mime_type == "text/plain":
                    print(f"Found plain text part: {mime_type}")
                    # Prefer plain text
                    data = part["body"].get("data", "")
                    if data:
                        body = base64.urlsafe_b64decode(data).decode("utf-8")
                        break
                elif mime_type == "text/html" and not body:
                    print(f"Found HTML part: {mime_type}")
                    # Fall back to HTML if no plain text
                    data = part["body"].get("data", "")
                    if data:
                        body = base64.urlsafe_b64decode(data).decode("utf-8")
                elif mime_type.startswith("multipart/"):
                    # Nested multipart - recurse
                    body = self.__get_message_body(part)
                    if body:
                        break
        logger.debug(f"body:\n {body}")
        return body



    def get_unread_messages_from_LinkedIn_JobAlerts(self, max_results=10):
        """
        Fetch unread messages that are from LinkedIn Job Alerts from Gmail.
        Args:
            max_results: The maximum number of messages to return.
        Returns:
            A list of unread messages that are from LinkedIn Job Alerts.
        """
        logger.info("Fetching unread LinkedIn Job Alerts", extra={'max_results': max_results})
        
        try:
            service = build("gmail", "v1", credentials=self.credentials)
            results = service.users().messages().list(
                userId="me",
                q="is:unread",
                maxResults=max_results
            ).execute()
            
            messages = results.get("messages", [])
            logger.info(f"Found {len(messages)} unread messages", extra={'message_count': len(messages)})
            
            if not messages:
                logger.warning("No unread messages found")
                return []

            unread = []
            for i, msg in enumerate(messages, 1):
                logger.debug(
                    f"Processing message {i}/{len(messages)}",
                    extra={'message_num': i, 'total_messages': len(messages), 'message_id': msg["id"]}
                )
                
                message = service.users().messages().get(
                    userId="me",
                    id=msg["id"],
                    format="full",
                    metadataHeaders=["Subject", "From", "Date"]
                ).execute()

                headers = {h["name"]: h["value"] for h in message["payload"]["headers"]}
                body = self.__get_message_body(message["payload"])
                
                if "LinkedIn Job Alerts" in headers.get("From", ""):
                    logger.info(
                        "Processing LinkedIn Job Alert",
                        extra={
                            'message_id': msg["id"],
                            'subject': headers.get("Subject", ""),
                            'sender': headers.get("From", "")
                        }
                    )
                    
                    jobs = self.__parse_jobs_from_body(body)
                
                    alert = LinkedInJobAlert(
                        id=msg["id"],
                        subject=headers.get("Subject", ""),
                        sender=headers.get("From", ""),
                        date=headers.get("Date", ""),
                        snippet=message.get("snippet", ""),
                        jobs=jobs
                    )
                
                    unread.append(alert)
                else:
                    logger.debug(
                        "Skipping non-LinkedIn message",
                        extra={'message_id': msg["id"], 'sender': headers.get('From', '')}
                    )
            
            logger.info(
                "Completed processing LinkedIn Job Alerts",
                extra={
                    'total_alerts': len(unread),
                    'total_jobs': sum(len(alert.jobs) for alert in unread)
                }
            )
            return unread
            
        except HttpError as error:
            logger.error(
                "Gmail API error occurred",
                extra={'error_status': error.resp.status if hasattr(error, 'resp') else 'unknown'},
                exc_info=True
            )
            return None



if __name__ == "__main__":
    READ_ONLY_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
    gmail_client = GmailClient(READ_ONLY_SCOPES)
    gmail_client.authenticate()
    unread_messages = gmail_client.get_unread_messages_from_LinkedIn_JobAlerts(max_results=20)
    for unread_message in unread_messages:
        print("########################################################")
        print(unread_message.model_dump_json())
        with open(f"unread_messages_debug_{unread_message.id}.json", "w") as f:
            f.write(unread_message.model_dump_json())
        print("--------------------------------")


