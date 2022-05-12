#!/usr/bin/env python

# -*- coding: utf-8 -*
# I waive copyright and related rights in the this work worldwide
# through the CC0 1.0 Universal public domain dedication.
# https://creativecommons.org/publicdomain/zero/1.0/legalcode

# Author(s):
#   Tom Parker <tparker@usgs.gov>

"""Post volcview
I send images to volcview

"""  # NOQA: E501

# import io
import json
import os
from datetime import datetime

import boto3
import requests

VV_ENDPOINTS = os.environ["VV_ENDPOINTS"].split(";")
VV_USER = os.environ["VV_USER"]
VV_PASSWORD = os.environ["VV_PASSWORD"]


def get_image(bucket, key):
    client = boto3.client("s3")
    response = client.get_object(Bucket=bucket, Key=key)
    return response["Body"].read()


def post_image(endpoint, image_attr):
    headers = {"username": VV_USER, "password": VV_PASSWORD}
    parts = endpoint.split("|")
    if len(parts) > 1:
        headers["Host"] = parts[0]
        url = parts[1]
    else:
        url = parts[0]

    url += "/imageApi/uploadImage"
    print(f"publishing image to {url}")

    volcview_args = {
        "sector": image_attr["area_id"],
        "band": image_attr["volcview_band"],
        "dataType": "avhrr",
        "imageUnixtime": datetime.fromisoformat(image_attr["start_time"]).timestamp(),
    }
    print(f"data: {volcview_args}")
    files = {
        "file": (os.path.basename(image_attr["file"]), open((image_attr["file"]), "rb"))
    }

    print(f"files: {files}")

    try:
        response = requests.post(
            url,
            headers=headers,
            data=volcview_args,
            files=files,
            #            verify=False,
        )
        print(f"server said: {response.status_code}:{response.text}")
    #        image_size = len(pngimg.getbuffer())
    #        print(f"image size {image_size}")
    except requests.exceptions.RequestException as e:
        print(e)

    return response


def handler(event, context):
    print(f"Received event: {event}")
    msg = json.loads(event["Records"][0]["Sns"]["Message"])
    print(f"Received msg: {msg}")
    status_code = 200
    body = ""
    for endpoint in VV_ENDPOINTS:
        # if not endpoint:
        #     continue
        print(f"Pushing to {endpoint}")
        response = post_image(endpoint, msg)
        if not response.ok:
            print(f"Bad response from volcview at {endpoint}: {response.reason}")
            status_code = response.status_code
            body += f"{endpoint}: {response.reason}\n"

    return {"statusCode": status_code, "body": body}
