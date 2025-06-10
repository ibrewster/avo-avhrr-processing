import os
from datetime import datetime


platform_lookup = {
    "noaa18": "NOAA 18",
    "noaa19": "NOAA 19",
    "m01": "Metop-B",
    "m02": "Metop-A",
    "m03": "Metop-C"
}

code_lookup = {
    "NOAA 18": "noaa18",
    "NOAA 19": "noaa19",
    "Metop-A": "M02",
    "Metop-B": "M01",
    "Metop-C": "M03"
}


def parse_filename(name):
    # /blah/hrpt_noaa19_20220511_1616_68326.l1b
    filename = name.name
    parts = filename.split("_")

    return {
        "path": str(name.parent),
        "filename": filename,
        "platform": platform_lookup.get(parts[1].lower(), 'UNKNOWN'),
        "date": datetime.strptime(parts[2] + parts[3], "%Y%m%d%H%M"),
        "orbit": parts[4].split(".")[0],
    }


def format_filename(parts):
    filename = "_".join(
        [
            "hrpt",
            code_lookup.get(parts["platform"], 'unknown'),
            parts["date"].strftime("%Y%M%D_%H%M"),
            parts["orbit"],
        ]
    )

    return os.path.join(parts["path"], filename + ".l1b")
