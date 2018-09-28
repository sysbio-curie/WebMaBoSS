import React from "react";
import ModelPage from "../ModelPage";
import ModelName from "../ModelName";

import MaBossResult from "./MaBossResult";
import MaBossActions from "./MaBossActions";

import {ProjectContext, ModelContext} from "../../context";
import APICalls from "../../commons/apiCalls";


class MaBoss extends React.Component {

	constructor(props) {
		super(props);

		this.state = {
			simulationId: null,
		};

		this.onSubmit = this.onSubmit.bind(this);
		this.onSubmitOldSim = this.onSubmitOldSim.bind(this);

		this.createMaBossSimulationCall = null;
	}

	onSubmit(project_id, model_id, data) {
		this.setState({simulationId: null});
		this.createMaBossSimulationCall = APICalls.createMaBoSSSimulation(project_id, model_id, data);
		this.createMaBossSimulationCall.promise.then(data => {
			this.setState({showNewSimForm: false, simulationId: data['simulation_id']})
		});

	}

	onSubmitOldSim(data) {
		this.setState({showOldSimForm: false, simulationId: data});
	}

	componentWillUnmount() {
		if (this.createMaBossSimulationCall !== null) this.createMaBossSimulationCall.cancel();
	}

	render() {

		return (
			<ModelPage
				path={this.props.match.path}
				onModelChanged={this.onModelChanged}
			>
				<ProjectContext.Consumer>
					{(projectContext => <ModelContext.Consumer>
						{(modelContext => <React.Fragment>
								<ModelName
									modelName={modelContext.modelName}
								/>
								<MaBossActions
									project={projectContext.project}
									modelId={modelContext.modelId}
									onSubmit={this.onSubmit}
									onSubmitOldSim={this.onSubmitOldSim}
									// listOfSimulations={this.state.listOfSimulations}
									remove={this.removeOldSim}
								/>
								<MaBossResult simulationId={this.state.simulationId}/>
							</React.Fragment>
						)}
						</ModelContext.Consumer>
					)}
				</ProjectContext.Consumer>
			</ModelPage>
		);
	}
}

export default MaBoss;