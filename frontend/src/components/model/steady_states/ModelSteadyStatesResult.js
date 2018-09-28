import React, {Component} from "react";
import {FontAwesomeIcon} from "@fortawesome/react-fontawesome";
import { faEye } from '@fortawesome/free-solid-svg-icons';
import LoadingIcon from "../../commons/LoadingIcon";
import Graph from "./Graph";
import APICalls from "../../commons/apiCalls";


class ModelSteadyStatesResult extends Component {

	constructor(props) {
		super(props);

		this.state = {
			data: {},
			loaded: false,
			selectedSteadyState: null,
		};

		this.getSteadyStatesCall = null;
	}

	getSteadyStates(project_id, model_id) {

		this.setState({loaded: false, data: {}, selectedSteadyState: null});

		this.getSteadyStatesCall = APICalls.getSteadyStates(project_id, model_id);
		this.getSteadyStatesCall.promise.then(data => this.setState({data: data, loaded: true, selectedSteadyState: null}));
	}


	toggleGraph(steady_state) {
		if (this.state.selectedSteadyState !== steady_state){
			this.setState({selectedSteadyState: steady_state});
		} else {
			this.setState({selectedSteadyState: null});
		}
	}

	componentDidMount() {
		this.getSteadyStates(this.props.project, this.props.modelId);
	}

	componentWillUnmount() {
		this.getSteadyStatesCall.cancel();
	}

	shouldComponentUpdate(nextProps, nextState) {

		if (nextProps.modelId !== this.props.modelId) {
			this.getSteadyStatesCall.cancel();
			this.getSteadyStates(nextProps.project, nextProps.modelId);
		}

		return (nextState.loaded !== this.state.loaded && nextState.loaded);

	}

	render() {

		if (this.state.loaded && Object.keys(this.state.data).length > 0) {

			return (
				<React.Fragment>
				<table className="table-steadystates">
					<thead><tr>
					{Object.keys(this.state.data[0]).map((key, index) => {
						return <th key={key}
							data-toggle="tooltip" data-placement="top"
					   		title={key}

						><div><span>{key}</span></div></th>
					})}
					<th></th>
					</tr></thead>

					<tbody>
					{this.state.data.map((steady_state, index) => {
						return (
							<tr key={index}>
							{Object.keys(steady_state).map((key, subindex) => {
								if (steady_state[key] > 0) {
									return <td
										key={subindex}
										className="active"
										data-toggle="tooltip"
										data-placement="top"
					   					title={key}
									></td>;
								} else {
									return <td
										key={subindex}
										className="inactive"
										data-toggle="tooltip"
										data-placement="top"
					   					title={key}
									></td>;
								}
							})}
							<td
								className="actions"
							>
								<button
									className="btn btn-primary"

									onClick={() => {this.toggleGraph(steady_state);}}
								>
									<FontAwesomeIcon icon={faEye} size="sm" />
								</button>
							</td>
							</tr>
						)})
					}
					</tbody>
				</table>

				{
					this.state.selectedSteadyState !== null ?
						<React.Fragment>
							<br/><br/>
							<Graph
								project={this.props.project}
								modelId={this.props.modelId}
								steadyState={this.state.selectedSteadyState}
							/>
						</React.Fragment> : null
				}
				</React.Fragment>
			);


		} else {
			return <LoadingIcon width="3rem"/>;
		}

	}
}

export default ModelSteadyStatesResult;