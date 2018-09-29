import React from "react";
import LoadingIcon from "../../commons/LoadingIcon";
import APICalls from "../../commons/apiCalls";


class MaBoSSServers extends React.Component {

	constructor(props) {
		super(props);

		this.state = {
			data: [],
			loaded: false,
		};

		this.updateServers = this.updateServers.bind(this);
		this.updateServersCall = null;
	}

	updateServers(){
		if (this.updateServersCall !== null) this.updateServersCall.cancel();

		this.updateServersCall = APICalls.getMaBoSSServers();
		this.updateServersCall.promise.then(data => this.setState({ data: data, loaded: true }));
	}

	componentDidMount() {
		this.updateServers();
	}

	componentWillUnmount() {
		if (this.updateServersCall !== null) this.updateServersCall.cancel();
	}

	render() {
		if (this.state.loaded) {
			return this.props.render(this.state.data, this.updateServers);

		} else {
			return <LoadingIcon width="3rem"/>
		}
	}
}
export default MaBoSSServers;