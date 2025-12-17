Module.register("MMM-MotionSensor", {
	config:null,
	motion:"",
	defaults: {
		message: "Nothing to see here.",
		tvStatus: "TV State Unknown",
		off_delay: 30 ,			//in Seconds
		debounce_time: 2,
		//displayName: "HDMI-1",
		radar_pin: 4,
		diagnostic: false,
		debug: {level: "info"},

	},

	logToHelper(level, message) {
		this.sendSocketNotification("LOG", { level, message });
		console.log("MMM-MotionSensor:", message);
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
		if(notification==="ALL_MODULES_STARTED"){
			this.logToHelper("debug", "In notification received, all modules started");

			this.sendSocketNotification("CONFIG",this.config);
			this.logToHelper("debug", "Sent a SOCKET notification: CONFIG");

			this.sendSocketNotification("START_RADAR");
			this.logToHelper("debug", "Sent a SOCKET notification: START_RADAR");
		} else {
			this.logToHelper("debug", "Notification received: " + notification);
		}
	},

	socketNotificationReceived: function(notification, payload) {
		switch (notification) {
			case "MESSAGE":
				this.logToHelper("debug", "Received a SOCKET notification: " + notification + " - Payload: " + payload);
				this.config.message = payload;
				this.updateDom();
				break;
			case "RADAR_EVENT":
				const payloadObj = typeof payload === "object"
                	? JSON.stringify(payload, null, 2) : payload;
				this.logToHelper("debug","Received a SOCKET notification: " + notification + " - Payload: " + payloadObj);
				if (payload.event.includes("Display")){
					this.config.tvStatus = payload.event;
					this.sendNotification ("TV_STATUS", { status: payload.event});
					this.updateDom();
				}
				if (payload.event.includes("Motion")){ //&& this.config.diagnostic){
					this.motion = payload.event;
					this.updateDom();
				}
				//this.sendNotification ("TV_STATUS", { status: payload.event});
				//this.updateDom();
				break;
			default:
				//this.logToHelper("info","Unknown Socket Notification Received: " + notification);
		}
	},

	// system notification your module is being hidden
	// typically you would stop doing UI updates (getDom/updateDom) if the module is hidden
	suspend(){
	},

	// system notification your module is being unhidden/shown
	// typically you would resume doing UI updates (getDom/updateDom) if the module is shown
	resume(){
	},

	getDom() {
		var wrapper = document.createElement("div");

		var topLine = document.createElement("div");
		if (!this.config.diagnostic) {
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
			if (!this.config.diagnostic) {
				status.style.color = "white";
				status.style.fontSize = "large"
			}
			status.innerHTML = this.config.tvStatus;
			wrapper.appendChild(status);
		}

		// Bottom line: motion
		if (!this.config.diagnostic) {
			var status = document.createElement("div");
			status.style.color = "white";
			status.style.fontSize = "large"
			status.innerHTML = this.motion;
			wrapper.appendChild(status);
		}
    	return wrapper;
	},

})
