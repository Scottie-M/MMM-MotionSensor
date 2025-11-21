#!/usr/bin/env python3

from pathlib import Path
import logging, json, sys
from logging.handlers import RotatingFileHandler

HOME = Path.home()
LOG_DIR = HOME / "MotionSensor"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "display_motion.log"
JSON_LOG_FILE = LOG_DIR / "display_motion.json"

# Supported levels
# ----------------
LEVELS = {
	"info":     logging.INFO,
	"debug":    logging.DEBUG,
	"warning":  logging.WARNING,
	"error":    logging.ERROR,
	"critical": logging.CRITICAL,
}


# JSON formatter for optional JSON logs
# -------------------------------------
class JsonFormatter(logging.Formatter):
	def format(self, record):
		log_record = {
			"timestamp": self.formatTime(record, "%Y-%m-%d %H:%M:%S"),
			"level": record.levelname,
			"message": record.getMessage(),
			"module": record.module,
			"function": record.funcName,
			"line": record.lineno,
			"process": record.process,
		}
		return json.dumps(log_record)


# Create base logger (level will be set later)
# --------------------------------------------
logger = logging.getLogger("radar")
logger.setLevel(logging.INFO)   # temporary default


# Rotating text log file
# ----------------------
file_handler = RotatingFileHandler(
	LOG_FILE,
	maxBytes=1024*1024,
	backupCount=2
)
file_handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s"))


# Optional JSON log file
# ----------------------
json_handler = RotatingFileHandler(
	JSON_LOG_FILE,
	maxBytes=1024*1024,
	backupCount=2
)
json_handler.setFormatter(JsonFormatter())


# Console output handler
# ----------------------
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter("[%(levelname)s] [radar] %(message)s"))


# Register handlers
# -----------------
logger.addHandler(file_handler)
# logger.addHandler(json_handler)   # enable if needed
logger.addHandler(stream_handler)
for handler in logger.handlers:
    handler.flush = sys.stdout.flush

# Function to externally configure the log level
# ----------------------------------------------
def configure_logger(level_name: str):
	
	level = LEVELS.get(level_name.lower(), logging.INFO)
	logger.setLevel(level)
	logger.info(f"Logger level set to: {level_name}")


__all__ = ["logger", "configure_logger"]
