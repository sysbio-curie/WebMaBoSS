import React from "react";
import {Button, ButtonToolbar, Modal, ModalHeader, ModalBody, ModalFooter, Nav, NavItem, NavLink, TabContent, TabPane } from "reactstrap";
import classnames from 'classnames';
import ImportModelFromRepository from "./ImportModelFromRepository";
import Switch from "../commons/buttons/Switch";

// Tab, name, and a warning when importing takes long
const REPOSITORIES = [
	["biomodels", "BioModels", null],
	["cellcollective", "Cell Collective", "Cell Collective can take more than a minute to export a model"],
	["ginsim", "GINsim", null],
];

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
						{REPOSITORIES.map(([key, name]) =>
							<NavItem key={key}>
								<NavLink
									className={classnames({ active: this.state.activeTab === key })}
									onClick={() => { this.toggleTab(key); }}
								>{name}</NavLink>
							</NavItem>
						)}
					</Nav>
					<TabContent activeTab={this.state.activeTab}>
						<br/>
						{REPOSITORIES.map(([key, name, slow]) =>
							<TabPane key={key} tabId={key} style={{overflowY: "auto", height: '400px', width: '760px', textOverflow: 'ellipsis' }}>
								{/* Only the list shown is loaded */}
								{ this.state.activeTab === key ?
									<ImportModelFromRepository
										repository={key}
										slow={slow}
										project={this.props.project}
										updateParent={this.props.updateParent}
										hide={this.props.hide}
										showErrors={this.props.showErrors}
										useSBMLNames={this.state.useSBMLNames}
									/> : null
								}
							</TabPane>
						)}
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