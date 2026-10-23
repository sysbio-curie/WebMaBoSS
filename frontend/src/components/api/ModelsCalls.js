import {checkAuthorization, makeCancelable, getDefaultHeaders, extractFilename} from "./commons";
import FileSaver from "file-saver";

class ModelsCalls {

	static getModels(project_id) {
		return makeCancelable(
			fetch(
				"/api/logical_models/" + project_id + "/", {
					method: "get",
					headers: getDefaultHeaders()
				}
			).then(response => checkAuthorization(response))
			.then(response => response.json())
		);
	}

	static importModel(project_id, file, name, file2, use_sbml_names) {

		const formData = new FormData();
		formData.append('name', name);
		formData.append('use_sbml_names', use_sbml_names);
		formData.append('file', file);
		if (file2 !== undefined && file2 !== null) {
			formData.append('file2', file2);
		}
		
		return makeCancelable(
			fetch(
				"/api/logical_models/" + project_id + "/",
				{
					method: "post",
					body: formData,
					headers: getDefaultHeaders()
				}
			).then(response => checkAuthorization(response))
		);

	}

	static downloadModelAsZGINML(project_id, model_id, tag) {

		let endpoint = null;
		if (tag === undefined)
			endpoint = "/api/logical_models/" + project_id + "/" + model_id + "/file";
		else
			endpoint = "/api/logical_models/" + project_id + "/" + model_id + "/tags/" + tag + "/file";

		fetch(endpoint, {
			method: "get",
			headers: getDefaultHeaders()
		}).then(response => checkAuthorization(response))
		.then(response => Promise.all([
			extractFilename(response.headers.get('content-disposition')),
			response.blob()])
		)
		.then(([filename, blob]) => FileSaver.saveAs(blob, filename));
	}

	static downloadModelAsSBML(project_id, model_id, tag) {

		let endpoint = null;
		if (tag === undefined)
			endpoint = "/api/logical_models/" + project_id + "/" + model_id + "/sbmlfile";
		else
			endpoint = "/api/logical_models/" + project_id + "/" + model_id + "/tags/" + tag + "/sbmlfile";

		fetch(endpoint, {
			method: "get",
			headers: getDefaultHeaders()
		}).then(response => checkAuthorization(response))
		.then(response => Promise.all([
			extractFilename(response.headers.get('content-disposition')),
			response.blob()])
		)
		.then(([filename, blob]) => FileSaver.saveAs(blob, filename));

	}
	
	static downloadModelAsBNet(project_id, model_id, tag) {

		let endpoint = null;
		if (tag === undefined)
			endpoint = "/api/logical_models/" + project_id + "/" + model_id + "/bnetfile";
		else
			endpoint = "/api/logical_models/" + project_id + "/" + model_id + "/tags/" + tag + "/bnetfile";

		fetch(endpoint, {
			method: "get",
			headers: getDefaultHeaders()
		}).then(response => checkAuthorization(response))
		.then(response => Promise.all([
			extractFilename(response.headers.get('content-disposition')),
			response.blob()])
		)
		.then(([filename, blob]) => FileSaver.saveAs(blob, filename));

	}

	static downloadModelAsMaBoSS(project_id, model_id, tag, file_id) {

		let endpoint = null;
		let filetype = null;
		if (file_id === 0) {
			filetype = "bndfile";
		} else {
			filetype = "cfgfile";
		}

		if (tag === undefined)
			endpoint = "/api/logical_models/" + project_id + "/" + model_id + "/" + filetype;
		else
			endpoint = "/api/logical_models/" + project_id + "/" + model_id + "/tags/" + tag + "/" + filetype;

		fetch(endpoint, {
			method: "get",
			headers: getDefaultHeaders()
		}).then(response => checkAuthorization(response))
		.then(response => Promise.all([
			extractFilename(response.headers.get('content-disposition')),
			response.blob()])
		)
		.then(([filename, blob]) => FileSaver.saveAs(blob, filename));
	}

}
export default ModelsCalls;