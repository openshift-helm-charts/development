import os
import sys

import requests

pr_labels = []
xRateLimit = "X-RateLimit-Limit"
xRateRemain = "X-RateLimit-Remaining"


def get_labels(api_url):
    if not pr_labels:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f'Bearer {os.environ.get("BOT_TOKEN")}',
        }
        r = requests.get(api_url, headers=headers)
        pr_data = r.json()

        if xRateLimit in r.headers:
            print(f"[DEBUG] {xRateLimit} : {r.headers[xRateLimit]}")
        if xRateRemain in r.headers:
            print(f"[DEBUG] {xRateRemain}  : {r.headers[xRateRemain]}")

        if "message" in pr_data:
            print(f'[ERROR] getting pr files: {pr_data["message"]}')
            sys.exit(1)
        if "labels" in pr_data:
            for label in pr_data["labels"]:
                pr_labels.append(label["name"])

    return pr_labels
