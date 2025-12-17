#!/usr/bin/env python3

import re
import subprocess
import json
import threading
import time
import sys
from logger import logger

# Supported output types (DRM/KMS standard naming)
OUTPUT_REGEX = r"^(HDMI|DP|DVI|VGA|DSI|DPI|LVDS|TV|Composite|CVBS|eDP)[A-Za-z0-9\-]*$"

# Best → worst display selection order
PREFERRED_ORDER = [
	"HDMI", "DP", "DSI", "eDP", "DPI", "LVDS", "TV", "Composite", "CVBS", "VGA", "DVI"
]


class DisplayController:
	def __init__(self, diagnostic: False):
		self.display_type = self.detect_display_server()
		self.base_command = self.build_base_command(self.display_type)
		self.display_is_on = False
		self.lock = threading.Lock()
		self.diagnostic = diagnostic

	# Send structured event JSON to stdout for node_helper to parse.
	#---------------------------------------------------------------
	def emit_event(self, event_type, message):
		payload = {"type": "event", "event": event_type, "message": message}
		print(json.dumps(payload), flush=True)

	# Detect whether we are using Wayland or X11
	#-------------------------------------------
	def detect_display_server(self):
		try:
			sessions_output = subprocess.check_output(
				['loginctl', 'list-sessions', '--no-legend'], 
				text=True
			)

			session_id = None
			for line in sessions_output.strip().splitlines():
				parts = line.split()
				if len(parts) >= 4 and parts[3] == "seat0":
					session_id = parts[0]
					break

			if not session_id:
				return "unknown"

			type_output = subprocess.check_output(
				['loginctl', 'show-session', session_id, '-p', 'Type'],
				text=True
			).strip()

			return type_output.split("=")[1]
		except Exception as e:
			logger.error(f"Failed detecting display server: {e}")
			return "unknown"

	# Select the "best" output based on ranking
	#------------------------------------------
	def select_best_output(self, displays):
		for prefix in PREFERRED_ORDER:
			for d in displays:
				if d["name"].startswith(prefix):
					return d["name"]
		return displays[0]["name"]

	# Parse Wayland (wlroots) display names
	#--------------------------------------
	def get_wayland_displays(self):
		displays = []
		try:
			output = subprocess.check_output(['wlr-randr'], text=True)

			for line in output.splitlines():
				line = line.strip()

				# Matches: HDMI-A-1 "Monitor Name"
				m = re.match(r'^(\S+) "(.*)"$', line)
				if m:
					name = m.group(1)

					# Skip NOOP or headless outputs
					if name.startswith("NOOP") or name.startswith("HEADLESS"):
						continue

					if re.match(OUTPUT_REGEX, name):
						displays.append({"name": name})
			return displays

		except Exception as e:
			logger.error(f"Wayland parsing error: {e}")
			return []

	# Find X11 display number (:0, :0.0 etc)
	#-----------------------------------
	def find_x11_display_number(self):
		try:
			output = subprocess.check_output(["ps", "-eo", "cmd"], text=True)
			for line in output.splitlines():
				if "Xorg" in line:
					m = re.search(r"\s(:[0-9.]+)", line)
					if m:
						return m.group(1)
			return None
		except Exception:
			return None

	# Parse xrandr display names
	#---------------------------
	def get_x11_displays(self, display_number):
		displays = []
		try:
			output = subprocess.check_output(
				['xrandr', '-display', display_number, '--query'],
				text=True
			)

			for line in output.splitlines():
				if " connected" in line:
					parts = line.split()

					# Find first part matching any connector
					match_name = next(
						(p for p in parts if re.match(OUTPUT_REGEX, p)), None
					)

					if match_name:
						displays.append({"name": match_name})

			return displays

		except Exception as e:
			logger.error(f"X11 parse error: {e}")
			return []

	# Build immutable base command for Wayland or X11
	#------------------------------------------------
	def build_base_command(self, display_type):
		# Wayland
		if display_type == "wayland":
			displays = self.get_wayland_displays()
			if not displays:
				logger.error("No Wayland displays found.")
				sys.exit(11)

			name = self.select_best_output(displays)
			logger.info(f"Using Wayland output: {name}")

			return ["/usr/bin/wlr-randr", "--output", name]

		# X11
		if display_type == "x11":
			display_num = self.find_x11_display_number()
			if not display_num:
				logger.error("Failed to determine X11 display number.")
				sys.exit(33)

			displays = self.get_x11_displays(display_num)
			if not displays:
				logger.error("No X11 displays found.")
				sys.exit(44)

			name = self.select_best_output(displays)
			logger.info(f"Using X11 output: {name}")

			return ["/usr/bin/xrandr", "-display", display_num, "--output", name]

		logger.error("Unknown display server type.")
		sys.exit(99)

	# Turn display on/off (thread-safe)
	#----------------------------------
	def set_display(self, on: bool):
		with self.lock:
			if self.display_is_on == on:
				return

			# Correct flags for each compositor:
			if self.display_type == "wayland":
				action_flag = "--on" if on else "--off"
			else:  # X11
				action_flag = "--auto" if on else "--off"

			cmd = self.base_command + [action_flag]

			try:
				if not self.diagnostic:
					logger.debug(f"Running command: {cmd}")
					subprocess.run(cmd, check=True, capture_output=True, text=True)
				else:
					logger.debug(f"Diagnostic mode. NOT running command: {cmd}")

			except subprocess.CalledProcessError as e:
				logger.error(f"Display command failed: {e.stderr.strip()}")
				return

			self.display_is_on = on
			msg = f"{time.strftime('%H:%M:%S')} - Motion {'detected' if on else 'stopped'} - turning display {'ON' if on else 'OFF'}"
			self.emit_event(f"Display {'ON' if on else 'OFF'}", msg)
			logger.info(f"Display {'ON' if on else 'OFF'}")


class MotionHandler:
	def __init__(self, display: DisplayController, radar_device, off_delay=15, debounce=2, diagnostic=False):
		self.display = display
		self.radar = radar_device
		self.off_delay = off_delay
		self.debounce = debounce
		self.last_trigger = 0
		self.timer = None
		self.lock = threading.Lock()
		self.diagnostic = diagnostic

		# Link handlers
		self.radar.when_activated = self.motion_start
		self.radar.when_deactivated = self.motion_end

	def motion_start(self):
		now = time.time()
		if now - self.last_trigger < self.debounce:
			return
		self.last_trigger = now

		with self.lock:
			if self.timer:
				self.timer.cancel()
			logger.debug("Motion detected")
			if self.diagnostic:
				msg = f"{time.strftime('%H:%M:%S')} - Motion detected"
				self.display.emit_event(f"Motion Detected", msg)

			self.display.set_display(True)

	def motion_end(self):
		logger.debug("Motion stopped")
		if self.diagnostic:
			msg = f"{time.strftime('%H:%M:%S')} - Motion Stopped"
			self.display.emit_event(f"Motion Stopped", msg)

		with self.lock:
			if self.timer:
				self.timer.cancel()
			self.timer = threading.Timer(self.off_delay, self.display_off)
			self.timer.start()

	def display_off(self):
		logger.debug("Auto turning OFF display")
		self.display.set_display(False)
