Module.register("MMM-MotionSensor", {
	config:null,
	motion:"",
	button:"",
	defaults: {
		message: "Nothing to see here.",
		tvStatus: "TV State Unknown",
		off_delay: 30 ,			// in Seconds
		debounce_time: 2,
		//displayName: "HDMI-1",
		detection_mode: "radar", // radar / button /  both
		button_pin: 17,
		radar_pin: 4,
		diagnostic: false,
		debug: {level: "info"},
		dev: false,

	},

	logToHelper(level, message) {
		this.sendSocketNotification("LOG", { level, message });
		console.log("MMM-MotionSensor:", message);
	},

	// Send a message to the running motion sensor Python process 
	messageToRadar(commandType, radarAction) {
		this.sendSocketNotification("RADAR_COMMAND", (JSON.stringify({
						type: commandType,
						action: radarAction
					}) + "\n"));
	},

	start(){
		//this.logToHelper("info", this.name + " is starting!");
		this.data.header = "Motion Sensor";
	},

	getScripts() {
		return	[]
	}, 

	getStyles() {
		return 	[]
	},

	getHeader() {
		return this.data.header;
	},

	notificationReceived: function(notification, payload, sender) {
		// once everybody is loaded up
		switch (notification) {
			case "ALL_MODULES_STARTED":
				this.logToHelper("debug", "In notification received, all modules started");
				this.sendSocketNotification("CONFIG",this.config);
				this.logToHelper("debug", "Sent a SOCKET notification: CONFIG");

				this.sendSocketNotification("START_RADAR");
				this.logToHelper("debug", "Sent a SOCKET notification: START_RADAR");
				break;
			case "DISPLAY_ON":
				this.messageToRadar("command","DISPLAY_ON");
				break;
			case "DISPLAY_OFF":
				this.messageToRadar("command","DISPLAY_OFF");
				break;
			case "DISPLAY_TOGGLE":
				this.messageToRadar("command","DISPLAY_TOGGLE");
				break;
			case "DISABLE_RADAR": // TODO - Not implimented yet
				this.messageToRadar("command","DISABLE_RADAR");
				break;
			case "ENABLE_RADAR": // TODO - Not implimented yet
				this.messageToRadar("command","ENABLE_RADAR");
				break;
			case "DISABLE_BUTTON": // TODO - Not implimented yet
				this.messageToRadar("command","DISABLE_BUTTON");
				break;
			case "ENABLE_BUTTON": // TODO - Not implimented yet
				this.messageToRadar("command","ENABLE_BUTTON");
				break;
			default:
				//this.logToHelper("info", "Notification received: " + notification);
			}
	},

	socketNotificationReceived: function(notification, payload) {
		switch (notification) {
			case "MESSAGE":
				this.logToHelper("debug", "Received a SOCKET notification: " + notification + " - Payload: " + payload);
				this.config.message = payload;
				this.updateDom();
				break;
			case "SENSOR_EVENT":
				const payloadObj = typeof payload === "object"
                	? JSON.stringify(payload, null, 2) : payload;
				this.logToHelper("debug","Received a SOCKET notification: " + notification + " - Payload: " + payloadObj);

				if (payload.event.includes("Display")){
					this.config.tvStatus = payload.event;
					this.sendNotification ("TV_STATUS", { status: payload.event});
					this.updateDom();
				}

				if (payload.event.includes("Motion") && this.config.diagnostic){
					this.motion = payload.event;
					this.updateDom();
				}
				if (payload.event.includes("Button") && this.config.diagnostic){
					this.button = payload.event;
					this.updateDom();
				}
				break;

			default:
				this.logToHelper("info","Unknown Socket Notification Received: " + notification);
		}
	},

	getDom() {
		var wrapper = document.createElement("div");

		var topLine = document.createElement("div");
		if (this.config.diagnostic) {
			topLine.style.color = "white";
		}

		if (this.config.hasOwnProperty("message")) {
			topLine.innerHTML = this.config.message;
		} else {
			topLine.innerHTML = "Hello world!";
		}
		wrapper.appendChild(topLine);

		// Second line: tvStatus
		if (this.config.hasOwnProperty("tvStatus")) {
			var status = document.createElement("div");
			if (this.config.diagnostic) {
				status.style.color = "white";
			}
			status.innerHTML = this.config.tvStatus;
			wrapper.appendChild(status);
		}

		// Motion line
		if (this.config.diagnostic) {
			var status = document.createElement("div");
			status.style.color = "white";
			status.innerHTML = this.motion;
			wrapper.appendChild(status);
		}
		
		// Button line
		if (this.config.diagnostic) {
			var status = document.createElement("div");
			status.style.color = "white";
			status.innerHTML = this.button;
			wrapper.appendChild(status);
		}
    	return wrapper;
	},

})
