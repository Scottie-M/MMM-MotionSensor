#!/usr/bin/env python3

import time, sys, json, threading
from signal import pause
from gpiozero import DigitalInputDevice
from display_controller import DisplayController, MotionHandler
from logger import logger, configure_logger

# Default Hardware Configuration (override via JSON)
# --------------------------------------------------
DEFAULT_CONFIG = {
	"radar_pin": 4,
	"off_delay": 5,
	"debounce_time": 2,
	"log_level": "debug",
	"diagnostic": False,
	"dev" : False
}


def load_config():
	# Load configuration from JSON passed as sys.argv[1].
	# Falls back to defaults if missing or invalid.
	# --------------------------------------------------
	config = DEFAULT_CONFIG.copy()

	if len(sys.argv) > 1:
		try:
			incoming = json.loads(sys.argv[1])
			if isinstance(incoming, dict):
				config.update({
					"radar_pin": incoming.get("radar_pin", config["radar_pin"]),
					"off_delay": incoming.get("off_delay", config["off_delay"]),
					"debounce_time": incoming.get("debounce_time", config["debounce_time"]),
					"log_level": incoming.get("log_level", config["log_level"]),
					"diagnostic": incoming.get("diagnostic", config["diagnostic"]),
					"dev": incoming.get("dev", config["dev"])
				})
			else:
				logger.error("JSON argument is not a valid object.")
		except Exception as e:
			logger.error(f"Failed to parse JSON argument: {e}")

	logger.info(f"Loaded configuration: {config}")
	return config

def listen_for_commands(motion, display, radar):
	logger.info("In Listen for commands")
	for line in sys.stdin:
		try:
			msg = json.loads(line.strip())
			if msg.get("type") == "command":
				action = msg.get("action")
				if action == "DISPLAY_ON":
					logger.info("Received command from Node: DISPLAY_ON")
					motion.motion_start()
				elif action == "DISPLAY_OFF":
					logger.info("Received command from Node: DISPLAY_OFF")
					motion.motion_end(True)
				elif action == "DISPLAY_TOGGLE":
					logger.info("Received command from Node: DISPLAY_TOGGLE")
					if display.display_is_on:
						motion.motion_end(True)
					else:
						motion.motion_start()
				elif action == "DISABLE_RADAR":
					logger.info("TODO Received command from Node: DISABLE_RADAR")
					#TODO
				elif action == "ENABLE_RADAR":
					logger.info("TODO Received command from Node: ENABLE_RADAR")
					#TODO
		except Exception as e:
			logger.error(f"Command parse error: {e}")

def motion_control():
	config = load_config()
	configure_logger(config["log_level"])

	RADAR_PIN = config["radar_pin"]
	OFF_DELAY = config["off_delay"]
	DEBOUNCE_TIME = config["debounce_time"]
	DIAGNOSTIC = config["diagnostic"]
	DEV = config["dev"]

	if DIAGNOSTIC:
		logger.info(f"Diagnostic state is active")
	logger.info("Starting Motion-controlled Display Manager...")

	# Initialize radar sensor
	# ------------------------
	try:
		radar = DigitalInputDevice(RADAR_PIN)
	except Exception as e:
		logger.error(f"Failed to initialize radar sensor: {e}")
		return

	logger.debug(f"Initial radar state: {'ACTIVE' if radar.is_active else 'inactive'}")

	# Initialize display controller (detects Wayland/X11)
	# ----------------------------------------------------
	display = DisplayController(diagnostic=DIAGNOSTIC, dev=DEV)

	logger.info(f"Detected Display Server: {display.display_type}")
	logger.info(f"Base Display Command: {display.base_command}")

	# Initialize motion logic
	# ------------------------
	motion = MotionHandler(
		display=display,
		radar_device=radar,
		off_delay=OFF_DELAY,
		debounce=DEBOUNCE_TIME,
		diagnostic=DIAGNOSTIC,
		dev=DEV
	)
	logger.info("Display state:")
	logger.info(display.display_is_on)
	# Startup behavior
	# -----------------
	if radar.is_active:
		logger.info("Motion detected on startup → Turning display ON")
		display.set_display(True)
	else:
		logger.info("No motion detected on startup → Scheduling display OFF")
		time.sleep(1)
		display.set_display(True)
		motion.motion_end()

	logger.info("System Ready. Monitoring motion...")

	# Start listener for commands from the node_helper
	threading.Thread(
		target=listen_for_commands,
		args=(motion, display, radar),
		daemon=True).start()

	# Run until user exits
	# --------------------
	try:
		pause()
	except KeyboardInterrupt:
		logger.info("Shutting down...")
		display.set_display(True)  # Leave display ON on exit

motion_control()


