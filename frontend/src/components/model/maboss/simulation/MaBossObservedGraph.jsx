import React from "react";
import Cytoscape from 'cytoscape';
import CytoscapeComponent from 'react-cytoscapejs';
import dagre from 'cytoscape-dagre';
import FileSaver from "file-saver";
import {Button, Input, Label} from "reactstrap";
import {FontAwesomeIcon} from "@fortawesome/react-fontawesome";
import {faDownload, faSyncAlt} from "@fortawesome/free-solid-svg-icons";

import LoadingIcon from "../../../commons/loaders/LoadingIcon";
import Switch from "../../../commons/buttons/Switch";
import MyDropdown from "../../../commons/buttons/MyDropdown";

Cytoscape.use(dagre);

const LAYOUTS = {0: "cose", 1: "circle", 2: "dagre", 3: "breadthfirst"};

// The boxes of the states are as large as their names : the layouts must know it, or they overlap them
const LAYOUT_OPTIONS = {
	cose: {nodeDimensionsIncludeLabels: true, idealEdgeLength: 100, nodeRepulsion: 1000000, nodeOverlap: 40, numIter: 2000},
	dagre: {nodeDimensionsIncludeLabels: true},
	breadthfirst: {nodeDimensionsIncludeLabels: true},
};

// Colors of the transitions, from the least to the most probable (light to dark blue, as in pyMaBoSS)
const LOW_COLOR = [198, 219, 239];
const HIGH_COLOR = [8, 48, 107];

function probaColor(proba) {
	const rgb = LOW_COLOR.map((low, i) => Math.round(low + (HIGH_COLOR[i] - low) * proba));
	return "rgb(" + rgb.join(",") + ")";
}

function formatProba(proba) {
	return (proba * 100).toFixed(proba < 0.1 ? 1 : 0) + "%";
}


class MaBossObservedGraph extends React.Component {

	constructor(props) {
		super(props);

		this.state = {
			cutoff: 0,
			layout: "cose",
			showProbas: true,
			version: 0,
		};

		this.cy = null;
		this.style = {width: '100%', height: '550px', border: '1px solid #dee2e6'};
	}

	setCutoff(e) {
		const value = parseFloat(e.target.value);
		this.setState({cutoff: isNaN(value) ? 0 : Math.min(Math.max(value, 0), 100) / 100});
	}

	download() {
		if (this.cy !== null) {
			const blob = this.cy.png({output: 'blob', full: true, bg: '#fff', scale: 2});
			FileSaver.saveAs(blob, (this.props.simulationName || "simulation") + "_observed_graph.png");
		}
	}

	render() {
		// Cytoscape can't lay out a graph in a hidden tab
		if (!this.props.active) {
			return null;
		}

		if (!this.props.loaded) {
			return this.props.simulationId !== null ? <LoadingIcon width="3rem"/> : <div/>;
		}

		const graph = this.props.observedGraph;

		if (graph === null || graph === undefined || graph.nodes === undefined) {
			return <div className="mt-3 text-muted">{
				(graph !== null && graph !== undefined && graph.error !== undefined) ? graph.error :
				"No nodes were selected for the observed graph when this simulation was created " +
				"(tab \"Observed graph\" of the new simulation)"
			}</div>;
		}

		// Like pyMaBoSS : unlikely transitions are left out, and the states which no longer have any
		const edges = graph.edges.filter(edge => edge[2] >= this.state.cutoff);
		const states = graph.states.filter(state => edges.some(edge => edge[0] === state || edge[1] === state));

		const elements = states.map(state => ({
			data: {id: state, label: state.split(" -- ").join("\n")}
		})).concat(edges.map((edge, index) => ({
			data: {
				id: "edge_" + index, source: edge[0], target: edge[1],
				color: probaColor(edge[2]), width: 1 + 4 * edge[2], label: formatProba(edge[2])
			}
		})));

		const stylesheet = [
			{
				selector: 'node',
				style: {
					'shape': 'roundrectangle',
					'background-color': '#fff',
					'border-width': 2,
					'border-color': '#000',
					'content': 'data(label)',
					'text-wrap': 'wrap',
					'text-valign': 'center',
					'text-halign': 'center',
					'width': 'label',
					'height': 'label',
					'padding': 10,
					'font-size': 14,
				}
			}, {
				selector: 'edge',
				style: {
					'curve-style': 'bezier',
					'line-color': 'data(color)',
					'target-arrow-color': 'data(color)',
					'target-arrow-shape': 'triangle',
					'width': 'data(width)',
					'label': this.state.showProbas ? 'data(label)' : '',
					'font-size': 10,
					'text-background-color': '#fff',
					'text-background-opacity': 1,
					'text-background-padding': 1,
				}
			}
		];

		return <React.Fragment>
			<div className="d-flex align-items-center flex-wrap mt-3 mb-2">
				<Label for="observedGraphCutoff" className="mb-0 mr-2">Hide transitions under</Label>
				<Input
					type="number" id="observedGraphCutoff" min={0} max={100} step={1}
					style={{width: '6rem'}} className="mr-1"
					value={Math.round(this.state.cutoff * 1000) / 10}
					onChange={(e) => this.setCutoff(e)}
				/>
				<span className="mr-4">%</span>
				<span className="mr-2">Probabilities</span>
				<span className="mr-4">
					<Switch checked={this.state.showProbas} toggle={() => this.setState({showProbas: !this.state.showProbas})}/>
				</span>
				<MyDropdown
					label={this.state.layout} dict={LAYOUTS} width={"10rem"} inline={true}
					callback={ind => this.setState({layout: LAYOUTS[ind]})}
				/>
				<Button className="ml-1" title="Layout again" onClick={() => this.setState({version: this.state.version + 1})}>
					<FontAwesomeIcon icon={faSyncAlt}/>
				</Button>
				<Button className="ml-1" title="Download as PNG" onClick={() => this.download()}>
					<FontAwesomeIcon icon={faDownload}/>
				</Button>
			</div>
			{ states.length > 0 ?
				<CytoscapeComponent
					// Drawn again, with a new layout, when the transitions shown change
					key={[this.state.layout, this.state.cutoff, this.state.version, this.props.simulationId].join("|")}
					elements={elements} stylesheet={stylesheet} style={this.style}
					layout={{name: this.state.layout, animate: false, fit: true, padding: 30, ...LAYOUT_OPTIONS[this.state.layout]}}
					cy={(cy) => { this.cy = cy; }}
				/> :
				<div className="text-muted">No transition between the states of {graph.nodes.join(", ")} is that likely</div>
			}
			<div className="d-flex align-items-center flex-wrap mt-2">
				<small className="mr-2">0%</small>
				<div style={{
					width: '12rem', height: '0.75rem',
					background: "linear-gradient(to right, " + probaColor(0) + ", " + probaColor(1) + ")"
				}}/>
				<small className="ml-2 mr-4">100%</small>
				<small className="text-muted">
					States of {graph.nodes.join(", ")} (&lt;nil&gt; : none of them is active). Each arrow is the
					probability that the next change of these nodes leads to that state.
				</small>
			</div>
		</React.Fragment>;
	}
}

export default MaBossObservedGraph;
