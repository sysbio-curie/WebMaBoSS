import AuthCalls from "./AuthCalls";
import MaBoSSCalls from "./MaBoSSCalls";
import MaBoSSServerCalls from "./MaBoSSServerCalls";
import GenericCalls from "./GenericCalls";
import ProjectCalls from "./ProjectCalls";
import ModelsCalls from "./ModelsCalls";
import ModelTagsCalls from "./ModelTagsCalls";
import ModelCalls from "./ModelCalls";
import RepositoriesCalls from "./RepositoriesCalls";
import MonitoringCalls from "./MonitoringCalls";

class APICalls {
	static AuthCalls = AuthCalls;
	static MaBoSSCalls = MaBoSSCalls;
	static MaBoSSServerCalls = MaBoSSServerCalls;
	static GenericCalls = GenericCalls;
	static ProjectCalls = ProjectCalls;
	static ModelsCalls = ModelsCalls;
	static ModelTagsCalls = ModelTagsCalls;
	static ModelCalls = ModelCalls;
	static RepositoriesCalls = RepositoriesCalls;
	static MonitoringCalls = MonitoringCalls;
}
export default APICalls;