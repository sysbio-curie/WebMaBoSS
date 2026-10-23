// Sizes in bytes, and dates, as displayed on the monitoring page

function formatSize(bytes) {
	const units = ["B", "KB", "MB", "GB", "TB"];
	let value = bytes;
	let unit = 0;
	while (value >= 1000 && unit < units.length - 1) {
		value /= 1000;
		unit++;
	}
	return (unit === 0 ? value : value.toFixed(1)) + " " + units[unit];
}

// With the time (in the browser's time zone) if asked
function formatDate(isoDate, withTime = false) {
	if (isoDate === null) {
		return "never";
	}
	if (!withTime) {
		return isoDate.substring(0, 10);
	}
	const date = new Date(isoDate);
	const pad = value => String(value).padStart(2, "0");
	return date.getFullYear() + "-" + pad(date.getMonth() + 1) + "-" + pad(date.getDate())
		+ " " + pad(date.getHours()) + ":" + pad(date.getMinutes());
}

// YYYY-MM-DD of a date, days before today
function daysAgo(days) {
	const date = new Date();
	date.setDate(date.getDate() - days);
	return date.toISOString().substring(0, 10);
}

export {formatSize, formatDate, daysAgo};
