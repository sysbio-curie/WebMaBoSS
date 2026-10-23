import React from "react";
import FullPage from "./FullPage";
import { Col, Row } from "reactstrap";
import EuropeanFlag from "./commons/EuropeanFlag";
import Investissements_davenir from "./commons/InvestissementAvenir";
import APICalls from "./api/apiCalls";
import sysbio_logo from "../images/sysbio_logo.png";
import curie_logo from "../images/curie_logo.svg";

class About extends React.Component {

	constructor(props) {
		super(props);
		this.state = {versions: null};
		this.getVersionsCall = null;
	}

	componentDidMount() {
		this.getVersionsCall = APICalls.GenericCalls.getVersions();
		this.getVersionsCall.promise.then(versions => this.setState({versions: versions}), () => {});
	}

	componentWillUnmount() {
		if (this.getVersionsCall !== null) { this.getVersionsCall.cancel(); }
	}

	render(){
		return 	<FullPage path={this.props.match.path}>
			<h2>About</h2><br/>
			WebMaBoSS was created and is maintained by the team <b><a href="https://sysbio.curie.fr">Computational System Biology of Cancer</a></b> at <b><a href="https://institut-curie.org/">Institut Curie</a></b>.<br/>
			It is open-source and available on <b><a href="https://github.com/sysbio-curie/WebMaBoSS">GitHub</a></b>, where you can also find instructions to run it locally and tutorials.
			<br/><br/>
			<div className="d-flex align-items-center">
				<a href="https://sysbio.curie.fr" title="Computational System Biology of Cancer" className="mr-5">
					<img src={sysbio_logo} alt="Computational System Biology of Cancer" style={{height: "100px"}}/>
				</a>
				<a href="https://institut-curie.org/" title="Institut Curie">
					<img src={curie_logo} alt="Institut Curie" style={{height: "100px"}}/>
				</a>
			</div>
			<br/><br/>
			{ this.state.versions !== null ? <React.Fragment>
				<h3>Version</h3><br/>
				<ul>
					{Object.entries(this.state.versions).filter(([, version]) => version !== null).map(([tool, version]) =>
						<li key={tool}><b>{tool}</b> {version}</li>
					)}
				</ul>
				<br/><br/>
			</React.Fragment> : null }
			<h3>Publications</h3><br/>
			<ul>
				<li>Noel V, Ruscone M, Stoll G, Viara E, Zinovyev A, Barillot E, Calzone L. WebMaBoSS: A web interface for simulating Boolean models stochastically. <i>Frontiers in molecular biosciences 2021; 8: 754444</i>. doi: <a href="https://doi.org/10.3389/fmolb.2021.754444">10.3389/fmolb.2021.754444</a></li>
				<br/>
				<li>Stoll G, Viara E, Barillot E, Calzone L. Continuous time Boolean modeling for biological signaling: application of Gillespie algorithm. <i>BMC Syst Biol. 2012 Aug 29;6:116</i>. doi: <a href="https://doi.org/10.1186/1752-0509-6-116">10.1186/1752-0509-6-116</a>.</li>
				<br/>
				<li>Stoll G, Caron B, Viara E, Dugourd A, Zinovyev A, Naldi A, Kroemer G, Barillot E, Calzone L.  MaBoSS 2.0: an environment for stochastic Boolean modeling. <i>Bioinformatics btx123. 2017 Mar</i>. doi: <a href="https://doi.org/10.1093/bioinformatics/btx123">10.1093/bioinformatics/btx123</a>.</li>
			</ul>
			<br/><br/>
			<h3>Funding</h3><br/>
			<Row>
				<Col className={"col-2"}>
					<EuropeanFlag width={"100px"}/>
				</Col>
				<Col className={"col-10"}>
					The development was supported by European Union's Horizon 2020 Programme under agreement no. 668858 (PrECISE project) and agreement no. 951773 (PerMedCoE project).
				</Col>
			</Row>
			<br/><br/>
			<Row>
				<Col className={"col-2"}>
					<Investissements_davenir width={"60px"}/>
				</Col>
				<Col className={"col-10"}>
					It was also partially funded by Agence Nationale de la Recherche in the program Investissements d’Avenir (project No. ANR-19-P3IA-0001; PRAIRIE 3IA Institute).
				</Col>
			</Row>
	  		
		
		</FullPage>;
	}
}

export default About;