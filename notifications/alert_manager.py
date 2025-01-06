# File: notifications/alert_manager.py

import winsound  # For sound notifications (Windows only)
import logging
from .email_notifications import EmailNotification
import yaml
from pathlib import Path


class NotificationManager:
    def __init__(self):
        # Set up logging configuration
        logging.basicConfig(filename='alerts.log', level=logging.INFO,
                            format='%(asctime)s:%(levelname)s:%(message)s')
        
        # Load email configuration
        self.email_config = self._load_email_config()
        
        # Initialize email notifier if configuration exists
        self.email_notifier = None
        if self.email_config:
            self.email_notifier = EmailNotification(
                smtp_server=self.email_config.get('smtp_server'),
                port=self.email_config.get('port'),
                sender_email=self.email_config.get('sender_email'),
                sender_password=self.email_config.get('sender_password')
            )

    def _load_email_config(self):
        """Load email configuration from config file."""
        config_path = Path('configs/email_config.yaml')
        if config_path.exists():
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        return None

    def notify_console(self, message):
        """Notify message to the console."""
        print(f"Notification: {message}")

    def notify_sound(self, duration=500):
        """Play a sound alert for a given duration (in milliseconds)."""
        # Play a simple beep sound (Windows)
        winsound.Beep(1000, duration)  # Frequency (Hz), Duration (ms)

    def log_alert(self, message):
        """Log the alert message to a file."""
        logging.info(message)

    def alert(self, anomaly_message):
        """Send an alert for an anomaly detected."""
        self.notify_console(anomaly_message)
        self.notify_sound()  # Default duration of 500ms
        self.log_alert(anomaly_message)
        
        # Send email notification if configured
        if self.email_notifier and self.email_config.get('recipient_email'):
            self.email_notifier.send_email(
                recipient_email=self.email_config['recipient_email'],
                subject="CCTV Alert Notification",
                message=anomaly_message
            )