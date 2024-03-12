import React from "react";

import maboss_logo from '../../images/maboss_logo.jpg';

class MaBoSSIcon extends React.Component {

	render() {

		return <div align="center">
			<img
				src={maboss_logo}
				style={{width: this.props.width}} />
		</div>;
	}
}

export default MaBoSSIcon;