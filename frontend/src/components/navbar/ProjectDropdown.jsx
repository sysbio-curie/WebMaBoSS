import React from "react";
import {setProject, getProject} from "../commons/sessionVariables";
import APICalls from "../api/apiCalls";
import LoadingIcon from "../commons/loaders/LoadingIcon";
import MyDropdown from "../commons/buttons/MyDropdown";

class ProjectDropdown extends React.Component {

	constructor(props) {
		super(props);
		this.state = {
			loaded: false,
			projects: [],
			projectName: ""
		};

		this.onProjectChanged = this.onProjectChanged.bind(this);

		this.getProjectCall = null;
	}

	getProjects() {
		this.getProjectCall = APICalls.ProjectCalls.getProjects();
		this.getProjectCall.promise.then((projects) => {
			this.setState({ projects: projects, loaded: true });
			if (getProject() !== null && getProject() !== undefined) {
				let found = false;
				for (const project in projects) {
					if (projects[project].id === getProject()) {
						this.setState({projectName: projects[project].name});
						found = true;
						break;
					}
				}
				if (!found && projects.length > 0){
					setProject(projects[0].id);
					this.setState({projectName: projects[0].name});
					this.props.updateProject(projects[0].id);
				}
			} else {
				if (projects.length > 0){
					setProject(projects[0].id);
					this.setState({projectName: projects[0].name});
					this.props.updateProject(projects[0].id);
				}
			}
		});

	}

	componentDidMount(){
		this.getProjects();
	}

	componentWillUnmount(){
		this.getProjectCall.cancel();
	}

	onProjectChanged(project_ind) {
		setProject(this.state.projects[project_ind].id);
		this.setState({projectName: this.state.projects[project_ind].name});
		this.props.updateProject(this.state.projects[project_ind].id);
	}

	render() {

		if (!this.state.loaded) {
			return <LoadingIcon width="1rem" dark/>;

		} else {
			if (this.state.projects.length > 0) {
				return <MyDropdown
						dict={this.state.projects.reduce((result, project, key) => {
							result[key] = project.name;
							return result;
						},{})}
						label={this.state.projectName}
						width={"15rem"}
						callback={item => this.onProjectChanged(item)}
					/>;
				
			} else {
				return null;
			}
		}
	}
}

export default ProjectDropdown;
