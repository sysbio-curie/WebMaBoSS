import React from "react";
import {Card, CardHeader, CardBody} from "reactstrap";
import history from '../history';

import FullPage from "../FullPage";
import ErrorAlert from "../commons/ErrorAlert";
import {setAPIKey} from "../commons/sessionVariables";
import APICalls from "../api/apiCalls";
import MaBoSSIcon from "../commons/MaBoSSIcon";


class Register extends React.Component {

	constructor(props) {
		super(props);

		this.state = {
			username: "",
			usernameHasError: false,
			email: "",
			emailHasError: false,
			password1: "",
			password1HasError: false,
			password2: "",
			errorMessages: []
		};

		this.handleSubmit.bind(this);
		this.handleUsernameChange.bind(this);
		this.handleEmailChange.bind(this);
		this.handlePassword1Change.bind(this);
		this.handlePassword2Change.bind(this);

		this.registerCall = null;
	}

	handleSubmit(e) {

		e.preventDefault();

		this.registerCall = APICalls.AuthCalls.register(
			this.state.username, this.state.email, this.state.password1, this.state.password2
		);
		this.registerCall.promise.then(json_response => {

			this.state = {
				usernameHasError: false,
				emailHasError: false,
				password1HasError: false,
				errorMessages: []
			};

			if ('key' in json_response) {
				setAPIKey(json_response['key']);
				history.push("/");

			} else if (
				'email' in json_response || 'username' in json_response	|| 'password1' in json_response
			) {

				let new_state = {};
				let errorMessages = [];

				if ('username' in json_response) {
					new_state.usernameHasError = true;
					errorMessages.push(json_response['username']);
				}

				if ('email' in json_response) {
					new_state.emailHasError = true;
					errorMessages.push(json_response['email']);
				}

				if ('password1' in json_response) {
					new_state.password1HasError = true;
					errorMessages.push(json_response['password1']);
				}

				new_state.errorMessages = errorMessages;
				this.setState(new_state);

			} else if ('non_field_error' in json_response) {

				let errorMessages = this.state.errorMessages;
				errorMessages.push(json_response['non_field_errors']);
				this.setState({errorMessages: errorMessages});
			}

		});

	}

	handleUsernameChange(e) {
		this.setState({username: e.target.value});
	}

	handleEmailChange(e) {
		this.setState({email: e.target.value});
	}

	handlePassword1Change(e) {
		this.setState({password1: e.target.value});
	}

	handlePassword2Change(e) {
		this.setState({password2: e.target.value});
	}

	componentWillUnmount(e) {
		if (this.registerCall !== null) this.registerCall.cancel();
	}

	render(){

		return <FullPage path={this.props.match.path} >
			<div className="d-flex justify-content-center">
				<form onSubmit={(e) => this.handleSubmit(e)}>
					<Card style={{width: '20em'}}>
						<CardHeader>Register to WebMaBoSS</CardHeader>
						<CardBody>
						<div className="d-flex justify-content-center">
							<MaBoSSIcon width={"200px"}/>
						</div>
						<br/>
						<ErrorAlert errorMessages={this.state.errorMessages}/>
						<div className="form-group">
							<label htmlFor="username">Username</label>
							<input
								id="username"
								className={"form-control" + (this.state.usernameHasError?" is-invalid":"")}
								type="text"
								name="username"
								onChange={(e) => this.handleUsernameChange(e)}
								value={this.state.username}
								required
							/>
						</div>
						<div className="form-group">
							<div className="form-group">
								<label htmlFor="email">E-mail (optional)</label>
								<input
									id="email"
									className={"form-control" + (this.state.emailHasError?" is-invalid":"")}
									type="text"
									name="email"
									onChange={(e) => this.handleEmailChange(e)}
									value={this.state.email}
								/>
							</div>
						</div>
						<div className="form-group">
							<label htmlFor="password1">Password</label>
							<input
								id="password1"
								className={"form-control" + (this.state.password1HasError?" is-invalid":"")}
								type="password"
								name="password1"
								onChange={(e) => this.handlePassword1Change(e)}
								value={this.state.password1}
								required
							/>
						</div>
						<div className="form-group">
							<label htmlFor="password2">Confirm password</label>
							<input
								id="password2"
								className={"form-control" + (this.state.password1HasError?" is-invalid":"")}
								type="password"
								name="password2"
								onChange={(e) => this.handlePassword2Change(e)}
								value={this.state.password2}
								required
							/>
						</div>
						<div>
							<button type="submit" className="btn btn-primary">
								Register
							</button>
						</div>
						</CardBody>
					</Card>
				</form>
			</div>
		</FullPage>;
	}
}

export default Register;