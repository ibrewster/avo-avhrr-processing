from pathlib import Path

from pyresample import parse_area_file, geometry
from satpy.scene import Scene

from .utils import parse_filename
from .processor import Processor
from .post_volcview import post_image
from . import config

AREA_DEF = f"{config.PPP_CONFIG_DIR}/areas.def"
COVERAGE_THREASHOLD = 0.1


def main(file):
    name_parts = parse_filename(file)

    scn = Scene(reader="avhrr_l1b_aapp", filenames=[file])
    platform = name_parts["platform"]
    scn.load(['longitude', 'latitude'])
    lons = scn['longitude'].values
    lats = scn['latitude'].values
    swath_def = geometry.SwathDefinition(lons=lons, lats=lats)

    for sector_def in parse_area_file(AREA_DEF):
        try:
            coverage = swath_def.overlap_rate(sector_def)
        except TypeError:
            # no overlap
            coverage = 0.0

        print(f"Sector {sector_def.area_id} -> {coverage}")
        if coverage < COVERAGE_THREASHOLD:
            print("Insufficient coverage, aborting")
            continue

        for p in Processor.__subclasses__():
            processor = p(scn, platform)
            filename = processor.filename(sector_def)
            if Path(filename).exists():
                print(f"Skipping {processor.product}, found {filename}")
                continue
            try:
                processor.load_data()
                msg = processor.write_image(sector_def)
                for endpoint in config.VOLCVIEW_SERVERS:
                    pass
                    # response = post_image(endpoint, msg)

                    # if not response.ok:
                    #    print(f"Bad response from volcview at {endpoint}: {response.reason}")
                # Path(filename).unlink()
            except KeyError as e:
                print(f"Something went wrong, will try the next product. ({e})")

    # TODO: determine if we want to archive the data file or something.
    Path(file).unlink()
