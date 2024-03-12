import React from "react";
import logo_eu from '../../images/Flag_of_Europe.png';

const EuropeanFlag = props => <div align="center">
<img
	src={logo_eu}
	style={{width: props.width}} />
</div>;

export default EuropeanFlag;