import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def get_message_body(payload):
    """Extract the body from a Gmail message payload."""
    body = ""
    
    if "body" in payload and payload["body"].get("data"):
        # Simple message - body is directly in payload
        body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")
    
    elif "parts" in payload:
        # Multipart message - need to find the text part
        for part in payload["parts"]:
            mime_type = part.get("mimeType", "")
            
            if mime_type == "text/plain":
                # Prefer plain text
                data = part["body"].get("data", "")
                if data:
                    body = base64.urlsafe_b64decode(data).decode("utf-8")
                    break
            elif mime_type == "text/html" and not body:
                # Fall back to HTML if no plain text
                data = part["body"].get("data", "")
                if data:
                    body = base64.urlsafe_b64decode(data).decode("utf-8")
            elif mime_type.startswith("multipart/"):
                # Nested multipart - recurse
                body = get_message_body(part)
                if body:
                    break
    
    return body

def get_unread_messages_from_LinkedIn_JobAlerts(service, max_results=10):
    """Fetch unread messages from Gmail."""
    results = service.users().messages().list(
        userId="me",
        q="is:unread",
        maxResults=max_results
    ).execute()
    
    messages = results.get("messages", [])
    
    if not messages:
        print("No unread messages.")
        return []
    
    unread = []
    for msg in messages:
        message = service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="full",
            metadataHeaders=["Subject", "From", "Date"]
        ).execute()
        

        headers = {h["name"]: h["value"] for h in message["payload"]["headers"]}
        body = get_message_body(message["payload"])
        if "LinkedIn Job Alerts" in headers.get("From", ""):
            unread.append({
                "id": msg["id"],
                "subject": headers.get("Subject", ""),
                "from": headers.get("From", ""),
                "date": headers.get("Date", ""),
                "snippet": message.get("snippet", ""),
                "body": body
            })
        else:
            print(f"Message from {headers.get('From', '')} is not from LinkedIn Job Alerts")
      
    
    return unread



def main():
  """Shows basic usage of the Gmail API.
  Lists the user's Gmail labels.
  """
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  try:
    # Call the Gmail API
    service = build("gmail", "v1", credentials=creds)
    results = service.users().labels().list(userId="me").execute()
    labels = results.get("labels", [])

    if not labels:
      print("No labels found.")
      return
    print("Labels:")
    for label in labels:
      print(label["name"])

    print("--------------------------------")
    print("Getting unread messages...")
    unread_messages = get_unread_messages_from_LinkedIn_JobAlerts(service, max_results=20)
    print("Unread messages:")
    for msg in unread_messages:
      print(msg["subject"])
      print(msg["snippet"])
      print(msg["body"])
      print("--------------------------------")

  except HttpError as error:
    # TODO(developer) - Handle errors from gmail API.
    print(f"An error occurred: {error}")


if __name__ == "__main__":
  main()
