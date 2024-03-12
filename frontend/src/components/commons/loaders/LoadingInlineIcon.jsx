import React from "react";

import loading_icon from '../../../images/loading.svg';
import loading_icon_dark from '../../../images/loading_dark.svg';

class LoadingInlineIcon extends React.Component {

	render() {

		const src = this.props.dark !== undefined ? loading_icon_dark : loading_icon;
		return <span align="center" className={"d-inline-flex" + " " + this.props.className}>
			<img
				src={src}
				className="align-items-center"
				style={{width: this.props.width}} />
		</span>;
	}
}

export default LoadingInlineIcon;