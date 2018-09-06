import React from "react";
import {Button} from "reactstrap";

import FullPage from "../FullPage";
import Projects from "./Projects";
import TableProjects from "./TableProjects";
import ProjectForm from "./ProjectForm";

import {isConnected} from "../commons/sessionVariables";


class ProjectsPage extends React.Component {

	constructor(props) {
		super(props);

		this.showProjectForm = this.showProjectForm.bind(this);
		this.hideProjectForm = this.hideProjectForm.bind(this);
		this.state = {
			showProjectForm: false,
			idProjectForm: null,
		}
	}

	showProjectForm(idProjectForm=null) {
		this.setState({
			showProjectForm: true,
			idProjectForm: idProjectForm
		})
	}

	hideProjectForm() {
		this.setState({
			showProjectForm: false
		})
	}

	componentWillMount() {
		if (!isConnected()) {
			this.props.history.push("/login/");
		}
	}

	render () {

		if (isConnected()) {
			return (
				<FullPage>
					<h2>Projects</h2><br/>

					<Projects endpoint="/api/projects/"
					render={
						(data, updateProjects) => {
							return <React.Fragment>
								<TableProjects
									data={data}
									updateProjects={updateProjects}
									edit={this.showProjectForm}
								/>
								<Button type="button" color="primary" onClick={() => {this.showProjectForm(null);}}>
									New project
								</Button>
								<ProjectForm
									id={this.state.idProjectForm}
									status={this.state.showProjectForm}
									show={this.showProjectForm}
									hide={this.hideProjectForm}
									updateProjects={updateProjects}
								/>
							</React.Fragment>
						}
					}
					/>

				</FullPage>
			);
		}
		else return null;

	}
}

export default ProjectsPage;
