import React from "react";
import { Card, CardBody, CardHeader, CardText, Col, Row } from "reactstrap";
import FullPage from "./FullPage";
import image_cohen from '../images/tutorials/cohen/image17.png';
import image_corral from '../images/tutorials/corral/image22.png';
class Tutorials extends React.Component {

	render(){
		return 	<FullPage path={this.props.match.path}>
			<h2>Tutorials</h2><br/><br/><br/>
			<div className={"container-fluid"}>
				<Row>
					<Col className={"col-sm-4"}>
						<a href="/tutorials/cohen/"><Card>
							<CardHeader>Cohen model</CardHeader>
							<CardBody>
								<div className="container-fluid"><img src={image_cohen} width="250"/></div>
								<CardText>Studying tumor cell invasion and migration with a model from Cohen et al.</CardText>
							</CardBody>
						</Card></a>
						
					</Col>
					<Col className={"col-sm-4"}>
						<a href="/tutorials/corral/"><Card>
							<CardHeader>Corral model</CardHeader>
							<CardBody>
								<div className="container-fluid"><img src={image_corral} width="250"/></div>
								<CardText>Studying TH cells differentiation with a model from Corral et al.</CardText>
							</CardBody>
						</Card></a>
					</Col>
				</Row>
			</div>
		</FullPage>;
	}
}

export default Tutorials;