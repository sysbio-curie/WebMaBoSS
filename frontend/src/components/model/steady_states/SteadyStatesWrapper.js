import React from "react";
import Loadable from "react-loadable";
import LoadingPage from "../../commons/loaders/LoadingPage";


const SteadyStatesWrapper = Loadable({
	loader: () => import("./ModelSteadyStates"),
	loading: () => <LoadingPage width="5rem"/>
});


export {SteadyStatesWrapper};