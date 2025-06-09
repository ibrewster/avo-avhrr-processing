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

import requests

from . import config

def post_image(endpoint, image_attr):
    headers = {"username": config.VV_USER, "password": config.VV_PASSWORD}
    # print(f"TOMP SAYS :{VV_PASSWORD} :: {VV_USER}")
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
