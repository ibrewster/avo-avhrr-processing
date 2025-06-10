import glob
import sys

from pathlib import Path

import image_processing

if __name__ == "__main__":
    if len(sys.argv) !=2:
        print(f"Usage: {sys.argv[0]} <filepath>")
        exit(1)
    file_pattern = sys.argv[1]

    # Use glob to find all matching files (works for both single files and patterns)
    matching_files = glob.glob(file_pattern)

    if not matching_files:
        print(f"No files found matching pattern: {file_pattern}")
        exit(2)

    # Convert to Path objects and sort for consistent processing order
    file_paths = sorted([Path(f) for f in matching_files])

    print(f"Processing {len(file_paths)} file(s)...")

    for file_path in file_paths:
        print(f"Processing: {file_path}")
        image_processing.process_avhrr.main(file_path)
