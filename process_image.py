#!/shared/apps/avhrr_processing/env/bin/python
import glob
import logging
import os
import sys

from pathlib import Path

import image_processing

logging.basicConfig(
    filename=image_processing.config.LOG_FILE,
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S',
    format='%(asctime)s GINA-AVHRR-PROCESSING-%(levelname)s: %(message)s'
)

logger = logging.getLogger('AVHRRProcessor')
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler(image_processing.config.LOG_FILE)
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    fmt='%(asctime)s GINA-AVHRR-PROCESSING-%(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.propagate = False


if __name__ == "__main__":
    if len(sys.argv) !=2:
        print(f"Usage: {sys.argv[0]} <filepath>")
        exit(1)
    file_pattern = sys.argv[1]

    # Use glob to find all matching files (works for both single files and patterns)
    matching_files = glob.glob(file_pattern)

    if not matching_files:
        logger.error(f"No files found matching pattern: {file_pattern}")
        exit(2)

    # Convert to Path objects and sort for consistent processing order
    file_paths = sorted([Path(f) for f in matching_files])

    logger.info(f"Processing {len(file_paths)} file(s)...")

    for file_path in file_paths:
        logger.info(f"Processing: {file_path}")
        try:
            image_processing.process_avhrr.main(file_path)
        except Exception as e:
            logger.exception("An error occured during processing.")
        logger.info(f"Completed processing {file_path}")

    logger.info("AVHRR Processing complete")
    sys.exit(0)