var NodeHelper = require("node_helper");
const { spawn } = require("child_process");
const createLogger = require("./logger");
const { execSync } = require("child_process");

module.exports = NodeHelper.create({
	init(){
		this.LEVELS = {
			info: "info",
			debug: "debug",
			warning: "warn",
			error: "error",
			critical: "error"
		};

		// Initialise with 'info' level until the config is received from the module
		this.logger = createLogger("MMM-MotionSensor Helper", "info");
		this.loggerMMM = createLogger("MMM-MotionSensor", "info");
		this.logger.info("Initialise node_helper.");
		this.pythonProcess = null; // track running process
	},

	start(){
		this.logger.info('Starting node_helper.');
	},
	

	startPython() {
		this.logger.debug("Attempting to start the Python Motion Sensor process.");

		if (this.pythonProcess && !this.pythonProcess.killed) {
			this.logger.debug("Python process already running — skipping start.");
			return;
		}

		const configPayload = {
			off_delay: this.config.off_delay,
			radar_pin: this.config.radar_pin,
			debounce_time: this.config.debounce_time,
			log_level: this.config.debug.level?.toLowerCase() || "info",
			diagnostic: this.config.diagnostic
		};
		const jsonArg = JSON.stringify(configPayload);
		const py = spawn("python3", ["-u", this.path + "/main.py", jsonArg]);
		this.pythonProcess = py;

		// Buffer for partial lines
		let stdoutBuffer = "";
		let stderrBuffer = "";

		const processChunk = (chunk, isStderr = false) => {
			const buffer = isStderr ? stderrBuffer : stdoutBuffer;
			const data = buffer + chunk.toString();
			const lines = data.split(/\r?\n/);
			
			// Save the last partial line back to buffer
			if (isStderr) stderrBuffer = lines.pop();
			else stdoutBuffer = lines.pop();

			lines.forEach(line => {
				line = line.trim();
				if (!line) return;

				try {
					const message = JSON.parse(line);
					if (message.type === "event") {
						this.sendSocketNotification("RADAR_EVENT", message);
						const msgObj = typeof message === "object"
							? JSON.stringify(message, null, 2)
							: message;
						this.logger.debug("Socket Notification sent: " + msgObj);
						return;
					}
				} catch (e) {
					// Not JSON → normal Python log
				}

				// Combine multi-line logs into a single debug entry per chunk
				this.logger.info("Python log: " + line);
			});
		};

		py.stdout.on("data", chunk => processChunk(chunk, false));
		py.stderr.on("data", chunk => processChunk(chunk, true));

		py.on("close", code => {
			// Flush any remaining partial lines
			if (stdoutBuffer.trim()) this.logger.debug("Python log: " + stdoutBuffer.trim());
			if (stderrBuffer.trim()) this.logger.debug("Python log: " + stderrBuffer.trim());

			this.logger.info("Python process exited with code " + code);
			this.pythonProcess = null;
		});
	},


	stop(){
		this.logger.info('Stopping module helper.');
		if (this.pythonProcess && !this.pythonProcess.killed) {
			this.logger.info("Stopping Python process.");
			this.pythonProcess.kill("SIGTERM");
			this.pythonProcess = null;
		}
	},


	socketNotificationReceived(notification, payload) {
		switch (notification) {
			case "CONFIG":
				this.config=payload
				this.debugLevel = this.LEVELS[this.config.debug.level?.toLowerCase()] || "info";
				this.logger = createLogger("MMM-MotionSensor Helper", this.debugLevel);
				this.loggerMMM = createLogger("MMM-MotionSensor", this.debugLevel);
				this.logger.debug("Socket notification Received: " + notification);
				break;
			case "START_RADAR":
				//this.logger.info("Socket notification Received: " + notification);
				if (this.config.diagnostic) {
					this.sendSocketNotification("MESSAGE","Diagnostic Mode")
				} else {
					this.sendSocketNotification("MESSAGE","Motion Detection Running")
				}
				
				this.startPython();
				break;
			case "LOG":
				this.loggerMMM[payload.level]
					? this.loggerMMM[payload.level](payload.message)
					: this.loggerMMM.info(payload.message);
				break;
			default:
				this.logger.info("Unknown Socket Notification Received: " + notification);
		}
	},
});

