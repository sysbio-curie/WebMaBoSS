import React from "react";
import {Button, Card, CardHeader, CardBody, Input, Table} from "reactstrap";
import {FontAwesomeIcon} from "@fortawesome/react-fontawesome";
import {faChevronDown, faChevronUp, faSyncAlt} from "@fortawesome/free-solid-svg-icons";

import APICalls from "../../api/apiCalls";
import LoadingIcon from "../../commons/loaders/LoadingIcon";
import {formatSize, formatDate} from "./format";

// Columns : key, title, value used for sorting, how it's displayed
const COLUMNS = [
	["username", "User", user => user.username.toLowerCase(), user => <React.Fragment>
		{user.username}{user.is_staff ? <span className="badge badge-secondary ml-1">admin</span> : null}
		<br/><small className="text-muted">{user.email}</small>
	</React.Fragment>],
	["date_joined", "Registered", user => user.date_joined, user => formatDate(user.date_joined)],
	["last_activity", "Last visit", user => user.last_activity || "", user => formatDate(user.last_activity)],
	["projects", "Projects", user => user.projects, user => user.projects],
	["models", "Models", user => user.models, user => user.models],
	["simulations", "Simulations", user => user.simulations, user => user.simulations],
	["analyses", "Sensitivity analyses", user => user.analyses, user => user.analyses],
	["database", "Database", user => user.database, user => formatSize(user.database)],
	["data", "Data", user => user.data, user => formatSize(user.data)],
	["total", "Total", user => user.database + user.data, user => formatSize(user.database + user.data)],
];


class UsersTable extends React.Component {

	constructor(props) {
		super(props);

		this.state = {
			users: null,
			computedAt: null,
			computing: false,
			error: null,
			sortBy: "total",
			ascending: false,
			filter: "",
		};

		this.getUsersCall = null;
		this.checker = null;
	}

	// The statistics are computed in the background (by the maintenance job, or when asked) : checked until they're done
	received(statistics) {
		this.setState({users: statistics.users, computedAt: statistics.computed_at, computing: statistics.computing, error: null});
		clearTimeout(this.checker);
		if (statistics.computing) {
			this.checker = setTimeout(() => this.getUsers(), 3000);
		}
	}

	getUsers(compute = false) {
		if (this.getUsersCall !== null) { this.getUsersCall.cancel(); }

		this.getUsersCall = compute ? APICalls.MonitoringCalls.computeUsers() : APICalls.MonitoringCalls.getUsers();
		this.getUsersCall.promise.then(
			statistics => this.received(statistics),
			error => { if (!error.isCanceled) { this.setState({error: "Could not load the users"}); } }
		);
	}

	sort(key) {
		if (key === this.state.sortBy) {
			this.setState({ascending: !this.state.ascending});
		} else {
			// Names in alphabetical order, the rest from the biggest or most recent
			this.setState({sortBy: key, ascending: key === "username"});
		}
	}

	componentDidMount() {
		this.getUsers();
	}

	componentDidUpdate(prevProps) {
		// After a cleanup
		if (prevProps.version !== this.props.version) {
			this.getUsers(true);
		}
	}

	componentWillUnmount() {
		clearTimeout(this.checker);
		if (this.getUsersCall !== null) { this.getUsersCall.cancel(); }
	}

	renderTable() {
		const column = COLUMNS.find(column => column[0] === this.state.sortBy);
		const filter = this.state.filter.toLowerCase();
		const users = this.state.users.filter(
			user => user.username.toLowerCase().includes(filter) || user.email.toLowerCase().includes(filter)
		).sort((a, b) => {
			const order = column[2](a) < column[2](b) ? -1 : (column[2](a) > column[2](b) ? 1 : 0);
			return this.state.ascending ? order : -order;
		});

		return <React.Fragment>
			<Input className="mb-3" type="search" placeholder="Filter by name or email" value={this.state.filter}
				   onChange={(e) => this.setState({filter: e.target.value})}/>
			<small className="text-muted">{users.length} of {this.state.users.length} users</small>
			<div style={{overflow: "auto", maxHeight: "40rem"}}>
				<Table size="sm" hover>
					<thead>
						<tr>
							{COLUMNS.map(([key, title]) =>
								<th key={key} onClick={() => this.sort(key)} style={{
									cursor: "pointer", whiteSpace: "nowrap", position: "sticky", top: 0, background: "white"
								}}>
									{title}
									{key === this.state.sortBy ?
										<FontAwesomeIcon className="ml-1" icon={this.state.ascending ? faChevronUp : faChevronDown}/> : null}
								</th>
							)}
						</tr>
					</thead>
					<tbody>
						{users.map(user =>
							<tr key={user.id}>
								{COLUMNS.map(([key, , , display]) =>
									<td key={key} style={key === "username" ? {} : {whiteSpace: "nowrap"}}>{display(user)}</td>
								)}
							</tr>
						)}
					</tbody>
				</Table>
			</div>
		</React.Fragment>;
	}

	render() {
		let content;
		if (this.state.error !== null) {
			content = <div className="alert alert-danger">{this.state.error}</div>;
		} else if (this.state.users === null) {
			content = <React.Fragment>
				<LoadingIcon width="3rem"/>
				{this.state.computing ? <small className="text-muted">Computing the statistics, which takes a while on a large database</small> : null}
			</React.Fragment>;
		} else {
			content = this.renderTable();
		}

		return <Card className="mb-4">
			<CardHeader className="d-flex align-items-center">
				<span className="mr-auto">Users</span>
				<small className="text-muted mr-2">
					{this.state.computing ? "Computing..." : (this.state.computedAt ? "Computed " + formatDate(this.state.computedAt, true) : null)}
				</small>
				<Button size="sm" title="Compute again" disabled={this.state.computing} onClick={() => this.getUsers(true)}>
					<FontAwesomeIcon icon={faSyncAlt} spin={this.state.computing}/>
				</Button>
			</CardHeader>
			<CardBody>{content}</CardBody>
		</Card>;
	}
}

export default UsersTable;
