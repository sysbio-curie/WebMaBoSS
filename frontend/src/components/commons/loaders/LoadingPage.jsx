import React from "react";

import './loading-page.scss';
import loading_icon from '../../../images/loading.svg';
import loading_icon_dark from '../../../images/loading_dark.svg';

class LoadingPage extends React.Component {

	render() {

		const src = this.props.dark !== undefined ? loading_icon_dark : loading_icon;
		return <div className="loading-page">
			<img src={src} />
		</div>;
	}
}

export default LoadingPage;