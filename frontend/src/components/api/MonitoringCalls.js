import {checkAuthorization, makeCancelable, getDefaultHeaders} from "./commons";


function getJSON(url) {
	return makeCancelable(
		fetch(url, {method: "get", headers: getDefaultHeaders()})
		.then(response => checkAuthorization(response))
		.then(response => response.ok ? response.json() : Promise.reject(response))
	);
}

function postJSON(url, values) {
	const formData = new FormData();
	Object.entries(values).forEach(([key, value]) => formData.append(key, value));

	return makeCancelable(
		fetch(url, {method: "post", body: formData, headers: getDefaultHeaders()})
		.then(response => checkAuthorization(response))
		.then(response => response.ok ? response.json() : Promise.reject(response))
	);
}

function cleanupParameters(kind, days, inactiveOnly) {
	return {kind: kind, days: days, inactive_only: inactiveOnly ? "true" : "false"};
}


class MonitoringCalls {

	// Resolves to true only for administrators
	static isAdmin() {
		return makeCancelable(
			fetch("/api/monitoring/", {method: "get", headers: getDefaultHeaders()})
			.then(response => response.ok ? response.json() : {admin: false})
			.then(response => response.admin === true)
		);
	}

	static getActivity(start, end, period) {
		return getJSON("/api/monitoring/activity?" + new URLSearchParams({start: start, end: end, period: period}));
	}

	static getStorage() {
		return getJSON("/api/monitoring/storage");
	}

	static optimizeStorage() {
		return postJSON("/api/monitoring/storage/optimize", {});
	}

	// The statistics as last computed : {users, computed_at, computing}
	static getUsers() {
		return getJSON("/api/monitoring/users");
	}

	// Computes them again, in the background
	static computeUsers() {
		return postJSON("/api/monitoring/users", {});
	}

	static getCleanupPreview(kind, days, inactiveOnly) {
		return getJSON("/api/monitoring/cleanup?" + new URLSearchParams(cleanupParameters(kind, days, inactiveOnly)));
	}

	// Deletes a batch : to call again until nothing is left
	static cleanup(kind, days, inactiveOnly) {
		return postJSON("/api/monitoring/cleanup", cleanupParameters(kind, days, inactiveOnly));
	}
}

export default MonitoringCalls;
