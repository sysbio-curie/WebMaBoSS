from django.urls import path, re_path, include

from api.views.logical_model.LogicalModel import (
	LogicalModelFile, LogicalModelSBMLFile, LogicalModelMaBoSSBNDFile, LogicalModelMaBoSSCFGFile, 
	LogicalModelBNetFile, LogicalModelName, LogicalModelNodes, LogicalModelGraph, LogicalModelGraphRaw,
	LogicalModelGraphRawModify
)
from api.views.logical_model.LogicalModels import LogicalModels
from api.views.logical_model.LogicalModelsTags import LogicalModelsTags, TaggedLogicalModelFile, TaggedLogicalModelSBMLFile
from api.views.Projects import Projects, ProjectDemoModels
from api.views.BioLQMSimulation import LogicalModelSteadyStates

from api.views.maboss.MaBossServerView import MaBoSSServerView, CheckServerView
from api.views.maboss.MaBoSSSimulationView import MaBoSSSimulationView, MaBoSSSimulationRemove, MaBossSettings, MaBoSSSimulationBNDFile, MaBoSSSimulationCFGFile, MaBoSSSimulationNewModel, MaBoSSSimulationStatusView
from api.views.maboss.MaBoSSSensitivityAnalysisView import MaBoSSSensitivityAnalysisView, MaBoSSSensitivityAnalysisRemove, MaBoSSSensitivitySteadyStatesView, MaBoSSSensitivityStatusView
from api.views.maboss.MaBoSSResultsView import MaBoSSResultsLastState, MaBoSSResultsFixedPoints, MaBoSSResultsNodesProbTraj, MaBoSSResultsStatesProbTraj, MaBoSSResultsFixedPointsPCA, MaBoSSResultsSteadyStatesPCA, MaBoSSResultsObservedGraph
from api.views.maboss.MaBoSSModel import (
	MaBoSSSpeciesFormulas, MaBoSSSpeciesFormula, MaBoSSCheckFormula,
	MaBoSSParameters, MaBoSSParameter, MaBoSSCheckParameter,
	MaBoSSInitialStates, MaBoSSModelSettings, MaBoSSOutputs
)
from api.views.AuthView import TestAuthView, LogoutViewEx, UserEmailView
from api.views.InstallStatus import InstallStatus
from api.views.Monitoring import (
	MonitoringAccess, MonitoringActivity, MonitoringStorage, MonitoringOptimize, MonitoringUsers, MonitoringCleanup
)

from api.views.CCApi import CCApi
from api.views.BioModelsAPI import BioModelsAPI
from dj_rest_auth.views import LoginView, PasswordChangeView
from dj_rest_auth.registration.views import RegisterView, VerifyEmailView

urlpatterns = [
	re_path('api-auth/', include('rest_framework.urls')),
	path('api/auth/is_logged_in', TestAuthView.as_view(), name='is_logged_in', ),
	path('api/auth/logout', LogoutViewEx.as_view(), name='logout', ),
	path('api/auth/login', LoginView.as_view(), name='login', ),
	path('api/auth/register', RegisterView.as_view(), name='register'),
	path('api/auth/email', UserEmailView.as_view(), name='user_email'),
	path('api/auth/password/change', PasswordChangeView.as_view(), name='password_change'),
	path('api/auth/account-confirm-email', VerifyEmailView.as_view(), name='account_email_verification_sent'),
	path('api/auth/account-confirm-email/<str:key>', VerifyEmailView.as_view(), name='account_confirm_email'),

	path('api/monitoring/', MonitoringAccess.as_view()),
	path('api/monitoring/activity', MonitoringActivity.as_view()),
	path('api/monitoring/storage', MonitoringStorage.as_view()),
	path('api/monitoring/storage/optimize', MonitoringOptimize.as_view()),
	path('api/monitoring/users', MonitoringUsers.as_view()),
	path('api/monitoring/cleanup', MonitoringCleanup.as_view()),

	path('api/projects/', Projects.as_view()),
	path('api/projects/<int:project_id>', Projects.as_view()),
	path('api/projects/<int:project_id>/demo_models', ProjectDemoModels.as_view()),

	# path('api/logical_models/', LogicalModels.as_view()),
	path('api/logical_models/<int:project_id>/', LogicalModels.as_view()),
	path('api/logical_models/<int:project_id>/<int:model_id>', LogicalModels.as_view()),
	path('api/logical_models/<int:project_id>/<int:model_id>/tags/', LogicalModelsTags.as_view()),
	path('api/logical_models/<int:project_id>/<int:model_id>/tags/<str:tag>', LogicalModelsTags.as_view()),

	path('api/logical_models/<int:project_id>/<int:model_id>/tags/<str:tag>/file', TaggedLogicalModelFile.as_view()),
	path('api/logical_models/<int:project_id>/<int:model_id>/tags/<str:tag>/sbmlfile', TaggedLogicalModelSBMLFile.as_view()),

	path('api/logical_models/<int:project_id>/<int:model_id>/file', LogicalModelFile.as_view()),
	path('api/logical_models/<int:project_id>/<int:model_id>/sbmlfile', LogicalModelSBMLFile.as_view()),
	path('api/logical_models/<int:project_id>/<int:model_id>/bndfile', LogicalModelMaBoSSBNDFile.as_view()),
	path('api/logical_models/<int:project_id>/<int:model_id>/cfgfile', LogicalModelMaBoSSCFGFile.as_view()),
	path('api/logical_models/<int:project_id>/<int:model_id>/bnetfile', LogicalModelBNetFile.as_view()),

	path('api/logical_model/<int:project_id>/<int:model_id>/name', LogicalModelName.as_view()),
	path('api/logical_model/<int:project_id>/<int:model_id>/nodes', LogicalModelNodes.as_view()),
	path('api/logical_model/<int:project_id>/<int:model_id>/graph', LogicalModelGraph.as_view()),
	path('api/logical_model/<int:project_id>/<int:model_id>/graph_raw', LogicalModelGraphRaw.as_view()),
	path('api/logical_model/<int:project_id>/<int:model_id>/graph_raw/<str:node>', LogicalModelGraphRawModify.as_view()),
	path('api/logical_model/<int:project_id>/<int:model_id>/steady_states', LogicalModelSteadyStates.as_view()),
	path('api/logical_model/<int:project_id>/<int:model_id>/maboss', MaBoSSSimulationView.as_view()),
	path('api/logical_model/<int:project_id>/<int:model_id>/maboss_sensitivity', MaBoSSSensitivityAnalysisView.as_view()),
	path('api/logical_model/<int:project_id>/<int:model_id>/maboss/settings/', MaBossSettings.as_view()),

	path('api/logical_model/<int:project_id>/<int:model_id>/formulas', MaBoSSSpeciesFormulas.as_view()),
	path('api/logical_model/<int:project_id>/<int:model_id>/formula/<str:node>/<str:field>', MaBoSSSpeciesFormula.as_view()),
	path('api/logical_model/<int:project_id>/<int:model_id>/check_formula/<str:node>/<str:field>', MaBoSSCheckFormula.as_view()),

	path('api/logical_model/<int:project_id>/<int:model_id>/parameters', MaBoSSParameters.as_view()),
	path('api/logical_model/<int:project_id>/<int:model_id>/parameter/<str:name>', MaBoSSParameter.as_view()),
	path('api/logical_model/<int:project_id>/<int:model_id>/check_parameter/<str:name>', MaBoSSCheckParameter.as_view()),

	path('api/logical_model/<int:project_id>/<int:model_id>/initial_states', MaBoSSInitialStates.as_view()),
	path('api/logical_model/<int:project_id>/<int:model_id>/outputs', MaBoSSOutputs.as_view()),
	path('api/logical_model/<int:project_id>/<int:model_id>/settings', MaBoSSModelSettings.as_view()),

	path('api/maboss/<int:project_id>/<int:simulation_id>/', MaBoSSSimulationRemove.as_view()),
	path('api/maboss/<int:project_id>/<int:simulation_id>/status', MaBoSSSimulationStatusView.as_view()),
	path('api/maboss/<int:project_id>/<int:simulation_id>/fixed_points/', MaBoSSResultsFixedPoints.as_view()),
	path('api/maboss/<int:project_id>/<int:simulation_id>/last_states/', MaBoSSResultsLastState.as_view()),
	path('api/maboss/<int:project_id>/<int:simulation_id>/states_trajs/', MaBoSSResultsStatesProbTraj.as_view()),
	path('api/maboss/<int:project_id>/<int:simulation_id>/nodes_trajs/', MaBoSSResultsNodesProbTraj.as_view()),
	path('api/maboss/<int:project_id>/<int:simulation_id>/observed_graph/', MaBoSSResultsObservedGraph.as_view()),
	path('api/maboss/<int:project_id>/<int:simulation_id>/bnd_file', MaBoSSSimulationBNDFile.as_view()),
	path('api/maboss/<int:project_id>/<int:simulation_id>/cfg_file', MaBoSSSimulationCFGFile.as_view()),
	path('api/maboss/<int:project_id>/<int:simulation_id>/new_model', MaBoSSSimulationNewModel.as_view()),
	path('api/maboss/<int:project_id>/<int:simulation_id>/pca', MaBoSSResultsFixedPointsPCA.as_view()),
	path('api/maboss/<int:project_id>/<int:simulation_id>/sspca', MaBoSSResultsSteadyStatesPCA.as_view()),

	path('api/maboss_sensitivity/<int:project_id>/<int:analysis_id>/', MaBoSSSensitivityAnalysisRemove.as_view()),
	path('api/maboss_sensitivity/<int:project_id>/<int:analysis_id>/status', MaBoSSSensitivityStatusView.as_view()),
	path('api/maboss_sensitivity/<int:project_id>/<int:analysis_id>/steady_states/', MaBoSSSensitivitySteadyStatesView.as_view()),

	path('api/maboss/servers/', MaBoSSServerView.as_view()),
	path('api/maboss/servers/<int:server_id>', MaBoSSServerView.as_view()),
	path('api/maboss/check_server/<int:server_id>', CheckServerView.as_view()),

	path('api/ccapi/all', CCApi.as_view()),
	path('api/biomodels/all', BioModelsAPI.as_view()),

	path('api/install_status', InstallStatus.as_view()),
]
