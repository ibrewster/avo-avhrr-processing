# -*- coding: utf-8 -*
# I waive copyright and related rights in the this work worldwide
# through the CC0 1.0 Universal public domain dedication.
# https://creativecommons.org/publicdomain/zero/1.0/legalcode

# Author(s):
#   Tom Parker <tparker@usgs.gov>

import json
import os
import sys

import boto3
from pyresample import parse_area_file
from satpy.scene import Scene

# from satpy.utils import debug_on
from trollsched.satpass import Pass

from . import parse_filename

PPP_CONFIG_DIR = "/mnt/rsdata/trollconfig"
AREA_DEF = f"{PPP_CONFIG_DIR}/areas.def"
COVERAGE_THREASHOLD = 0.1
AVHRR_IMAGE_URL = os.environ["AVHRR_IMAGE_URL"]


def cleanup():
    print("cleaning up")
    os.system("find /mnt/avhrr -mtime +3 -print -exec rm {} \\;")


def lambda_handler(event, context):
    print(f"Received message: {event}")
    msg = json.loads(event["Records"][0]["Sns"]["Message"])
    local_path = msg["local_path"]
    parts = parse_filename(local_path)
    # print(f"parts: {parts}")
    #
    # if not os.path.isfile(local_path):
    #     return {"statusCode": 500, "body": "File isn't there."}
    #
    # # debug_on()
    # filenames = []
    # if parts["resolution"] == "1000m" or parts["resolution"] == "500m":
    #     geo = parts.copy()
    #     geo["resolution"] = "geo"
    #     fn = format_filename(geo)
    #     if os.path.exists(fn):
    #         filenames.extend([local_path, format_filename(geo)])
    #     else:
    #         print(f"Have {parts['resolution']} still waiting on geo file.")
    # elif parts["resolution"] == "geo":
    #     df = parts.copy()
    #     df["resolution"] = "500m"
    #     fn = format_filename(df)
    #     if os.path.exists(fn):
    #         filenames.extend([local_path, fn])
    #     else:
    #         print("Have geo file, still waiting on 500m.")
    #
    #     df["resolution"] = "1000m"
    #     fn = format_filename(df)
    #     if os.path.exists(fn):
    #         filenames.extend([local_path, fn])
    #     else:
    #         print("Have geo file, still waiting on 1000m.")
    #
    #     filenames = list(set(filenames))
    #
    # print(f"filenames: {filenames}")
    # if not filenames:
    #     return {"statusCode": 200, "body": "Still waiting on data"}
    #
    filenames = [msg["local_path"]]
    scn = Scene(reader="avhrr_l1b_aapp", filenames=filenames)
    overpass = Pass(parts["platform"], scn.start_time, scn.end_time, instrument="avhrr")

    print(f"AVHRR IMAGE QUEUE = {AVHRR_IMAGE_URL}")
    queue = boto3.resource("sqs").Queue(AVHRR_IMAGE_URL)
    for sector_def in parse_area_file(AREA_DEF):
        coverage = overpass.area_coverage(sector_def)
        print(f"Sector {sector_def.area_id} -> {coverage}")
        if coverage > COVERAGE_THREASHOLD:
            print("Sufficient coverage, queueing task.")
            queue.send_message(
                MessageGroupId="avhrr",
                MessageBody=json.dumps(
                    {"filenames": filenames, "area_id": sector_def.area_id}
                ),
            )

    return {"statusCode": 200, "body": "Yay!"}


def main():
    event = ""
    for line in sys.stdin:
        event += line.rstrip()
    lambda_handler(json.loads(event), None)


if __name__ == "__main__":
    main()
