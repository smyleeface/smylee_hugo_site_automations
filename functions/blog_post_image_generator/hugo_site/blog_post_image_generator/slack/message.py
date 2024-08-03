import json

import requests


def send(url, data):
    print(f"Sending message to Slack: {data}")
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, headers=headers, data=json.dumps(data))
    return response.status_code
