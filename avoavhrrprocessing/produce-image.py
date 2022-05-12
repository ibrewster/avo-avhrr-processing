#!/usr/bin/env python

# -*- coding: utf-8 -*
# I waive copyright and related rights in the this work worldwide
# through the CC0 1.0 Universal public domain dedication.
# https://creativecommons.org/publicdomain/zero/1.0/legalcode

# Author(s):
#   Tom Parker <tparker@usgs.gov>

"""Produce Image
I create a product and place it in a S3 bucket

I read SQS messages with bodies that look like:
{
   "md5":"f9864846a6b11764325b0e9f9277243b",
   "url":"http://nrt-dds-prod.gina.alaska.edu/gilmore/snpp/level1/viirs/2021/05/NPP.20210520.143115.dat.gz/SVI01_npp_d20210520_t1436065_e1437307_b49546_c20210520145326416799_cspp_dev.h5",
   "filename":"SVI01_npp_d20210520_t1436065_e1437307_b49546_c20210520145326416799_cspp_dev.h5",
   "channel":"SVI01",
   "satellite":"snpp",
   "orbit":49546,
   "start":"2021-05-20T14:36:06.500000",
   "end":"1900-01-01T14:37:30.700000",
   "proc_date":"2021-05-20T14:53:26.416799",
   "s3key":"viirs/sdr/snpp/49546/SVI01_npp_d20210520_t1436065_e1437307_b49546_c20210520145326416799_cspp_dev.h5",
   "local path":"/mnt/rsdata/viirs/sdr/snpp/49546/SVI01_npp_d20210520_t1436065_e1437307_b49546_c20210520145326416799_cspp_dev.h5",
   "message":"Yay!",
   "band":"SVI01",
   "platform_name":"SUOMI NPP",
   "status code":200,
   "granule":"npp_d20210520_t1436065_e1437307_b49546",
   "sector":"2kmAKNS",
   "product":"VIS"
}


"""  # NOQA: E501

import json
import os.path
import sys

from pyresample import load_area

from .processor import processor_factory

PPP_CONFIG_DIR = "/mnt/rsdata/trollconfig"
AREA_DEF = f"{PPP_CONFIG_DIR}/areas.def"


def handler(event, context):
    print("starting...")
    print(f"Received event: {event}")
    # debug_on()
    msg = json.loads(event["Records"][0]["body"])
    filenames = msg["filenames"]
    print(f"MSG: {msg}")
    sector_def = load_area(AREA_DEF, msg["area_id"])
    print(f"Checking for products which match {filenames}")
    for p in processor_factory(filenames):
        print(f"Found {p}")
        filename = p.filename(sector_def)
        if os.path.exists(filename):
            print(f"Skipping {p.product}, found {filename}")
            continue
        try:
            p.load_data()
            p.write_image(sector_def)
        except KeyError as e:
            print(f"Something went wrong, will try the next product. ({e})")

    return {"statusCode": 200, "body": "Yay!"}


def main():
    event = ""
    for line in sys.stdin:
        event += line.rstrip()
    handler(json.loads(event), None)


if __name__ == "__main__":
    main()
