import React from "react";
import {Button, ButtonToolbar, Modal, Card, CardHeader, CardBody, CardFooter} from "reactstrap";
import APICalls from "../api/apiCalls";
import MyDropdown from "../commons/buttons/MyDropdown";
import Switch from "../commons/buttons/Switch";
import ErrorAlert from "../commons/ErrorAlert";

class ModelForm extends React.Component {

	constructor(props) {
		super(props);

		this.dictFormats = {
			'maboss': "MaBoSS",
			'sbml': "SBML qual",
			'zginml': "GINsim",
			'bnet': "BNet"
			
		};

		this.dictLabels = {
			'zginml': ['Z-GINML file'],
			'bnet': ['BNet file'],
			'maboss': ['BND file', 'CFG file'],
			'sbml': ['SBML file'],
		};

		this.dictExtensions = {
			'zginml': ['.zginml'],
			'maboss': ['.bnd', '.cfg'],
			'sbml': ['.xml, .sbml'],
			'bnet': ['.bnet'],
		};

		this.dictNbFiles = {
			'zginml': 1,
			'maboss': 2,
			'sbml': 1,
			'bnet': 1
		};

		this.state = {
			id: null,
			name: "",
			file: null,
			fileName: "Select file... ",
			file2: null,
			file2Name: "Select file...",
			modal: false,
			type: 'maboss',
			useSBMLNames: true,
			errors: []
		};

		this.toggle = this.toggle.bind(this);
		this.handleNameChange.bind(this);
		this.handleFileChange.bind(this);
		this.handleSubmit.bind(this);
		this.toggleSBMLNames = this.toggleSBMLNames.bind(this);

		this.importModelCall = null;
	}

	toggle() {
		this.setState({modal: !this.state.modal});
	}

	handleNameChange(e) {
		this.setState({name: e.target.value});
	};

	handleFileChange(e) {
		this.setState({file: e.target.files[0], fileName: e.target.files[0].name});
	};

	handleFile2Change(e) {
		this.setState({file2: e.target.files[0], file2Name: e.target.files[0].name});
	};

	handleTypeChange(type) {
		this.setState({type: type})
	}

	handleSubmit(e) {
		e.preventDefault();

		if (this.state.id !== null) {
			this.importModelCall = APICalls.ModelCalls.setName(this.props.project, this.state.id, this.state.name);
		} else {
			this.importModelCall = APICalls.ModelsCalls.importModel(this.props.project, this.state.file, this.state.name, this.state.file2, undefined, this.state.useSBMLNames);
		}
		
		this.importModelCall.promise.then(response => {
			console.log(response);
			if (response.status === 400) {
				response.json().then(data => {
					this.setState({errors: data});
				});
			} else {
				this.setState({
					id: null,
					name: "",
					file: null,
					fileName: "Select file...",
					file2: null,
					modal: false,
					type: 'maboss'
				});
				this.props.hide();
				this.props.updateParent();
			}
		});
	};


	toggleSBMLNames() {
		this.setState({useSBMLNames: !this.state.useSBMLNames});
	}

	shouldComponentUpdate(nextProps, nextState) {

		if (nextState.type !== this.state.type) {
			this.setState({
				file: null,
				filename: "Select file...",
				file2: null,
				file2Name: "Select file",
			});
			return false;
		}

		if (nextProps.id !== this.props.id ){

			if (nextProps.id !== null) {

				this.setState({
					id: nextProps.id.id,
					name: nextProps.id.name,
				});
			} else {
				this.setState({
					id: null,
					name: "",
				});
			}
		}
		return true;
	}

	componentWillUnmount() {
		if (this.importModelCall !== null) this.importModelCall.cancel();
	}

	render() {
		return <React.Fragment>
			<Modal isOpen={this.props.status} toggle={() => {if (this.props.status) {this.props.hide();} else {this.props.show(this.state.id)}}}>
				<form onSubmit={(e) => this.handleSubmit(e)}>
					<Card>
						<CardHeader>{this.state.id !== null ? "Edit" : "Load"} model</CardHeader>
						<CardBody>
							<ErrorAlert errorMessages={this.state.errors}/>
							<div className="form-group">
								<label htmlFor="modelName">Name</label>
								<input
									id="modelName"
									className="form-control"
									type="text"
									name="name"
									onChange={(e) => this.handleNameChange(e)}
									value={this.state.name}
									required
								/>
							</div>
							{ this.state.id === null ? 
								<React.Fragment>
									<div className="form-group">
										<label htmlFor="modelFile">Type</label>
										<MyDropdown
											dict={this.dictFormats}
											width={"28rem"}
											label={this.dictFormats[this.state.type]}
											callback={item=>this.handleTypeChange(item)}
										/>
									</div> 
									<div className="form-group">
										<label htmlFor="modelFile">{this.dictLabels[this.state.type][0]}</label>
										<div className="custom-file" id="customFile">
											<input
												id="modelFile"
												type="file"
												className="custom-file-input"
												name="file"
												onChange={(e) => this.handleFileChange(e)}
												accept={this.dictExtensions[this.state.type][0]}
												aria-describedby="fileHelp" required/>
											<label className="custom-file-label"
												htmlFor="modelFile">{this.state.fileName}</label>
										</div>
									</div>
									{( this.dictNbFiles[this.state.type] === 2 ?
									<div className="form-group">
										<label htmlFor="model2File">{this.dictLabels[this.state.type][1]}</label>
										<div className="custom-file" id="customFile2">
											<input
												id="model2File"
												type="file"
												className="custom-file-input"
												name="file2"
												onChange={(e) => this.handleFile2Change(e)}
												accept={this.dictExtensions[this.state.type][1]}
												aria-describedby="fileHelp" required/>
											<label className="custom-file-label"
												htmlFor="model2File">{this.state.file2Name}</label>
										</div>
									</div> : null )}
									{( this.state.type === "sbml" ?
									<div className="form-group general mr-auto">
									<Switch checked={this.state.useSBMLNames} toggle={this.toggleSBMLNames} id={"use_sbml_names"}/>
									{'\u00A0\u00A0'}
									<label className="name">Use SBML names</label>
										
									</div> : null )}
								</React.Fragment> : null }
								
						</CardBody>
						<CardFooter>
							<ButtonToolbar className="d-flex">
								<Button color="danger" className="mr-auto" onClick={() => this.props.hide()}>Close</Button>
								<Button type="submit" color="primary" className="ml-auto">{this.state.id !== null ? "Save" : "Load"} model</Button>
							</ButtonToolbar>
						</CardFooter>
					</Card>
				</form>
			</Modal>
		</React.Fragment>;
	}
}

export default ModelForm;