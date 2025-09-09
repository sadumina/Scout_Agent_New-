import os
import requests

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

def send_slack_alert(message):
    if SLACK_WEBHOOK_URL:
        payload = {"text": message}
        requests.post(SLACK_WEBHOOK_URL, json=payload)
