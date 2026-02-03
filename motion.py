#!/usr/bin/env python3

import time, sys, json, threading
from signal import pause
from gpiozero import DigitalInputDevice, Button
from display_controller import DisplayController, MotionHandler
from logger import logger, configure_logger

# Default Hardware Configuration (override via JSON)
# --------------------------------------------------
DEFAULT_CONFIG = {
    "detection_mode": "button",   # "motion" | "button" | "both"
    "button_pin": 17,
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
                    "detection_mode": incoming.get("detection_mode", config["detection_mode"]),
                    "button_pin": incoming.get("button_pin", config["button_pin"]),
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
    for line in sys.stdin:
        try:
            msg = json.loads(line.strip())
            if msg.get("type") == "command":
                action = msg.get("action")
                if action == "DISPLAY_ON":
                    logger.info("Received command from Node: DISPLAY_ON")
                    if not display.display_is_on :
                        if motion:
                            motion.motion_start()
                        else:
                            display.set_display(True)
                elif action == "DISPLAY_OFF":
                    logger.info("Received command from Node: DISPLAY_OFF")
                    if display.display_is_on:
                        if motion:
                            motion.motion_end(True)
                        else:
                            display.set_display(False)
                elif action == "DISPLAY_TOGGLE":
                    logger.info("Received command from Node: DISPLAY_TOGGLE")
                    if display.display_is_on:
                        if motion:
                            motion.motion_end(True)
                        else:
                            display.set_display(False)
                    else:
                        if motion:
                            motion.motion_start()
                        else:
                            display.set_display(True)

                elif action == "DISABLE_RADAR":
                    logger.info("TODO Received command from Node: DISABLE_RADAR")
                    #TODO
                elif action == "ENABLE_RADAR":
                    logger.info("TODO Received command from Node: ENABLE_RADAR")
                    #TODO
                elif action == "DISABLE_BUTTON":
                    logger.info("TODO Received command from Node: DISABLE_BUTTION")
                    #TODO
                elif action == "ENABLE_BUTTON":
                    logger.info("TODO Received command from Node: ENABLE_BUTTON")
                    #TODO
        except Exception as e:
            logger.error(f"Command parse error: {e}")


def start_motion_handler(config, display):

    RADAR_PIN = config["radar_pin"]
    OFF_DELAY = config["off_delay"]
    DEBOUNCE_TIME = config["debounce_time"]
    DIAGNOSTIC = config["diagnostic"]
    DEV = config["dev"]

    if DIAGNOSTIC:
        logger.info(f"Diagnostic state is active")
    logger.info("Motion input enabled")


    # Initialize radar sensor
    # ------------------------
    try:
        radar = DigitalInputDevice(RADAR_PIN)
    except Exception as e:
        logger.error(f"Failed to initialize radar sensor: {e}")
        return None, None

    logger.debug(f"Initial radar state: {'ACTIVE' if radar.is_active else 'inactive'}")

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

    return motion, radar


def button_control(config, display, motion):
    
    # Momentary button control:
    # Short press toggles display ON/OFF
    # ----------------------------------
    DETECTION_MODE = config["detection_mode"]
    BUTTON_PIN = config["button_pin"]
    DIAGNOSTIC = config["diagnostic"]
    DEV = config["dev"]

    if DIAGNOSTIC:
        logger.info(f"Diagnostic state is active")
    logger.info("Button input enabled")

    try:
        button = Button(
            BUTTON_PIN,
            pull_up=True,   # typical for tactile switches
            bounce_time=0.1 # hardware debounce
        )
    except Exception as e:
        logger.error(f"Failed to initialize button on GPIO {BUTTON_PIN}: {e}")
        msg = f"{time.strftime('%H:%M:%S')} - Failed to initialize button on GPIO {BUTTON_PIN}"
            display.emit_event(f"error", f"Button Initialisation Error", msg)

        return

    def handle_press():
        logger.info("Button pressed")

        if DIAGNOSTIC:
            msg = f"{time.strftime('%H:%M:%S')} - Button pressed"
            display.emit_event(f"event", f"Button Pressed", msg)

        # Toggle display
        if motion:
            if display.display_is_on:
                motion.motion_end(no_delay=True)
            else:
                motion.motion_start()
        else:
            if display.display_is_on:
                display.set_display(False)
            else:
                display.set_display(True)

    # Startup behavior
    # -----------------
    if DETECTION_MODE == "button":
        display.set_display(False)

    button.when_pressed = handle_press

    logger.info(f"Button control active on GPIO {BUTTON_PIN}")


def run():
    config = load_config()
    configure_logger(config["log_level"])

    DETECTION_MODE = config["detection_mode"]
    BUTTON_PIN = config["button_pin"]
    RADAR_PIN = config["radar_pin"]
    DIAGNOSTIC = config["diagnostic"]
    DEV = config["dev"]


    # Initialize display controller (detects Wayland/X11)
    # ----------------------------------------------------
    display = DisplayController(diagnostic=DIAGNOSTIC, dev=DEV)

    logger.info(f"Detected Display Server: {display.display_type}")
    logger.info(f"Base Display Command: {display.base_command}")

    motion = None
    radar = None

    if DETECTION_MODE in ("motion", "both") and RADAR_PIN is not None:
        motion, radar = start_motion_handler(config, display)

    if DETECTION_MODE in ("button", "both") and BUTTON_PIN is not None:
        button_control(config, display, motion)

    logger.info(
        f"Detection mode: {DETECTION_MODE} | "
        f"Radar: {'ENABLED' if motion else 'DISABLED'} | "
        f"Button: {'ENABLED' if BUTTON_PIN else 'DISABLED'}"
    )

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


run()
