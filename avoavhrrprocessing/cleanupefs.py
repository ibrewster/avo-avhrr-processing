#!/usr/bin/env python

# -*- coding: utf-8 -*
# I waive copyright and related rights in the this work worldwide
# through the CC0 1.0 Universal public domain dedication.
# https://creativecommons.org/publicdomain/zero/1.0/legalcode

# Author(s):
#   Tom Parker <tparker@usgs.gov>

""" Purge old files
"""

import os
import shutil
import time

BASE = "/mnt/rsdata/modis"
DAYS = 3


def handler(event, context):
    dir_cnt = 0
    file_cnt = 0
    threshold = time.time() - (DAYS * 24 * 60 * 60)

    for root, dirs, files in os.walk(BASE):
        for dir in dirs:
            path = os.path.join(root, dir)
            if os.stat(path).st_ctime <= threshold:
                print(f"Removing dir {path}")
                shutil.rmtree(path)
                dir_cnt += 1

        for file in files:
            path = os.path.join(root, file)
            if os.stat(path).st_ctime <= threshold:
                print(f"Removing file {path}")
                os.remove(path)
                file_cnt += 1
                print(f"Removing {file} age: {os.stat(path).st_ctime - threshold}")
            else:
                print(f"Skipping {file} age: {os.stat(path).st_ctime - threshold}")

    print(f"Dirs deleted: {dir_cnt}")
    print(f"Files deleted: {file_cnt}")
