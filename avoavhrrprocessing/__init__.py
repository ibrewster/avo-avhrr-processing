# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
#  Purpose: process avhrr data
#   Author: Tom Parker
#
# -----------------------------------------------------------------------------
"""
avoavhrrprocessing
=================

:license:
    CC0 1.0 Universal
    http://creativecommons.org/publicdomain/zero/1.0/
"""

import os
from datetime import datetime


def parse_filename(name):
    # /blah/a1.20192.2308.250m.hdf
    filename = os.path.basename(name)
    parts = filename.split(".")
    if parts[0] == "a1":
        platform = "aqua"
    elif parts[0] == "t1":
        platform = "terra"
    else:
        platform = None

    date_str = datetime.strptime(parts[1] + parts[2], "%y%j%H%M")
    return {
        "path": os.path.dirname(name),
        "filename": filename,
        "platform": platform,
        "date": date_str,
        "resolution": parts[3],
    }


def format_filename(parts):
    if parts["platform"] == "aqua":
        platform = "a1"
    elif parts["platform"] == "terra":
        platform = "t1"

    filename = ".".join(
        [platform, parts["date"].strftime("%y%j.%H%M"), parts["resolution"], "hdf",]
    )
    return os.path.join(parts["path"], filename)
