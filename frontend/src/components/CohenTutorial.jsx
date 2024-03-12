import React from "react";
import FullPage from "./FullPage";

import image10 from "../images/tutorials/cohen/image10.png";
import image1f from "../images/tutorials/cohen/image1f.png";
import image20 from "../images/tutorials/cohen/image20.png";
import image21 from "../images/tutorials/cohen/image21.png";
import image22 from "../images/tutorials/cohen/image22.png";
import image23 from "../images/tutorials/cohen/image23.png";
import image24 from "../images/tutorials/cohen/image24.png";
import image17 from "../images/tutorials/cohen/image17.png";
import image25 from "../images/tutorials/cohen/image25.png";
import image19 from "../images/tutorials/cohen/image19.png";
import image1a from "../images/tutorials/cohen/image1a.png";
import image26 from "../images/tutorials/cohen/image26.png";
import image27 from "../images/tutorials/cohen/image27.png";
import image28 from "../images/tutorials/cohen/image28.png";
import image1e from "../images/tutorials/cohen/image1e.png";

class CohenTutorial extends React.Component {

	render(){
		return 	<FullPage path={this.props.match.path}>
			<h2>Cohen's Tutorial</h2><br/><br/><br/>
			Here we propose a tutorial to give the user a total overview about the WebMaBoSS functionality. <br/>
			It is possible to get access through browser at <a href="https://maboss.curie.fr/webmaboss/">https://maboss.curie.fr/webmaboss</a>
			<br/><br/>
			<h3>Starting a Project</h3>

			WebMaBoSS allows the user to organize the models inside Projects folder. <br/><br/>
			<div className="container" align="center"><img src={image10} width="80%"/></div><br/>
			In the Projects folder the users can upload their own model in Z-GINML, SBMLqual or MaBoSS format or import a model from BioModels and Cell Collective. <br/>
			For this tutorial we will use a model of Tumour Cell Invasion and Migration from Cohen DP et al. imported from Cell Collective. <br/><br/>
			<div className="container" align="center"><img src={image1f} width="80%"/></div><br/>

			<br/><br/>
			<h3>Overview Tab</h3>
			Once imported the model, it can be visualized in the Overview tab. <br/><br/>
			<div className="container" align="center"><img src={image20} width="60%"/></div><br/>
			This particular model is composed by 32 nodes, describing the intercourse of different trascription factors involved in the invasion process; to acquire the ability to migrate Epithelial to Mesenchymal Transition (EMT) is needed to gain motility. that is induced  loss of E-cadherin (CDH1) and by gene expression of N-cadherin (CDH2), this last one is up-regulated by activation of ZEB1/2 SNAI1/2 and TWIST1. In order to activate the Metastasis phenotype, EMT is needed as well as the activation of Migration and Invasion. <br/><br/>
			
			<br/><br/>
			<h3>Editing tab </h3>
			Models exported in MaBoSS are characterized by two file, model.bnd and model.cfg. <br/>
			The .bnd file contains the logic equation for each node of the network, while the .cfg file contains the parameters for the MaBoSS simulation. <br/>
			On WebMaBoSS the .cfg file is summarized in the editing tab. The user can visualize the logical equation for each node and editing the formula using the buttons on the right of the corresponding nodes or insert a new node in the network. <br/><br/>
			<div className="container" align="center"><img src={image21} width="80%"/></div><br/>

			MaBoSS computes the trajectories over time and the probable states of the model associating an initial states for each node, that by default is set to 0. The user can change the initial state of each node of the network in order to simulate different initial conditions. This can be done as shown in the figure below: <br/>
			<div className="container" align="center"><img src={image22} width="80%"/></div><br/>

			In order to reduce the computational time of the simulation, the user should reduce the number of output nodes that will be displayed in next results (less then 10 output nodes to avoid longer computational time). <br/><br/>
			<div className="container" align="center"><img src={image23} width="60%"/></div><br/>

			<br/><br/>
 			<h3>Simulation tab </h3>
			Once edited the parameters, the user can launch a simulation through the Simulation tab. The previously modified parameters will be kept and will be shown a recap of the simulation before to submit. <br/><br/>
			<div className="container" align="center"><img src={image24} width="60%"/></div><br/>

 			Below we are showing the results of a simulation of wild type model with random intial conditions. 
			<div className="container" align="center"><img src={image17} width="60%"/></div><br/>


 			WebMaBoSS will automatically generate a plot for the final state distribution: 

 			Nodes probability trajectories plot: 
			<div className="container" align="center"><img src={image25} width="60%"/></div><br/>

 			Table of the fixed points: 
			<div className="container" align="center"><img src={image19} width="60%"/></div><br/>

			It is possible to visualize directly on the network the stable nodes, using the blue icon on the left. 
			<div className="container" align="center"><img src={image1a} width="40%"/></div><br/>
			

			In the Mutations tab, the user can force the up/down regulation of certain nodes. <br/>
			<div className="container" align="center"><img src={image26} width="40%"/></div><br/>


			This is useful to understand what the influence of a gene or transcription factor is and the impact of a node on the possible network states. <br/>
			<div className="container" align="center"><img src={image27} width="10%"/></div><br/>

			As example, we simulated a loss of function of E-cadherin (CDH1) while forcing the activation of N-cadherin (CDH2). This leads to the activation of EMT, confirming that down-regulation of CDH1 and up-regulation of CDH2 is necessary in order to induce Epithelial to Mesenchymal Transition. <br/><br/>

			
			WebMaBoSS provides also a Sensitivity Analysis, that introduces one mutation at a time for each node providing for each step a final state distribution. The analysis can be done with single or double mutation. <br/><br/>
			<div className="container" align="center"><img src={image28} width="40%"/></div><br/>
			<div className="container" align="center"><img src={image1e} width="100%"/></div><br/>

 

 
 
		</FullPage>;
	}
}

export default CohenTutorial;