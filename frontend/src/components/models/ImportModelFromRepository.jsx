import React from "react";
import {Input} from "reactstrap";
import {FontAwesomeIcon} from "@fortawesome/react-fontawesome";
import {faExternalLinkAlt} from "@fortawesome/free-solid-svg-icons";

import APICalls from "../api/apiCalls";
import Settings from "../Settings";
import LoadingIcon from "../commons/loaders/LoadingIcon";

const cell = {height: '2.5rem', overflow: 'hidden', textOverflow: 'ellipsis', display: 'inline-block', whiteSpace: 'nowrap'};


class ImportModelFromRepository extends React.Component {

	constructor(props) {
		super(props);

		this.state = {
			models: null,
			error: null,
			filter: "",
			importing: null,
		};

		this.getModelsCall = null;
		this.importCall = null;
		this.statusCall = null;
		this.statusChecker = null;
	}

	getModels() {
		this.getModelsCall = APICalls.RepositoriesCalls.getModels(this.props.repository);
		this.getModelsCall.promise.then(
			response => {
				if (response.ok) {
					this.setState({models: response.data});
				} else {
					this.setState({models: [], error: response.data.error || "Could not get the models"});
				}
			},
			error => { if (!error.isCanceled) { this.setState({models: [], error: "Could not get the models"}); } }
		);
	}

	failed(message) {
		this.setState({importing: null});
		this.props.showErrors([message]);
		this.props.hide();
	}

	importModel(model) {
		this.setState({importing: model});
		this.props.showErrors([]);

		this.importCall = APICalls.RepositoriesCalls.importModel(
			this.props.repository, this.props.project, model.id, model.name, this.props.useSBMLNames
		);
		this.importCall.promise.then(
			response => {
				if (!response.ok) {
					const data = response.data;
					this.failed(Array.isArray(data) ? data.join(" ") : (data.error || data.detail || "Could not import the model"));
					return;
				}
				// Downloading and converting the model can take a while : its status is checked until it's done
				this.statusChecker = setInterval(() => this.checkImport(response.data.import_id), Settings.updateRate);
			},
			error => { if (!error.isCanceled) { this.failed("Could not import the model"); } }
		);
	}

	checkImport(import_id) {
		if (this.statusCall !== null) { this.statusCall.cancel(); }
		this.statusCall = APICalls.RepositoriesCalls.getImportStatus(this.props.project, import_id);
		this.statusCall.promise.then(data => {
			if (data.done) {
				clearInterval(this.statusChecker);
				this.setState({importing: null});
				this.props.hide();
				this.props.updateParent();
			} else if (data.failed) {
				clearInterval(this.statusChecker);
				this.failed(data.error);
			}
		}, () => {});
	}

	componentDidMount() {
		this.getModels();
	}

	componentWillUnmount() {
		clearInterval(this.statusChecker);
		for (const call of [this.getModelsCall, this.importCall, this.statusCall]) {
			if (call !== null) { call.cancel(); }
		}
	}

	render() {
		if (this.state.importing !== null) {
			return <div className="text-center mt-4">
				<LoadingIcon width="2rem"/>
				<p className="mt-2">Importing {this.state.importing.name}</p>
				{ this.props.slow ? <p className="text-muted">{this.props.slow}</p> : null }
			</div>;
		}

		if (this.state.models === null) {
			return <LoadingIcon width="1rem"/>;
		}

		if (this.state.error !== null) {
			return <div className="text-danger">{this.state.error}</div>;
		}

		const words = this.state.filter.toLowerCase().split(/\s+/).filter(word => word.length > 0);
		const models = this.state.models.filter(model => {
			const text = (model.name + " " + model.author + " " + model.id).toLowerCase();
			return words.every(word => text.includes(word));
		});

		return <React.Fragment>
			<Input
				type="search" placeholder={"Search the " + this.state.models.length + " models"} className="mb-2"
				value={this.state.filter} onChange={e => this.setState({filter: e.target.value})}
			/>
			<table className="table table-striped">
				<thead>
					<tr>
						<th style={{...cell, width: '470px'}}>Name</th>
						<th style={{...cell, width: '230px'}}>Author</th>
						<th style={{...cell, width: '30px'}}/>
					</tr>
				</thead>
				<tbody>{models.map(model =>
					<tr key={model.id} onClick={() => this.importModel(model)} style={{cursor: 'pointer'}} title={"Import " + model.name}>
						<td style={{...cell, width: '470px'}}>{model.name}</td>
						<td style={{...cell, width: '230px'}}>{model.author}</td>
						<td style={{...cell, width: '30px'}}>{ model.url ?
							<a href={model.url} target="_blank" rel="noopener noreferrer" title="Page of the model"
							   onClick={e => e.stopPropagation()}>
								<FontAwesomeIcon icon={faExternalLinkAlt}/>
							</a> : null
						}</td>
					</tr>
				)}</tbody>
			</table>
		</React.Fragment>;
	}
}

export default ImportModelFromRepository;
