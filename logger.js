// logger.js
const winston = require("winston");
const path = require("path");
const os = require("os");
const fs = require("fs");

const directoryName = "log/MotionSensor";
const fileName = "MMM-MotionSensor_Log.log"

// Configure custom colors for log levels
winston.addColors({
  error: 'red',
  warn: 'yellow',
  info: 'green',
  debug: 'cyan'  // Changed from default blue to cyan for better visibility
});

const LEVELS = {
  info: "info",
  debug: "debug",
  warning: "warn",
  error: "error",
  critical: "error"
};

const logDir = path.join(os.homedir(), directoryName);
fs.mkdirSync(logDir, { recursive: true });

const timestampFormat = winston.format.timestamp({ format: "YYYY-MM-DD HH:mm:ss.SSS" });

const fileFormat = moduleName =>
  winston.format.combine(
    timestampFormat,
    winston.format.printf(({ timestamp, level, message }) => {
      const safeMessage = typeof message === "object"
        ? JSON.stringify(message, null, 2) : message;
      return `[${timestamp}] [${level.toUpperCase()}] ${moduleName}: ${safeMessage}`;
    })
  );

const isInteractive = process.stdout.isTTY || process.env.FORCE_CONSOLE === "true";

function createLogger(moduleName = "App", customLevel) {
  const level = customLevel || LEVELS[process.argv[2]?.toLowerCase()] || "info";

  const transports = [
    new winston.transports.File({
      filename: path.join(logDir, fileName),
      maxsize: 1024 * 1024,
      maxFiles: 3,
      tailable: true
    })
  ];

  if (isInteractive) {
    transports.push(
      new winston.transports.Console({
        level,
        format: winston.format.combine(
          timestampFormat,
          winston.format.printf(({ timestamp, level, message }) => {
            const bracketLevel = "[" + level + "]";
            const paddedLevel = bracketLevel.toUpperCase().padEnd(7);
            const safeMessage = typeof message === "object"
                ? JSON.stringify(message, null, 2) : message;
            return `[${timestamp}] ${paddedLevel} ${moduleName}: ${safeMessage}`;
          }),
          winston.format.colorize({
            all: true
          })
        )
      })
    );
  }

  const logger = winston.createLogger({
    level,
    format: fileFormat(moduleName),
    transports
  });

  logger.info(
    isInteractive
      ? `Console logging enabled (interactive mode).`
      : `Running in non-interactive mode — logging to file only.`
  );

  return logger;
}

module.exports = createLogger;
