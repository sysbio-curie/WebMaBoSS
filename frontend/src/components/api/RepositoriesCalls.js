import {checkAuthorization, makeCancelable, getDefaultHeaders} from "./commons";

// Public repositories of models : biomodels, cellcollective, ginsim
class RepositoriesCalls {

	static getModels(repository) {
		return makeCancelable(
			fetch(
				"/api/repositories/" + repository + "/",
				{
					method: "get",
					headers: getDefaultHeaders()
				}
			).then(response => response.json().then(data => ({ok: response.ok, data: data})))
		);
	}

	static importModel(repository, project_id, model_id, name, use_sbml_names) {
		const formData = new FormData();
		formData.append('model_id', model_id);
		formData.append('name', name);
		formData.append('use_sbml_names', use_sbml_names);

		return makeCancelable(
			fetch(
				"/api/repositories/" + repository + "/" + project_id + "/import",
				{
					method: "post",
					body: formData,
					headers: getDefaultHeaders()
				}
			).then(response => checkAuthorization(response))
			.then(response => response.json().then(data => ({ok: response.ok, data: data})))
		);
	}

	static getImportStatus(project_id, import_id) {
		return makeCancelable(
			fetch(
				"/api/repositories/imports/" + project_id + "/" + import_id,
				{
					method: "get",
					headers: getDefaultHeaders()
				}
			).then(response => checkAuthorization(response))
			.then(response => response.json())
		);
	}
}

export default RepositoriesCalls;
