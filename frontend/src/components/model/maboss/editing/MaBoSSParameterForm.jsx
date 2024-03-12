import React from "react";
import {Button, ButtonToolbar, Modal, Card, CardHeader, CardBody, CardFooter} from "reactstrap";
import PropTypes from "prop-types";
import ErrorAlert from "../../../commons/ErrorAlert";
import APICalls from "../../../api/apiCalls";
import LoadingInlineIcon from "../../../commons/loaders/LoadingInlineIcon";
import BufferedTextField from "../../../commons/buttons/BufferedTextField";

class MaBoSSParameterForm extends React.Component {

	static propTypes = {
		status: PropTypes.bool.isRequired,
		toggle: PropTypes.func.isRequired,
	};

	constructor(props) {
		super(props);

		this.state = {
			name: "",
			value: "",

			nameError: "Please provide a name",
			valueError: "Please provide a value",

			showErrors: false,
			waitSubmit: false,
		};

		this.checkParameterCall = null;

		this.inputNameRef = React.createRef();
		this.inputValueRef = React.createRef();
		
		this.onNameChange = this.onNameChange.bind(this);
		this.onValueChange = this.onValueChange.bind(this);
		this.onSubmit = this.onSubmit.bind(this);
	}

	onNameChange(name) {
		this.setState({name: name});
		this.checkParameterName(name);
	}

	onValueChange(value) {
		this.setState({value: value});
		this.checkParameterValue(value);
	}

	onSubmit(e) {
		e.preventDefault();
		if (this.state.nameError !== "" || this.state.valueError !== "") {
			this.setState({showErrors: true});

			if (this.state.nameError !== "") {
				this.inputNameRef.current.focus();
			}
			if (this.state.valueError !== "") {
				this.inputValueRef.current.focus();
			}

		} else {
			this.setState({showErrors: false});
			this.props.submit(
				this.props.name !== null ? this.props.name : this.state.name,
				this.state.value
			);
		}

	}

	checkParameterValue(value) {
		if (this.checkParameterCall !== null) { this.checkParameterCall.cancel();}

		if (value === "") {
			this.setState({valueError: "Please provide a value"});
		} else if (isNaN(value)) {
			this.setState({valueError: "Not a number"});
		} else {

			this.setState({waitSubmit: true});
			this.checkParameterCall = APICalls.MaBoSSCalls.checkMaBoSSParameter(
				this.props.project, this.props.modelId,
				"$whatever_the_name_as_long_as_its_unique",
				value
			);

			this.checkParameterCall.promise.then((data) => {
				if (data.error !== "") {
					this.setState({valueError: data.error, waitSubmit: false})
				} else {
					this.setState({valueError: "", waitSubmit: false});
				}
			});


		}
	}

	checkParameterName(name) {
		if (this.checkParameterCall !== null) { this.checkParameterCall.cancel();}

		if (value === "") {
			this.setState({nameError: "Please provide a name"});
		} else if (Object.keys(this.props.parameters).includes(name)) {
			this.setState({nameError: "Parameter " + name + " already exists"});
		} else if (!name.startsWith("$")) {
			this.setState({nameError: "Parameter name must start with a '$'"});
		} else  {
			this.setState({waitSubmit: true});
			this.checkParameterCall = APICalls.MaBoSSCalls.checkMaBoSSParameter(
				this.props.project, this.props.modelId,
				name, 1
			);

			this.checkParameterCall.promise.then((data) => {
				if (data.error !== "") {
					this.setState({nameError: data.error, waitSubmit: false})
				} else {
					this.setState({nameError: "", waitSubmit: false});
				}
			});

		}

	}

	componentDidMount() {
		if (this.props.name === null){
			this.checkParameterName(this.state.name);
		}
		this.checkParameterValue(this.state.value);
	}

	componentWillUnmount() {
		if (this.checkParameterCall !== null) {
			this.checkParameterCall.cancel();
		}
	}

	shouldComponentUpdate(nextProps, nextState) {

		if (nextProps.status !== this.props.status) {
			this.setState({name: "", nameError: "", valueError: "", showErrors: false});
		}

		if (nextProps.value !== this.props.value && nextProps.value !== this.state.value) {
			this.setState({value: nextProps.value})
		}

		return true;
	}

	render() {

		const errors = [];
		if (this.state.nameError !== "") {
			errors.push(this.state.nameError);
		}

		if (this.state.valueError !== "") {
			errors.push(this.state.valueError);
		}

		return (
			<Modal isOpen={this.props.status} toggle={() => this.props.toggle()}>
				<form>
				<Card>
					<CardHeader>{this.props.name !== null ? "Editing" : "Creating"} parameter value</CardHeader>
					<CardBody>
						{ this.state.showErrors ? <ErrorAlert errorMessages={errors}/> : null}
						<div className="form-group">
							<label htmlFor="name">Name</label>
							<BufferedTextField
								id="name" name="name" inputRef={this.inputNameRef}
								value={this.props.name !== null ? this.props.name : this.state.name}
								error={this.state.nameError} disabled={this.props.name !== null}
								onValueChange={this.onNameChange}

							/>
						</div>
						<div className="form-group">
							<label htmlFor="value">Value</label>
							<BufferedTextField
								id="value" name="value" inputRef={this.inputValueRef}
								value={this.state.value}
								error={this.state.valueError}
								onValueChange={this.onValueChange}

							/>
						</div>

					</CardBody>
					<CardFooter>
						<ButtonToolbar className="d-flex">
							<Button color="danger" className="mr-auto" onClick={() => this.props.toggle()}>Close</Button>
							<Button
								type="submit" color="default" className="ml-auto"
								onClick={this.onSubmit} disabled={this.state.waitSubmit}
							>Submit {this.state.waitSubmit ? <LoadingInlineIcon width="1rem"/> : null}</Button>
						</ButtonToolbar>
					</CardFooter>
				</Card>
				</form>
			</Modal>
		);
	}
}

export default MaBoSSParameterForm;