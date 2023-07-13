from rest_framework.response import Response
from rest_framework import status

from api.views.HasMaBoSSSimulation import HasMaBoSSSimulation
from json import loads
import maboss, json
import numpy as np
from sklearn.decomposition import PCA

class MaBoSSResultsFixedPointsPCA(HasMaBoSSSimulation):

	def get(self, request, project_id, simulation_id):

		HasMaBoSSSimulation.load(self, request, project_id, simulation_id)

		model = maboss.load(self.getBNDFilePath(), self.getCFGFilePath())

		if self.simulation.fixpoints is not None:

			fixed_points = loads(self.simulation.fixpoints)
			output_vars = [label for label, node in model.network.items() if not node.is_internal]
			nb_nodes = len(output_vars)

			res = np.zeros((nb_nodes, 0))
			for i, proba in enumerate(fixed_points["Proba"]):
				t_res = np.zeros((nb_nodes, 1))

				for node in output_vars:
					t_res[output_vars.index(node)] = fixed_points[node][str(i)]
				res = np.append(res, t_res, axis=1)

			mat = np.transpose(res)

			pca = PCA()
			pca_res = pca.fit(mat)
			x_new = pca.transform(mat)

			res = {}
			for i, state in enumerate(fixed_points["State"]):
				res.update({fixed_points["State"][state]: list(x_new[i, 0:2])})

			raw_arrows = np.transpose(pca_res.components_[0:2, :])

			# Adjusting arrow length to fit in the graph
			max_x_arrows = max(raw_arrows[:, 0])
			min_x_arrows = min(raw_arrows[:, 0])
			max_x_values = max(x_new[:, 0])
			min_x_values = min(x_new[:, 0])
			min_x_ratio = min_x_values / min_x_arrows
			max_x_ratio = max_x_values / max_x_arrows
			x_ratio = min(min_x_ratio, max_x_ratio)

			max_y_arrows = max(raw_arrows[:, 1])
			min_y_arrows = min(raw_arrows[:, 1])
			max_y_values = max(x_new[:, 1])
			min_y_values = min(x_new[:, 1])
			min_y_ratio = min_y_values / min_y_arrows
			max_y_ratio = max_y_values / max_y_arrows
			y_ratio = min(min_y_ratio, max_y_ratio)

			from math import log10, floor

			def round_sig(x, sig=2):
				if x == 0.0:
					return x
				return round(x, sig - int(floor(log10(abs(x)))) - 1)

			values = []
			names = []
			for i, arrow_raw in enumerate(raw_arrows):
				as_list = [round(val, 2) for val in list(arrow_raw)]
				if as_list not in values:
					values.append(as_list)
					names.append([output_vars[i]])

				else:
					names[values.index(as_list)].append(output_vars[i])

			values = [[value[0]*x_ratio, value[1]*y_ratio] for value in values]

			return Response({
				'status': 'Finished', 'data': json.dumps(res),
				'arrows': values, 'arrowlabels': names,
				'explainedVariance': [round_sig(value*100, 4) for value in list(pca.explained_variance_ratio_[0:2])]
			})

		else:
			return Response({'status': 'Busy'})

class MaBoSSResultsSteadyStatesPCA(HasMaBoSSSimulation):

	def get(self, request, project_id, simulation_id):

		HasMaBoSSSimulation.load(self, request, project_id, simulation_id)

		model = maboss.load(self.getBNDFilePath(), self.getCFGFilePath())

		if self.simulation.states_probtraj is not None:

			states_probtraj = loads(self.simulation.states_probtraj)
			states_lastprob = {}
			for state, values in states_probtraj.items():
				list_values = list(values.values())
				states_lastprob.update({state: list_values[len(list_values) - 1]})

			nodes = [name for name, node in model.network.items() if not node.is_internal]
			nb_nodes = len(nodes)
			nb_fp = len(states_lastprob.keys())
			states = []

			res = np.zeros((nb_nodes, 0))
			for index, proba in states_lastprob.items():
				if proba > 0.01:
					states.append(index)
					if index == "<nil>":
						res = np.append(res, np.zeros((nb_nodes, 1)), axis=1)
					else:
						t_res = np.zeros((nb_nodes, 1))
						for node in [t_node.strip() for t_node in index.split("--")]:
							#                 print(node)
							t_res[nodes.index(node)] = 1

						res = np.append(res, t_res, axis=1)
			columns = ["FP%d" % i for i in range(res.shape[1])]
			mat = np.transpose(res)


			pca = PCA()
			pca_res = pca.fit(mat)
			x_new = pca.transform(mat)

			res = {}
			for i, state in enumerate(states):
				res.update({state: list(x_new[i, 0:2])})

			raw_arrows = np.transpose(pca_res.components_[0:2, :])

			# Adjusting arrow length to fit in the graph
			max_x_arrows = max(raw_arrows[:, 0])
			min_x_arrows = min(raw_arrows[:, 0])
			max_x_values = max(x_new[:, 0])
			min_x_values = min(x_new[:, 0])
			min_x_ratio = abs(min_x_values / min_x_arrows)
			max_x_ratio = abs(max_x_values / max_x_arrows)
			x_ratio = min(min_x_ratio, max_x_ratio)

			max_y_arrows = max(raw_arrows[:, 1])
			min_y_arrows = min(raw_arrows[:, 1])
			max_y_values = max(x_new[:, 1])
			min_y_values = min(x_new[:, 1])
			min_y_ratio = abs(min_y_values / min_y_arrows)
			max_y_ratio = abs(max_y_values / max_y_arrows)
			y_ratio = min(min_y_ratio, max_y_ratio)

			from math import log10, floor

			def round_sig(x, sig=2):
				if x == 0.0:
					return x
				return round(x, sig - int(floor(log10(abs(x)))) - 1)

			values = []
			names = []
			for i, arrow_raw in enumerate(raw_arrows):
				as_list = [round(val, 2) for val in list(arrow_raw)]
				if as_list not in values:
					values.append(as_list)
					names.append([nodes[i]])

				else:
					names[values.index(as_list)].append(nodes[i])

			values = [[value[0] * x_ratio, value[1] * y_ratio] for value in values]

			return Response({
				'status': 'Finished', 'data': json.dumps(res),
				'arrows': values, 'arrowlabels': names,
				'explainedVariance': [round_sig(value * 100, 4) for value in
									  list(pca.explained_variance_ratio_[0:2])]
			})

		else:
			return Response({'status': 'Busy'})


class MaBoSSResultsFixedPoints(HasMaBoSSSimulation):

	def get(self, request, project_id, simulation_id):

		HasMaBoSSSimulation.load(self, request, project_id, simulation_id)

		fixed_points = None

		if self.simulation.fixpoints is not None:
			fixed_points = loads(self.simulation.fixpoints)
			# print(fixed_points)
			nodes = list(fixed_points.keys())[3:]
			new_fps = []
			if 'FP' in fixed_points.keys():
				for i in range(len(fixed_points['FP'])):
					new_fps.append({
						"proba": fixed_points['Proba'][str(i)],
						"nodes": {node:fixed_points[node][str(i)] for node in nodes}
					})
			fixed_points = new_fps
			
		return Response(
			{
				'fixed_points': fixed_points,
				'status': self.simulation.status
			},
			status=status.HTTP_200_OK
		)



class MaBoSSResultsLastState(HasMaBoSSSimulation):

	def get(self, request, project_id, simulation_id):

		HasMaBoSSSimulation.load(self, request, project_id, simulation_id)

		fixed_points = None

		if self.simulation.states_probtraj is not None:
			fixed_points = {}
			for key, values in loads(self.simulation.states_probtraj).items():
				last_time = list(values.keys())[len(values.keys())-1]
				if values[last_time] > 0.01:
					fixed_points.update({key: values[last_time]})

		return Response(
			{
				'last_states': fixed_points,
				'status': self.simulation.status
			},
			status=status.HTTP_200_OK
		)


class MaBoSSResultsStatesProbTraj(HasMaBoSSSimulation):

	def get(self, request, project_id, simulation_id):

		HasMaBoSSSimulation.load(self, request, project_id, simulation_id)

		if self.simulation.states_probtraj is not None:
			states_probtraj = {}
			for key, value in loads(self.simulation.states_probtraj).items():
				values = list(value.values())
				if max(values) > 0.01:
					states_probtraj.update({key: value})

			# states_probtraj = {key: value for key, value in loads(self.simulation.states_probtraj).items() if list(value.values())[len(value.values()) - 1] > 0.01}

		else:
			states_probtraj = None

		return Response(
			{
				'states_probtraj': states_probtraj,
				'status': self.simulation.status
			},
			status=status.HTTP_200_OK
		)


class MaBoSSResultsNodesProbTraj(HasMaBoSSSimulation):

	def get(self, request, project_id, simulation_id):

		HasMaBoSSSimulation.load(self, request, project_id, simulation_id)

		if self.simulation.nodes_probtraj is not None:
			nodes_probtraj = loads(self.simulation.nodes_probtraj)

		else:
			nodes_probtraj = None

		return Response(
			{
				'nodes_probtraj': nodes_probtraj,
				'status': self.simulation.status
			},
			status=status.HTTP_200_OK
		)
