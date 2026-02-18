import json
import stomp
from dotenv import load_dotenv
import os
import uuid
import time
import threading
from logger import setup_logging
import logging

setup_logging()
# Get logger for this module
logger = logging.getLogger(__name__)


class ReceiptListener(stomp.ConnectionListener):
    """
    Listener for receipt messages from ActiveMQ.
    This is used to ensure the message is delivered to the queue.
    If the message is not delivered to the queue, the listener will throw an error.
    If the message is delivered to the queue, the listener will print the message.
    If the connection is disconnected, the listener will print a message.
    If the connection is error, the listener will print a message.
    If the connection is disconnected, the listener will print a message.
    """

    # Thread to wait for the receipt message
    def __init__(self, thread):
        self.thread = thread

    def on_receipt(self, frame):
        logger.info(f"ReceiptListener Receipt received: {frame.body}, Receipt ID: {frame.headers['receipt-id']}")
        self.thread.set() # Set the thread to True, unblock the thread

    def on_error(self, frame):
        logger.error(f"ReceiptListener Error: {frame.body}")
        logger.error(f"Receipt ID: {frame.headers['receipt-id']}")
        self.thread.set() # Set the thread to True, unblock the thread

    def on_disconnected(self):
        logger.debug("ReceiptListener on Disconnect: Disconnected from ActiveMQ")
        self.thread.set() # Set the thread to True, unblock the thread



class Producer:
    """
    Producer class to send messages to ActiveMQ.
    """


    def __init__(self, host: str, port: int, username: str, password: str, destination: str):
        """
        Initialize the Producer class.

        Args:
            host: The host of the ActiveMQ server.
            port: The port of the ActiveMQ server.
            username: The username to connect to the ActiveMQ server.
            password: The password to connect to the ActiveMQ server.
            destination: The destination of the message.

        Returns:
            None
        """
        logger.info("Initializing Producer class")
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.destination = destination
        # Create a connection to ActiveMQ
        self.conn = stomp.Connection([(self.host, self.port)])
        # Connect to ActiveMQ
        self.conn.connect(self.username, self.password, wait=True)
        logger.info("Connected to ActiveMQ")
        # Create a thread to wait for the receipt message
        self.thread = threading.Event()
        # Set the listener for receipt messages and pass the thread to the listener
        self.conn.set_listener('', ReceiptListener(self.thread))
        logger.info("Listener set for receipt messages")
    
    
    def send_message(self, message: str):
        """
        Send a message to the ActiveMQ queue.

        Args:
            message: The message to send to the ActiveMQ queue.

        Returns:
            None
        """
        logger.info(f"Sending message to ActiveMQ: {message}")
        self.conn.send(body=message, destination=self.destination, headers={'receipt': str(uuid.uuid4())})
        # Wait for the receipt message
        self.thread.wait(timeout = 5)
        # Clear the thread, so it can be used again
        self.thread.clear()
        logger.info(f"Message sent to ActiveMQ: {message}")

    def close_connection(self):
        """
        Close the connection to ActiveMQ.

        Args:
            None

        Returns:
            None
        """
        self.conn.disconnect()
        logger.info("Connection closed")




def main():
    load_dotenv()
    HOST = os.getenv('HOST')
    PORT = os.getenv('PORT')
    USERNAME = os.getenv('USERNAME')
    PASSWORD = os.getenv('PASSWORD')
    DESTINATION = '/queue/test3'

    producer = Producer(
        host=HOST, 
        port=PORT, 
        username=USERNAME, 
        password=PASSWORD, 
        destination=DESTINATION)

    producer.send_message("Hello, from Producer3!")

    producer.send_message("Hello, from Producer4!")
# Clear the thread, so it can be used again
    producer.close_connection()

if __name__ == "__main__":
    main()