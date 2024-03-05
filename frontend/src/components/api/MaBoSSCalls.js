import {checkAuthorization, makeCancelable, getDefaultHeaders, extractFilename} from "./commons";
import FileSaver from "file-saver";

class MaBoSSCalls {


	static getMaBoSSNodes(project_id, model_id) {

		return makeCancelable(
			fetch(
				"/api/logical_model/" + project_id + "/" + model_id + "/nodes",
				{
					method: "get",
					headers: getDefaultHeaders()
				}
			).then(response => checkAuthorization(response))
			.then(response => response.json())
		);
	}

	static addMaBoSSNode(project_id, model_id, node) {

		const body = new FormData();
		body.append('name', node);

		return makeCancelable(
			fetch(
				"/api/logical_model/" + project_id + "/" + model_id + "/nodes",
				{
					method: "post",
					body: body,
					headers: getDefaultHeaders()
				}
			).then(response => checkAuthorization(response))
		);
	}

	static deleteMaBoSSNode(project_id, model_id, node) {

		const body = new FormData();
		body.append('name', node);

		return makeCancelable(
			fetch(
				"/api/logical_model/" + project_id + "/" + model_id + "/nodes",
				{
					method: "delete",
					body: body,
					headers: getDefaultHeaders()
				}
			).then(response => checkAuthorization(response))
			.then(response => response.json())

		);
	}

	static getMaBoSSNodesFormulas(project_id, model_id) {
		return makeCancelable(
			fetch(
				"/api/logical_model/" + project_id + "/" + model_id + "/formulas",
				{
					method: "get",
					headers: getDefaultHeaders()
				}
			).then(response => checkAuthorization(response))
			.then(response => response.json())
			.then(response => JSON.parse(response))
		);
	}

	static getMaBoSSNodesFormula(project_id, model_id, node, field) {
		return makeCancelable(
			fetch(
				"/api/logical_model/" + project_id + "/" + model_id + "/formula/" + node + "/" + field,
				{
					method: "get",
					headers: getDefaultHeaders()
				}
			).then(response => checkAuthorization(response))
			.then(response => response.json())
		);
	}

	static saveMaBoSSNodesFormula(project_id, model_id, node, field, formula) {

		const body = new FormData();
		body.append('formula', formula);

		return makeCancelable(
			fetch(
				"/api/logical_model/" + project_id + "/" + model_id + "/formula/" + node + "/" + field,
				{
					method: "post",
					body: body,
					headers: getDefaultHeaders()
				}
			).then(response => checkAuthorization(response))
		);
	}

	static deleteMaBoSSFormula(project_id, model_id, node, field) {

		return makeCancelable(
			fetch(
				"/api/logical_model/" + project_id + "/" + model_id + "/formula/" + node + "/" + field,
				{
					method: "delete",
					headers: getDefaultHeaders()
				}
			).then(response => checkAuthorization(response))
		);
	}

	static checkFormula(project_id, model_id, node, field, formula) {

		const body = new FormData();
		body.append('formula', formula);

		return makeCancelable(
			fetch(
				"/api/logical_model/" + project_id + "/" + model_id + "/check_formula/" + node + "/" + field,
				{
					method: "post",
					body: body,
					headers: getDefaultHeaders()
				}
			).then(response => checkAuthorization(response))
			.then(response => response.json())
		);
	}


	static checkDeleteMaBoSSFormula(project_id, model_id, node, field) {

		return makeCancelable(
			fetch(
				"/api/logical_model/" + project_id + "/" + model_id + "/check_formula/" + node + "/" + field,
				{
					method: "delete",
					headers: getDefaultHeaders()
				}
			).then(response => checkAuthorization(response))
			.then(response => response.json())

		);
	}

	static getMaBoSSParameters(project_id, model_id) {
		return makeCancelable(
			fetch(
				"/api/logical_model/" + project_id + "/" + model_id + "/parameters",
				{
					method: "get",
					headers: getDefaultHeaders()
				}
			).then(response => checkAuthorization(response))
			.then(response => response.json())
			.then(response => JSON.parse(response))
		);
	}

	static getMaBoSSParameter(project_id, model_id, name) {
		return makeCancelable(
			fetch(
				"/api/logical_model/" + project_id + "/" + model_id + "/parameter/" + name,
				{
					method: "get",
					headers: getDefaultHeaders()
				}
			).then(response => checkAuthorization(response))
			.then(response => response.json())
		);
	}


	static saveMaBoSSParameter(project_id, model_id, name, value) {

		const body = new FormData();
		body.append('value', value);

		return makeCancelable(
			fetch(
				"/api/logical_model/" + project_id + "/" + model_id + "/parameter/" + name,
				{
					method: "post",
					body: body,
					headers: getDefaultHeaders()
				}
			).then(response => checkAuthorization(response))
		);
	}

	static deleteMaBoSSParameters(project_id, model_id, name) {

		return makeCancelable(
			fetch(
				"/api/logical_model/" + project_id + "/" + model_id + "/parameter/" + name,
				{
					method: "delete",
					headers: getDefaultHeaders()
				}
			).then(response => checkAuthorization(response))
		);
	}

	static checkMaBoSSParameter(project_id, model_id, name, value) {

		const body = new FormData();
		body.append('value', value);

		return makeCancelable(
			fetch(
				"/api/logical_model/" + project_id + "/" + model_id + "/check_parameter/" + name,
				{
					method: "post",
					body: body,
					headers: getDefaultHeaders()
				}
			).then(response => checkAuthorization(response))
			.then(response => response.json())

		);
	}

	static checkDeleteMaBoSSParameters(project_id, model_id, name) {

		return makeCancelable(
			fetch(
				"/api/logical_model/" + project_id + "/" + model_id + "/check_parameter/" + name,
				{
					method: "delete",
					headers: getDefaultHeaders()
				}
			).then(response => checkAuthorization(response))
			.then(response => response.json())

		);
	}

	static getMaBoSSInitialStates(project_id, model_id) {
		return makeCancelable(
			fetch(
				"/api/logical_model/" + project_id + "/" + model_id + "/initial_states",
				{
					method: "get",
					headers: getDefaultHeaders()
				}
			).then(response => checkAuthorization(response))
			.then(response => response.json())
		);
	}

	static saveMaBoSSInitialStates(project_id, model_id, initial_states) {

		const body = new FormData();
		body.append('initialStates', JSON.stringify(initial_states));

		return makeCancelable(
			fetch(
				"/api/logical_model/" + project_id + "/" + model_id + "/initial_states",
				{
					method: "put",
					body: body,
					headers: getDefaultHeaders()
				}
			).then(response => checkAuthorization(response))
		);
	}

	static getMaBoSSModelOutputs(project_id, model_id) {
		return makeCancelable(
			fetch(
				"/api/logical_model/" + project_id + "/" + model_id + "/outputs",
				{
					method: "get",
					headers: getDefaultHeaders()
				}
			).then(response => checkAuthorization(response))
			.then(response => response.json())
		);
	}

	static setMaBoSSModelOutputs(project_id, model_id, outputs) {

		const body = new FormData();
		body.append('outputs', JSON.stringify(outputs));

		return makeCancelable(
			fetch(
				"/api/logical_model/" + project_id + "/" + model_id + "/outputs",
				{
					method: "put",
					body: body,
					headers: getDefaultHeaders()
				}
			).then(response => checkAuthorization(response))
		);
	}

	static getMaBoSSModelSettings(project_id, model_id) {
		return makeCancelable(
			fetch(
				"/api/logical_model/" + project_id + "/" + model_id + "/settings",
				{
					method: "get",
					headers: getDefaultHeaders()
				}
			).then(response => checkAuthorization(response))
			.then(response => response.json())
		);
	}

	static updateMaBoSSModelSettings(project_id, model_id, settings) {

		const body = new FormData();
		body.append('settings', JSON.stringify(settings));

		return makeCancelable(
			fetch(
				"/api/logical_model/" + project_id + "/" + model_id + "/settings",
				{
					method: "put",
					body: body,
					headers: getDefaultHeaders()
				}
			).then(response => checkAuthorization(response))
		);
	}

	static createMaBoSSSimulation(project_id, model_id, data) {

		const formData = new FormData();
		formData.append('name', data.name);
		formData.append('settings', JSON.stringify(data.settings));
		formData.append('initialStates', JSON.stringify(data.initialStates));
		formData.append('outputVariables', JSON.stringify(data.outputVariables));
		formData.append('mutations', JSON.stringify(data.mutations));

		if (data.serverHost !== null && data.serverPort !== null) {
			formData.append('serverHost', data.serverHost);
			formData.append('serverPort', data.serverPort);
		}

		return makeCancelable(
			fetch(
				"/api/logical_model/" + project_id + "/" + model_id + "/maboss",
				{
					method: "post",
					body: formData,
					headers: getDefaultHeaders()
				}
			).then(response => checkAuthorization(response))
			.then(response => response.json())
		);
	}

	static getMaBoSSSimulationSettings(project_id, model_id) {
		return makeCancelable(
			fetch(
				"/api/logical_model/" + project_id + "/" + model_id + "/maboss/settings/",
				{
				  method: "get",
				  headers: getDefaultHeaders()
				}
			).then(response => checkAuthorization(response))
			.then(response => response.json())
		);
	}

	static getListOfMaBoSSSimulations(project_id, model_id) {

		return makeCancelable(
			fetch(
				"/api/logical_model/" + project_id + "/" + model_id + "/maboss",
				{
				  method: "get",
				  headers: getDefaultHeaders()
				}
			).then(response => checkAuthorization(response))
			.then(response => response.json())
		);
	}

	static deleteMaBossSimulation(project_id, simulation_id) {
		return makeCancelable(
			fetch(
				"/api/maboss/" + project_id + "/" + simulation_id + "/",
				{
				  method: "delete",
				  headers: getDefaultHeaders()
				}
			).then(response => checkAuthorization(response))
		);
	}

	static getStatus(project_id, simulation_id) {
		return makeCancelable(
			fetch(
				"/api/maboss/" + project_id + "/" + simulation_id + "/status",
				{
					method: "get",
					headers: getDefaultHeaders()
				}
			).then(response => checkAuthorization(response)
			).then(response => response.json())
		);
	}

	static getFixedPoints(project_id, simulation_id) {
		return makeCancelable(
			fetch(
				"/api/maboss/" + project_id + "/" + simulation_id + "/fixed_points/",
				{
					method: "get",
					headers: getDefaultHeaders()
				}
			).then(response => response.json())
		);
	}

	static getLastStates(project_id, simulation_id) {
		return makeCancelable(
			fetch(
				"/api/maboss/" + project_id + "/" + simulation_id + "/last_states/",
				{
					method: "get",
					headers: getDefaultHeaders()
				}
			).then(response => response.json())
		);
	}
	
	static getNodesProbTraj(project_id, simulation_id) {
		return makeCancelable(
			fetch(
				"/api/maboss/" + project_id + "/" + simulation_id + "/nodes_trajs/",
				{
					method: "get",
					headers: getDefaultHeaders()
				}
			).then(response => checkAuthorization(response))
			.then(response => response.json())
		);
	}

	static getStatesProbTraj(project_id, simulation_id) {
		return makeCancelable(
			fetch(
				"/api/maboss/" + project_id + "/" + simulation_id + "/states_trajs/",
				{
					method: "get",
					headers: getDefaultHeaders()
				}
			).then(response => checkAuthorization(response))
			.then(response => response.json())
		);
	}

	static getPCA(project_id, simulation_id) {
		return makeCancelable(
			fetch(
				"/api/maboss/" + project_id + "/" + simulation_id + "/pca",
				{
					method: "get",
					headers: getDefaultHeaders()
				}
			).then(response => checkAuthorization(response))
			.then(response => response.json())
		);
	}

	static getSSPCA(project_id, simulation_id) {
		return makeCancelable(
			fetch(
				"/api/maboss/" + project_id + "/" + simulation_id + "/sspca",
				{
					method: "get",
					headers: getDefaultHeaders()
				}
			).then(response => checkAuthorization(response))
			.then(response => response.json())
		);
	}

	static createSensitivityAnalysis(project_id, model_id, settings) {
		const formData = new FormData();
		formData.append('settings', JSON.stringify(settings));

		return makeCancelable(
			fetch(
				"/api/logical_model/" + project_id + "/" + model_id + "/maboss_sensitivity",
				{
					method: "post",
					body: formData,
					headers: getDefaultHeaders()
				}
			).then(response => checkAuthorization(response)
			).then(response => response.json())
		);
	}

	static getSensitivityAnalysis(project_id, model_id) {
        return makeCancelable(
            fetch(
				"/api/logical_model/" + project_id + "/" + model_id + "/maboss_sensitivity",
				{
					method: "get",
					headers: getDefaultHeaders()
				}
            ).then(response => checkAuthorization(response)
			).then(response => response.json())
        )
    }


	static deleteSensitivityAnalysis(project_id, analysis_id) {
        return makeCancelable(
            fetch(
				"/api/maboss_sensitivity/" + project_id + "/" + analysis_id + "/",
				{
					method: "delete",
					headers: getDefaultHeaders()
				}
            ).then(response => checkAuthorization(response))
        )
    }

    static getSensitivityAnalysisStatus(project_id, analysis_id) {
        return makeCancelable(
            fetch(
				"/api/maboss_sensitivity/" + project_id + "/" + analysis_id + "/status",
				{
					method: "get",
					headers: getDefaultHeaders()
				}
            ).then(response => checkAuthorization(response)
			).then(response => response.json())
        )
    }

    static getSensitivityAnalysisSteadyStates(project_id, analysis_id) {
        return makeCancelable(
            fetch(
				"/api/maboss_sensitivity/" + project_id + "/" + analysis_id + "/steady_states/",
				{
					method: "get",
					headers: getDefaultHeaders()
				}
            ).then(response => checkAuthorization(response)
			).then(response => response.json())
        )
    }

    static downloadMaBoSSModel(project_id, simulation_id, filetype) {
		return makeCancelable(
			fetch("/api/maboss/" + project_id + "/" + simulation_id + "/" + filetype, {
				method: "get",
				headers: getDefaultHeaders()
			}).then(response => checkAuthorization(response))
			.then(response => Promise.all([
				extractFilename(response.headers.get('content-disposition')),
				response.blob()])
			)
			.then(([filename, blob]) => FileSaver.saveAs(blob, filename))
		)
	}
	static createNewModelFromSimulation(project_id, simulation_id) {
		return makeCancelable(
			fetch(
			"/api/maboss/" + project_id + "/" + simulation_id + "/new_model",
			{
					method: "get",
					headers: getDefaultHeaders()
				}
			).then(response => checkAuthorization(response))
		)
	}
}
export default MaBoSSCalls;