from pathlib import Path

from pyresample import parse_area_file
from satpy.scene import Scene
from trollsched.satpass import Pass

from .utils import parse_filename
from .processor import Processor
from .post_volcview import post_image
from . import config

PPP_CONFIG_DIR = "trollconfig"
AREA_DEF = f"{PPP_CONFIG_DIR}/areas.def"
COVERAGE_THREASHOLD = 0.1


def main(file):
    name_parts = parse_filename(file)
    files = [file]

    scn = Scene(reader="avhrr_l1b_aapp", filenames=files)
    platform = name_parts["platform"]
    overpass = Pass(platform, scn.start_time, scn.end_time, instrument="avhrr")

    for sector_def in parse_area_file(AREA_DEF):
        coverage = overpass.area_coverage(sector_def)
        print(f"Sector {sector_def.area_id} -> {coverage}")
        if coverage < COVERAGE_THREASHOLD:
            print("Insufficient coverage, aborting")
            continue

        for p in Processor.__subclasses__():
            p(scn, platform)
            filename = p.filename(sector_def)
            if Path(filename).exists():
                print(f"Skipping {p.product}, found {filename}")
                continue
            try:
                p.load_data()
                msg = p.write_image(sector_def)
                for endpoint in config.VOLCVIEW_SERVERS:
                    response = post_image(endpoint, msg)
                    if not response.ok:
                        print(f"Bad response from volcview at {endpoint}: {response.reason}")
                    else:
                        # image posted. Remove local image
                        Path(filename).unlink()
            except KeyError as e:
                print(f"Something went wrong, will try the next product. ({e})")

    Path(file).unlink
