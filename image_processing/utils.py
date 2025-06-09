import os
from datetime import datetime


def parse_filename(name):
    # /blah/hrpt_noaa19_20220511_1616_68326.l1b
    filename = os.path.basename(name)
    parts = filename.split("_")

    return {
        "path": os.path.dirname(name),
        "filename": filename,
        "platform": "NOAA 18" if parts[1] == "noaa18" else "NOAA 19",
        "date": datetime.strptime(parts[2] + parts[3], "%Y%m%d%H%M"),
        "orbit": parts[4].split(".")[0],
    }


def format_filename(parts):
    filename = "_".join(
        [
            "hrpt",
            "noaa18" if parts["platform"] == "NOAA 18" else "noaa19",
            parts["date"].strftime("%Y%M%D_%H%M"),
            parts["orbit"],
        ]
    )

    return os.path.join(parts["path"], filename + ".l1b")