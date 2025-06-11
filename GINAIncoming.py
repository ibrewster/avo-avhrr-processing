#!/shared/apps/avhrr_processing/env/bin/python
import logging
import os
import subprocess
import sys
import time

from image_processing import config

FILE_PATH = os.path.dirname(__file__)

# Configure logging for the main incron script
logging.basicConfig(
    filename=config.LOG_FILE,
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S',
    format='%(asctime)s GINA-AVHRR-INCRON-%(levelname)s: %(message)s'
)

PROCESSING_SCRIPT = os.path.join(FILE_PATH, 'process_image.py')

if __name__ == "__main__":
    files = sys.argv[1:] # list of files, probably only one
    
    if not files:
        logging.warning("No files provided by incron.")
        exit(0)

    logging.info("Incron triggered for files: %s", str(files))
    
    for file in files:
        initial_file_size = os.path.getsize(file_path)
        logging.info("Checking file settlement for '%s'. Initial size: %d bytes.", file_path, initial_file_size)
        time.sleep(15) # Wait for file to settle
        current_file_size = os.path.getsize(file_path)
        
        if current_file_size != initial_file_size:
            logging.info("File '%s' transfer still in process (size changed from %d to %d). Not launching processing.", 
                         file_path, initial_file_size, current_file_size)
            exit(1) # Exit if file is not settled
            
        logging.info("File '%s' appears settled. Launching detached process.", file_path)
        
        cmd = [
            'nohup',
            sys.executable,
            PROCESSING_SCRIPT,
            file_path, # Pass the single file path
            '>>', config.LOG_FILE, # Redirect stdout to /dev/null
            '2>&1',           # Redirect stderr to /dev/null as well
            '&'               # Run in background
        ]
        
        subprocess.Popen(" ".join(cmd), shell=True, preexec_fn=os.setsid)
        logging.info("Successfully launched detached proicess for %s", file_path)
        
    logging.info("Incron script finished (launched eligible processing job).")