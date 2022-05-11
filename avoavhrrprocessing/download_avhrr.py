#!/usr/bin/env python

# -*- coding: utf-8 -*
# I waive copyright and related rights in the this work worldwide
# through the CC0 1.0 Universal public domain dedication.
# https://creativecommons.org/publicdomain/zero/1.0/legalcode

# Author(s):
#   Tom Parker <tparker@usgs.gov>

"""Retrieve files from GINA
"""

import json
import os
from datetime import datetime, timedelta
from urllib.parse import urlparse

import boto3
import requests

GINA_URL = "http://nrt-status.gina.alaska.edu/products.json"
BACKFILL_DAYS = 2
CHUNK_SIZE_BYTES = 20 * 1024 * 1024
FILE_PATTERN = "hrpt.*l1b"
AVHRR_L1_DIR = "/mnt/rsdata/avhrr/l1"
AVHRR_L1_TOPIC = os.environ["AVHRR_L1_TOPIC"]


def list_gina_avhrr():
    print("Fetching list of available files from GINA")
    end_date = datetime.utcnow() + timedelta(days=1)
    start_date = datetime.utcnow() - timedelta(days=BACKFILL_DAYS)
    payload = {
        "action": "index",
        "commit": "Get Products",
        "controller": "products",
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "sensors[]": "avhrr",
        "processing_levels[]": "level1",
        # "facilities[]": "uafgina",
    }

    r = requests.get(GINA_URL, params=payload)
    print(f"URL: {r.url}")

    files = json.loads(r.text)
    for file in files:
        file["local_path"] = os.path.join(
            AVHRR_L1_DIR, urlparse(file["url"]).path.lstrip("/")
        )

    return files


def download_file(url, path):
    print(f"Downloading {url} to {path}")
    # basename = os.path.basename(path)
    dirname = os.path.dirname(path)
    if not os.path.exists(dirname):
        print(f"Creating {dirname}")
        os.makedirs(dirname)
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)


def lambda_handler(event, context):
    new_files = [f for f in list_gina_avhrr() if not os.path.exists(f["local_path"])]
    print(f"found new {len(new_files)} files")
    for file in new_files:
        try:
            download_file(file["url"], file["local_path"])
        except Exception as e:  # NOQA: E722
            print(e)
            print("Download unsuccessful. I'll clean up and continue.")
            if os.path.isfile(file["local_path"]):
                print(f"Removing partial download {file['local_path']}")
                os.unlink(file["local_path"])
        else:
            boto3.client("sns").publish(
                TargetArn=AVHRR_L1_TOPIC, Message=json.dumps(file)
            )
    return {"statusCode": 200, "body": json.dumps("Hello from Lambda!")}


def main():
    lambda_handler(None, None)


if __name__ == "__main__":
    main()
