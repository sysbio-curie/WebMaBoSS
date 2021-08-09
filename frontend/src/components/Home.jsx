import React from "react";
import {Table, Row, Col, Card, CardBody, CardTitle, CardText, CardHeader} from "reactstrap";
import MaBoSSIcon from "./commons/MaBoSSIcon";

class Home extends React.Component {

	render(){
		return <React.Fragment>
		<br/><br/>
		<div className={"container-fluid"}>
			<Row>
				<Col className={"col-4"}>
					<MaBoSSIcon width={"250px"}/>
				</Col>
				<Col className={"col-8"}>
					<h1>WebMaBoSS</h1>
           			<h3>A web tool for simulating Boolean models</h3>
					<br/>
					<h5>Click <a href="/login/">here</a> to login if you already have an account, overwise you can quickly create one <a href="/register/">here</a>.</h5>
				</Col>
			</Row>
			<br/><br/>
			<Row>
				<Col className={"col-sm-4"}>
					<Card>
						<CardHeader>Model analysis</CardHeader>
						<CardBody>
							<CardText>WebMaBoSS allows simulations, and multiple outputs for results. It also allows sensitivity analysis by performing single and double mutations.</CardText>
						</CardBody>
					</Card>
					
				</Col>
				<Col className={"col-sm-4"}>
					<Card>
						<CardHeader>Compatibility</CardHeader>
						<CardBody>
							<CardText>WebMaBoSS is able to import models in MaBoSS format (bnd, cfg files), BoolNet format, SBML-qual format, or in GINsim format. It also allows to export models in any of these three formats.</CardText>
						</CardBody>
					</Card>
					
				</Col>
				<Col className={"col-sm-4"}>
					<Card>
						<CardHeader>Public databases</CardHeader>
						<CardBody>
							<CardText>WebMaBoSS allows to browse models from CellCollective and BioModels, and import them.</CardText>
						</CardBody>
					</Card>
					
				</Col>
			</Row>
		</div>

	  <div class="footer" style={{
		  position: "absolute", bottom: "0", left: "0", width: "100%", 		
		  height: "80px", lineHeight: "40px", backgroundColor: "#f5f5f5",
		  paddingLeft: "100px", paddingRight: "100px"
      }}>
      <div class="container">
        <span class="text-muted">WebMaBoSS was created and is maintained by the team <b><a href="https://sysbio.curie.fr">Computational System Biology of Cancer</a></b> at <b><a href="https://institut-curie.org/">Institut Curie</a></b>.<br/>It is open-source and available on <b><a href="https://github.com/sysbio-curie/WebMaBoSS">GitHub</a></b>, where you can also find instructions to run it locally and tutorials.</span>
      </div>
    </div>
	</React.Fragment>;
	}
}

export default Home;