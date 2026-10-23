import React from "react";
import {TabContent, TabPane, Nav, NavItem, NavLink, ButtonToolbar, Button, Dropdown, DropdownToggle, DropdownMenu, DropdownItem} from "reactstrap";
import Settings from "../../../Settings";
import MaBoSSLastStates from "./MaBossLastStates";
import MaBossNodesProbTraj from "./MaBossNodesProbTraj";
import MaBossStatesProbTraj from "./MaBossStatesProbTraj";

import classnames from 'classnames';
import APICalls from "../../../api/apiCalls";
import {FontAwesomeIcon} from "@fortawesome/react-fontawesome";
import {faCaretDown} from "@fortawesome/free-solid-svg-icons";
import MaBossSteadyStatesPCA from "./MaBossSteadyStatesPCA";
import MaBossFixedPoints from "./MaBossFixedPoints";
import MaBossObservedGraph from "./MaBossObservedGraph";
import ErrorAlert from "../../../commons/ErrorAlert";
import { isConnected } from "../../../commons/sessionVariables";


class MaBossResult extends React.Component {

	constructor(props){
		super(props);

		this.toggle = this.toggle.bind(this);
		this.state = {
			activeTab: 'ls',
			dropdownOpen: false,

			// fptableLoaded: false,
			// fptable: null,
			
			fixedPoints: null,
			lastStates: null,
			nodesProbTraj: null,
			statesProbTraj: null,
			observedGraph: null,
			observedGraphLoaded: false,

			// pca: null,
			// pcaArrows: null,
			// pcaArrowLabels: null,
			// pcaExplainedVariance: null,

			errors: []
		};

		this.toggleDropdown = this.toggleDropdown.bind(this);
		this.createNewModel = this.createNewModel.bind(this);

		this.createNewModelCall = null;

		this.getStatusCall = null;
		this.getLastStatesCall = null;
		this.getFixedPointsCall = null;
		this.getNodesProbtrajCall = null;
		this.getStateProbtrajCall = null;
		this.getObservedGraphCall = null;
		// this.getPCACall = null;
		this.statusChecker = null;
	}


	getStatus(project_id, simulation_id) {
		if (this.getStatusCall !== null) this.getStatusCall.cancel();
		this.getStatusCall = APICalls.MaBoSSCalls.getStatus(project_id, simulation_id);
		this.getStatusCall.promise.then((data) => {
			if (data.done) {
				clearInterval(this.statusChecker);
				// this.getLastStates(project_id, simulation_id);
				// this.getFixedPoints(project_id, simulation_id);
				// this.getNodesProbtraj(project_id, simulation_id);
				// this.getStateProbtraj(project_id, simulation_id);
				this.getResults(project_id, simulation_id);
				// this.getPCA(project_id, simulation_id);
			}
			if (data.failed) {
				clearInterval(this.statusChecker);
				this.setState({
					lastStates: {}, fixedPoints: {}, nodesProbTraj: {}, statesProbTraj: {},
					observedGraph: null, observedGraphLoaded: true,
					errors: ["Simulation failed : " + data.error]
				})
				
			}
		});
	}
	
	getResults(project_id, simulation_id) {
		this.setState({lastStates: null, fixedPoints: null, nodesProbTraj: null, statesProbTraj: null});
		this.getLastStatesCall = APICalls.MaBoSSCalls.getLastStates(project_id, simulation_id);
		this.getFixedPointsCall = APICalls.MaBoSSCalls.getFixedPoints(project_id, simulation_id);
		this.getNodesProbtrajCall = APICalls.MaBoSSCalls.getNodesProbTraj(project_id, simulation_id);
		this.getStateProbtrajCall = APICalls.MaBoSSCalls.getStatesProbTraj(project_id, simulation_id);
		Promise.all([
			this.getLastStatesCall.promise, this.getFixedPointsCall.promise, 
			this.getNodesProbtrajCall.promise, this.getStateProbtrajCall.promise
		]).then((data) => {
			this.setState({
				lastStates: data[0]['last_states'], fixedPoints: data[1]['fixed_points'], 
				nodesProbTraj: data[2]['nodes_probtraj'], statesProbTraj: data[3]['states_probtraj']
			});
		});

		// Apart, as it's only there when nodes were selected for it
		this.setState({observedGraph: null, observedGraphLoaded: false});
		this.getObservedGraphCall = APICalls.MaBoSSCalls.getObservedGraph(project_id, simulation_id);
		this.getObservedGraphCall.promise.then(
			data => this.setState({observedGraph: data['observed_graph'], observedGraphLoaded: true}),
			error => { if (!error.isCanceled) { this.setState({observedGraph: null, observedGraphLoaded: true}); } }
		);
	}

	// getLastStates(project_id, simulation_id) {
	// 	this.setState({lastStates: null});
	// 	this.getLastStatesCall = APICalls.MaBoSSCalls.getLastStates(project_id, simulation_id);
	// 	this.getLastStatesCall.promise.then(data => {
	// 		this.setState({lastStates: data['last_states']})
	// 	});
	// }


	// getFixedPoints(project_id, simulation_id) {
	// 	this.setState({fixedPoints: null});
	// 	this.getFixedPointsCall = APICalls.MaBoSSCalls.getFixedPoints(project_id, simulation_id);
	// 	this.getFixedPointsCall.promise.then(data => {
			
	// 		this.setState({fixedPoints: data['fixed_points']})
	// 	});
	// }

	// getNodesProbtraj(project_id, simulation_id) {

	// 	this.setState({nodesProbTraj: null});
	// 	this.getNodesProbtrajCall = APICalls.MaBoSSCalls.getNodesProbTraj(project_id, simulation_id);
	// 	this.getNodesProbtrajCall.promise.then(data => {
	// 		this.setState({nodesProbTraj: data['nodes_probtraj']})
	// 	});
	// }

	// getStateProbtraj(project_id, simulation_id) {
	// 	this.setState({statesProbTraj: null});
	// 	this.getStateProbtrajCall = APICalls.MaBoSSCalls.getStatesProbTraj(project_id, simulation_id);
	// 	this.getStateProbtrajCall.promise.then(data => {
	// 		this.setState({statesProbTraj: data['states_probtraj']})
	// 	});
	// }

	// getPCA(project_id, simulation_id) {
	// 	this.setState({pca: null, pcaArrows: null, pcaArrowLabels: null, pcaExplainedVariance: null});
	// 	this.getPCACall = APICalls.MaBoSSCalls.getSSPCA(project_id, simulation_id);
	// 	this.getPCACall.promise.then(data => {
	// 		this.setState({
	// 			pca: JSON.parse(data.data),
	// 			pcaArrows: data.arrows,
	// 			pcaArrowLabels: data.arrowlabels,
	// 			pcaExplainedVariance: data.explainedVariance
	// 		})
	// 	});
	// }

	toggle(tab) {
		if (this.state.activeTab !== tab) {
			this.setState({activeTab: tab});
		}
	}

	toggleDropdown() {
		this.setState({dropdownOpen: !this.state.dropdownOpen});
	}

	createNewModel() {
		this.createNewModelCall = APICalls.MaBoSSCalls.createNewModelFromSimulation(this.props.project, this.props.simulationId);
		this.createNewModelCall.promise.then(response => {
			this.props.getModels(this.props.project);
		});
	}

	componentWillUnmount() {

		if (this.createNewModelCall !== null) {
			this.createNewModelCall.cancel();
		}
		if (this.getStatusCall !== null) {this.getStatusCall.cancel();}
		if (this.getFixedPointsCall !== null) {this.getFixedPointsCall.cancel();}
		if (this.getLastStatesCall !== null) {this.getLastStatesCall.cancel();}
		if (this.getNodesProbtrajCall !== null) {this.getNodesProbtrajCall.cancel();}
		if (this.getStateProbtrajCall !== null) {this.getStateProbtrajCall.cancel();}
		if (this.getObservedGraphCall !== null) {this.getObservedGraphCall.cancel();}
		// if (this.getPCACall !== null) {this.getPCACall.cancel();}

	}

	shouldComponentUpdate(nextProps, nextState, nextContext) {

		if (this.props.simulationId !== nextProps.simulationId && nextProps.simulationId !== null) {
			if (this.getStatusCall !== null) this.getStatusCall.cancel();
			this.setState({
				fixedPoints: null,
				lastStates: null,
				nodesProbTraj: null,
				statesProbTraj: null,
				observedGraph: null,
				observedGraphLoaded: false,
				errors: []
				// pca: null,
				// pcaArrows: null,
				// pcaArrowLabels: null,
				// pcaExplainedVariance: null,
			});
			
			this.statusChecker = setInterval(() => this.getStatus(nextProps.project, nextProps.simulationId), Settings.updateRate);
			this.getStatus(nextProps.project, nextProps.simulationId);
			return false;
		}
		return true;
	}
	render() {
		if (this.props.simulationId !== null) {
			return (
				<React.Fragment>
					<ErrorAlert errorMessages={this.state.errors}/>

					<Nav tabs style={{"justifyContent": "space-between"}}>
						<div className={"d-flex"} style={{"justifyContent": "flex-start"}}>
							<NavItem>
								<NavLink
									onClick={() => this.toggle('ls')}
									className={classnames({ active: this.state.activeTab === 'ls' })}
								>Final state distribution</NavLink>
							</NavItem>
							<NavItem>
								<NavLink
									onClick={() => this.toggle('npt')}
									className={classnames({ active: this.state.activeTab === 'npt' })}
								>Nodes probability trajectories</NavLink>
							</NavItem>
							<NavItem>
								<NavLink
									onClick={() => this.toggle('spt')}
									className={classnames({ active: this.state.activeTab === 'spt' })}
								>States probability trajectories</NavLink>
							</NavItem>
							<NavItem>
								<NavLink
									onClick={() => this.toggle('fp')}
									className={classnames({ active: this.state.activeTab === 'fp' })}
								>Fixed points</NavLink>
							</NavItem>
							<NavItem>
								<NavLink
									onClick={() => this.toggle('og')}
									className={classnames({ active: this.state.activeTab === 'og' })}
								>Observed graph</NavLink>
							</NavItem>
							
							{/* <NavItem>
								<NavLink
									onClick={() => this.toggle('pca')}
									className={classnames({ active: this.state.activeTab === 'pca' })}
								>PCA</NavLink>
							</NavItem> */}
						</div>
						<Dropdown isOpen={this.state.dropdownOpen} toggle={this.toggleDropdown}>
							<DropdownToggle><FontAwesomeIcon icon={faCaretDown}/></DropdownToggle>
							<DropdownMenu right>
								{ isConnected() ? <DropdownItem onClick={() => {this.createNewModel();}}>Save as new model</DropdownItem> : null }
								<DropdownItem onClick={() => {APICalls.MaBoSSCalls.downloadMaBoSSModel(this.props.project, this.props.simulationId, "bnd_file")}}>Download BND file</DropdownItem>
								<DropdownItem onClick={() => {APICalls.MaBoSSCalls.downloadMaBoSSModel(this.props.project, this.props.simulationId, "cfg_file")}}>Download CFG file</DropdownItem>
							</DropdownMenu>
						</Dropdown>
					</Nav>
					<TabContent activeTab={this.state.activeTab}>
						<TabPane tabId="ls">
							<MaBoSSLastStates
								project={this.props.project}
								modelId={this.props.modelId}
								simulationId={this.props.simulationId}
								simulationName={this.props.simulationName}
								fixedPoints={this.state.lastStates}
							/>
						</TabPane>
						<TabPane tabId="npt">
							<MaBossNodesProbTraj
								project={this.props.project}
								modelId={this.props.modelId}
								simulationId={this.props.simulationId}
								simulationName={this.props.simulationName}
								nodesProbas={this.state.nodesProbTraj}
							/>
						</TabPane>
						<TabPane tabId="spt">
							<MaBossStatesProbTraj
								project={this.props.project}
								modelId={this.props.modelId}
								simulationId={this.props.simulationId}
								simulationName={this.props.simulationName}
								statesProbas={this.state.statesProbTraj}
							/>
						</TabPane>
						<TabPane tabId="fp">
							<MaBossFixedPoints
								project={this.props.project}
								modelId={this.props.modelId}
								simulationId={this.props.simulationId}
								simulationName={this.props.simulationName}
								fixedPoints={this.state.fixedPoints}
							/>
						</TabPane>
						<TabPane tabId="og">
							<MaBossObservedGraph
								simulationId={this.props.simulationId}
								simulationName={this.props.simulationName}
								observedGraph={this.state.observedGraph}
								loaded={this.state.observedGraphLoaded}
								active={this.state.activeTab === 'og'}
							/>
						</TabPane>
						{/* <TabPane tabId="pca">
							<MaBossSteadyStatesPCA
								project={this.props.project}
								modelId={this.props.modelId}
								simulationId={this.props.simulationId}
								simulationName={this.props.simulationName}
								data={this.state.pca}
								arrows={this.state.pcaArrows}
								arrowLabels={this.state.pcaArrowLabels}
								explainedVariance={this.state.pcaExplainedVariance}
							/>
						</TabPane> */}
					</TabContent>
				</React.Fragment>
			);
		} else return null;

	}
}

export default MaBossResult;