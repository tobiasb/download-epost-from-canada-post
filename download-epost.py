import re
import sys
from os import path

import requests
from requests.adapters import HTTPAdapter, Retry

if len(sys.argv) < 2 or len(sys.argv) > 3:
    print(f"Usage: {sys.argv[0]} COOKIE_VALUE [DEST]")
    exit()

cookies = sys.argv[1]

headers = {
    "Cookie": cookies,
}

first_time = True
page_size = 50
offset = 0
num_processed = 0
num_total = 0

s = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
s.mount("https://", HTTPAdapter(max_retries=retries))

response = requests.get("https://www.canadapost-postescanada.ca/inbox/en", headers=headers)

sso_tokens = re.findall('"sso-token" content="([a-z0-9\-]*)"', response.text)
potential_sso_tokens = [token for token in sso_tokens if token]
if not potential_sso_tokens:
    print("Failed getting a SSO token. Are you sure you provided your up to date cookies? 🤔")
    exit()

headers["csrf"] = potential_sso_tokens[0]

while True:
    url = f"https://www.canadapost-postescanada.ca/inbox/rs/mailitem?folderId=0&sortField=1&order=D&offset={offset}&limit={page_size}"
    response = s.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Request to {url} failed with HTTP {response.status_code} 🔥")
        break

    if "content-length" in response.headers and response.headers["content-length"] == "0":
        print("Failed getting a response. Are you sure you provided your up to date cookies? 🤔")
        exit()

    data = response.json()

    if first_time:
        num_total = data["numTotal"]
        first_time = False

    if len(data["mailitemInfos"]) == 0:
        break

    for mail_item in data["mailitemInfos"]:
        desc = mail_item["shortDescription"]
        file_name = f'{desc}.{mail_item["mailItemID"]}.pdf'.replace("/", "-")
        file_location = path.join(sys.argv[2] if len(sys.argv) > 2 else "", file_name)
        if path.exists(file_location):
            print(f"Already downloaded {file_location}, skipping 💪")
            num_processed += 1
            continue

        response = s.get(
            f'https://www.epost.ca/service/displayMailStream.a?importSummaryId={mail_item["mailItemID"]}',
            headers=headers,
        )
        if response.status_code != 200:
            print(f"Downloading {desc} failed with HTTP {response.status_code} 🔥")
            continue
        print(f"Downloaded {file_location} 👍")

        with open(file_location, mode="bw") as f:
            f.write(response.content)

        num_processed += 1

    offset += page_size

print(f"Processed {num_processed} of {num_total}! 🎉")
