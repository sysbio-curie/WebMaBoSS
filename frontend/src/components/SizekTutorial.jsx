import React from "react";
import FullPage from "./FullPage";

import load_model from "../images/tutorials/sizek/load_model.png";
import new_simulation_observed from "../images/tutorials/sizek/new_simulation_observed.png";
import cyclins_trajectories from "../images/tutorials/sizek/cyclins_trajectories.png";
import cyclins_observed_graph from "../images/tutorials/sizek/cyclins_observed_graph.png";
import new_simulation_observed_casp3 from "../images/tutorials/sizek/new_simulation_observed_casp3.png";
import casp3_observed_graph from "../images/tutorials/sizek/casp3_observed_graph.png";
import new_simulation_mutation from "../images/tutorials/sizek/new_simulation_mutation.png";
import p110_trajectories from "../images/tutorials/sizek/p110_trajectories.png";
import p110_observed_graph from "../images/tutorials/sizek/p110_observed_graph.png";
import sizek_bnd from "../../../api/defaults/models/sizek/sizek.bnd";
import sizek_cfg from "../../../api/defaults/models/sizek/sizek.cfg";

const Figure = props => <div className="container" align="center"><img src={props.src} width={props.width || "80%"}/></div>;


class SizekTutorial extends React.Component {

	render(){
		return 	<FullPage path={this.props.match.path}>
			<h2>Sizek's Tutorial : observed graphs</h2><br/><br/>

			This tutorial reproduces the section 3.9 of the CoLoMoTo tutorial (Noël <i>et al.</i>, 2025), with the model of
			growth signaling, cell cycle and apoptosis of Sizek <i>et al.</i> (2019). It shows how to follow the order in
			which a few nodes are activated, with <b>observed graphs</b>.
			<br/><br/>
			An observed graph is a compressed state transition graph. A few nodes are selected : each state of the graph
			is a combination of these nodes which are active, <code>&lt;nil&gt;</code> when none is. Over all the simulated
			trajectories, MaBoSS counts the transitions between these states. The arrows give the probability that, from a
			state, the next change of the selected nodes leads to another one.
			<br/><br/><br/>

			<h3>1. Loading the model</h3>
			The model is one of the demo models : <b>Sizek2019 - Growth signaling, cell cycle and apoptosis</b>. It is in
			the <b>Demo</b>, where simulations can be run without an account, and in the projects created since then.
			<br/><br/>
			Otherwise, download the two files of the model :&nbsp;
			<a href={sizek_bnd} download>sizek.bnd</a> and&nbsp;
			<a href={sizek_cfg} download>sizek.cfg</a>.
			Then, in the Models page, click on <b>Load model</b>, choose the type <b>MaBoSS</b> and select the two files.
			<br/><br/>
			<Figure src={load_model} width="70%"/><br/>
			Besides the settings of the simulations, the cfg file sets the initial state of the Figure 5 of Sizek <i>et al.</i>,
			the outputs (the three cyclins and Casp3), and the nodes of the observed graph, here the three cyclins :
			<pre className="mt-2">{"CyclinA.in_graph = True;\nCyclinB.in_graph = True;\nCyclinE.in_graph = True;"}</pre>
			<br/>

			<h3>2. Order of the activation of the cyclins</h3>
			Select the model, and in the <b>Simulation</b> page, click on <b>New simulation</b>. The settings come from the
			cfg file (a maximum time of 200, 4000 trajectories). The tab <b>Observed graph</b> selects the nodes of the graph,
			up to 8 : the three cyclins are already selected. Click on <b>Submit</b>.
			<br/><br/>
			<Figure src={new_simulation_observed} width="60%"/><br/>
			The cyclins are expected to be activated in the order CyclinE, CyclinA, CyclinB, and inactivated in the same
			order. The tab <b>Nodes probability trajectories</b> shows this sequence as damped oscillations of their mean
			activity. Meanwhile, more and more cells activate Casp3 and die :
			<br/><br/>
			<Figure src={cyclins_trajectories}/><br/>
			The tab <b>Observed graph</b> shows the same sequence for the individual trajectories. The darker and wider an
			arrow, the more likely the transition. Starting from <code>&lt;nil&gt;</code> (no active cyclin, G0), the most likely
			transitions activate CyclinE (about 80%), then CyclinA (about 87%), inactivate CyclinE (about 64%), activate
			CyclinB (about 50%), inactivate CyclinA (about 83%) and finally CyclinB (about 98%), which closes the cycle. Other
			cycles are followed with lower probabilities.
			<br/><br/>
			<Figure src={cyclins_observed_graph}/><br/>
			The buttons above the graph hide the less likely transitions, show or hide the probabilities, change the layout
			(the boxes can also be moved), and download the graph as an image. The simulations are stochastic : the
			probabilities change slightly from one simulation to the other.
			<br/><br/><br/>

			<h3>3. When does apoptosis start along the cell cycle ?</h3>
			In a new simulation, select also <b>Casp3</b> in the tab <b>Observed graph</b> :
			<br/><br/>
			<Figure src={new_simulation_observed_casp3} width="60%"/><br/>
			With four nodes, the graph has more states. To keep it readable, hide the transitions under 2%. The cell cycle
			and the states with Casp3 active (apoptosis) are now apart, and only two transitions lead from the first to the
			second : from <code>&lt;nil&gt;</code>, which presumably represents G0, and from the state with only CyclinB active,
			which represents G2/M (about 2% and 3% of their transitions).
			<br/><br/>
			<Figure src={casp3_observed_graph}/><br/><br/>

			<h3>4. Ectopic p110_H activity blocks apoptosis</h3>
			In the model, p110_H activates PI3K and AKT, which inhibit cell death. In a new simulation, with the cyclins and
			Casp3 selected in the tab <b>Observed graph</b>, set <b>p110_H</b> ON in the tab <b>Mutations</b> :
			<br/><br/>
			<Figure src={new_simulation_mutation} width="60%"/><br/>
			Casp3 is never activated anymore, and the cyclins keep oscillating :
			<br/><br/>
			<Figure src={p110_trajectories}/><br/>
			The observed graph doesn't have any state with Casp3 : only the cycle remains.
			<br/><br/>
			<Figure src={p110_observed_graph}/><br/><br/>

			<h3>References</h3>
			<ul>
				<li>Noël V, Naldi A, Calzone L, Paulevé L, Thieffry D. Reproducible Boolean model analyses and simulations with
					the CoLoMoTo software suite: a tutorial. <i>Interface Focus 2025; 15: 20250002</i>.
					doi: <a href="https://doi.org/10.1098/rsfs.2025.0002">10.1098/rsfs.2025.0002</a></li>
				<li>Sizek H, Hamel A, Deritei D, Campbell S, Ravasz Regan ER. Boolean model of growth signaling, cell cycle and
					apoptosis predicts the molecular mechanism of aberrant cell cycle progression driven by hyperactive PI3K.
					<i> PLoS Computational Biology 2019; 15: e1006402</i>.
					doi: <a href="https://doi.org/10.1371/journal.pcbi.1006402">10.1371/journal.pcbi.1006402</a></li>
				<li>The same analysis with pyMaBoSS : <a href="https://github.com/vincent-noel/pyMaBoSS/blob/develop/doc/notebooks/Observed_graph_Sizek.ipynb">Observed_graph_Sizek.ipynb</a></li>
			</ul>
		</FullPage>;
	}
}

export default SizekTutorial;
