import json
import os
import urllib.request

SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")


def send_slack_alert(message: str):
    payload = {"text": message}
    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        SLACK_WEBHOOK_URL, data=data, headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req) as response:
            return response.read().decode()
    except Exception as e:
        print("Failed to send Slack alert:", e)


if __name__ == "__main__":
    send_slack_alert(
        "🚨 *Test Alert*\n" "@segin This is a test message from the alerting system."
    )
