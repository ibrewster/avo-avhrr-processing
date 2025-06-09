import sys

from pathlib import Path

import image_processing

if __name__ == "__main__":
    if len(sys.argv) !=2:
        print(f"Usage: {sys.argv[0]} <filepath>")
        exit(1)
        
    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print("Specified file does not exist")
        exit(2)
        
    image_processing.process_avhrr.main(file_path)