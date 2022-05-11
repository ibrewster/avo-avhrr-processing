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
    # /blah/hrpt_noaa19_20220511_1616_68326.l1b
    filename = os.path.basename(name)
    parts = filename.split("_")

    date_str = datetime.strptime(parts[2] + parts[3], "%y%m%d%H%M")
    return {
        "path": os.path.dirname(name),
        "filename": filename,
        "platform": parts[1],
        "date": date_str,
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
