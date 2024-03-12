import React from "react";

import loading_icon from '../../../images/loading.svg';
import loading_icon_dark from '../../../images/loading_dark.svg';

class LoadingIcon extends React.Component {

	render() {

		const src = this.props.dark !== undefined ? loading_icon_dark : loading_icon;
		return <div align="center">
			<img
				src={src}
				style={{width: this.props.width}} />
			{
				this.props.percent !== undefined ?
				<span>{Math.round(this.props.percent * 100.0)}%</span> : null
			}
		</div>;
	}
}

export default LoadingIcon;