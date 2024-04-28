import React from "react";
import {Button, ButtonToolbar, Modal, ModalHeader, ModalBody, ModalFooter, Nav, NavItem, NavLink, TabContent, TabPane } from "reactstrap";
import ImportModelFromCC from "./ImportModelFromCC";
import classnames from 'classnames';
import ImportModelsFromBiomodels from "./ImportModelFromBioModels";
import Switch from "../commons/buttons/Switch";

class ImportModel extends React.Component {

	constructor(props) {
		super(props);

		// this.getModelsListCall = null;
		
		this.state = {
			activeTab: "biomodels",
			useSBMLNames: true
		}
		
		// this.loadModel = this.loadModel.bind(this);
		// this.loadModelCall = null;
		
		
		
		this.toggleTab = this.toggleTab.bind(this);
		this.toggleSBMLNames = this.toggleSBMLNames.bind(this);
		// this.state = {
		// 	format: 'zginml',
		// 	buttonLabel: "Download",
		// 	showSecondButton: false,
		// 	secondButtonLabel: ""
		// };

		// this.dictFormats = {
		// 	'zginml': "Z-GINML (Extended save)",
		// 	'sbml': "SBML qual",
		// 	'maboss': "MaBoSS"
		// }
	}
	
	toggleTab(tab) {
		if (this.state.activeTab !== tab) {
			this.setState({activeTab: tab });
    	}
	}
	
	toggleSBMLNames() {
		this.setState({useSBMLNames: !this.state.useSBMLNames});
	}

	componentDidMount() {
	}
	
	componentWillUnmount() {
	}

	// loadModel(model_id, model_name) {
	// 	this.setState({importing: true})
	// 	let url = APICalls.CellCollective.getSBMLURLFromCC(model_id);
	// 	this.loadModelCall = APICalls.ModelsCalls.importModel(this.props.project, null, model_name, null, url);
	// 	this.loadModelCall.promise.then(() => { 
	// 		this.setState({importing: false});
	// 		this.props.hide();
	// 		this.props.updateParent();
	// 	});
	// }

	render() {
		return <React.Fragment>
			<Modal style={{minWidth: '800px'}}
				isOpen={this.props.status}
				toggle={() => {
					if (this.props.status) { this.props.hide();}
					else { this.props.show(); }
				}}
			>
				<ModalHeader toggle={() => {
					if (this.props.status) { this.props.hide();}
					else { this.props.show(); }
				}}>Import model</ModalHeader>
				<ModalBody>
					<Nav tabs>
						<NavItem>
							<NavLink
								className={classnames({ active: this.state.activeTab === 'biomodels' })}
								onClick={() => { this.toggleTab('biomodels'); }}
							>BioModels</NavLink>
						</NavItem>
						<NavItem>
							<NavLink
								className={classnames({ active: this.state.activeTab === 'cellcollective' })}
								onClick={() => { this.toggleTab('cellcollective'); }}
							>CellCollective</NavLink>
						</NavItem>
						
					</Nav>
					<TabContent activeTab={this.state.activeTab}>
						<br/>
						<TabPane tabId="biomodels" style={{overflowY: "auto", height: '400px', width: '760px', textOverflow: 'ellipsis' }}>
							<ImportModelsFromBiomodels
								project={this.props.project}
								updateParent={this.props.updateParent}
								hide={this.props.hide}
								showErrors={this.props.showErrors}
								useSBMLNames={this.state.useSBMLNames}
							/>
						</TabPane>
						<TabPane tabId="cellcollective" style={{overflowY: "auto", height: '400px', width: '760px', textOverflow: 'ellipsis' }}>
							<ImportModelFromCC
								project={this.props.project}
								updateParent={this.props.updateParent}
								hide={this.props.hide}
								showErrors={this.props.showErrors}
								useSBMLNames={this.state.useSBMLNames}
							/>
						</TabPane>
					</TabContent>
				
				</ModalBody>
				<ModalFooter>
					<div className="container-fluid d-flex justify-content-between">
						<div className="form-group general mr-auto">
						<Switch checked={this.state.useSBMLNames} toggle={this.toggleSBMLNames} id={"use_sbml_names"}/>
						<label className="name" style={{marginLeft: '1em'}}>Use SBML names</label>	
						</div>
						{/* <ButtonToolbar className="d-flex"> */}
						<Button color="danger" className="ml-auto" onClick={() => this.props.hide()}>Close</Button>
						{/* </ButtonToolbar> */}
					</div>
				</ModalFooter>
			</Modal>
		</React.Fragment>;
	}
}

export default ImportModel;