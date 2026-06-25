import requests
from config import NTFY_TOPIC

def notify(title: str, message: str) -> str:
    if not NTFY_TOPIC:
        return "Notifications disabled"
    try:
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=message.encode("utf-8"),
            headers={"Title": title, "Priority": "high"},
            timeout=10,
        )
        return f"{title}: {message}"
    except Exception as e:
        return f"Notification failed: {e}"
