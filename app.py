from flask import Flask, send_file, jsonify, request
from flask_cors import CORS, cross_origin
from Zone_Generation.Config.Constants import *
from filter_request import Filter_Request
import time

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": ["https://zone-optimizer.vercel.app", "http://localhost:3000"]}})


@app.route('/')
def home():
    response_data = {
        'home': 'This is the home page'
    }
    return jsonify(response_data)


@app.route('/api/generate_zones_test', methods=['POST', 'OPTIONS'])
@cross_origin(origin='http://localhost:3000')  # Specific CORS configuration for this route
def generate_zones_test():
    data = request.get_json()
    print("3: generate_zones_test3  was called", data)
    response_data = {
        'title': 'Test Title'
    }
    return jsonify(response_data)
    # return send_file('Figures/zone_partition.png', mimetype='image/png')




# expected inputs:
    # data json, with data['FRLDeviation'], data['Number_of_Zones'], data['Number_of_Zones']
# expected outputs:
#     image of the zoning map
#     data json for latex file:
#         Latex_formula: {
#             'Variables': {
#                 'A': "Definition of the new variable A, in the formula (if any new variables are defined)",
#                 'B': "Definition of the new variable B, in the formula (if any new variables are defined)",
#             },
#             'Formula': 'Theoretical Latex formula, for the constraint that was requested. '
#                        'Dont make any changes to the original formula'
#         }
@app.route('/api/generate_zones', methods=['POST', 'OPTIONS'])
# @cross_origin(origin='http://localhost:3000')  # Specific CORS configuration for this route
@cross_origin(origins=['https://zone-optimizer.vercel.app', 'http://localhost:3000'])


def generate_zones_backend():
    data = request.get_json()

    user_inputs = {}
    user_inputs["number_of_zones"] = data['number_of_zones']
    user_inputs["FRL_Dev"] = data['FRL_Dev']
    user_inputs["request_constraint"] = data['request_constraint']

    print("Initialized User Inputs: ", user_inputs)

    # Latex_Formula = {
    #     'Variables': {
    #         'var1_u': 'Definiton of Var 111.',
    #         'var2_u': 'Definiton of Var 2.',
    #
    #     },
    #     'Formula': '(1-0.24) \cdot (\sum_{u \in U} mathScore_u) / Z \leq \sum_{u \in U} mathScore_u . x_{u,z}  \leq 1 + 0.24) \cdot (\sum_{u \in U} mathScore_u)/Z   \quad  ∀ z \in Z'
    # }
    # response_data = {}
    # response_data['Latex_Formula'] = Latex_Formula
    # response_data['zone_dict'] = zone_dict
    # return jsonify(response_data)

    FR = Filter_Request(user_inputs)
    FR.fetch_llm_response()
    FR.filter_zones()

    print(FR.solution_status.keys())
    if "Latex_Formula" in FR.solution_status:
        print("\n FR.solution_status[Latex_Formula]: ",  FR.solution_status["Latex_Formula"])
    if "LLM_Request_Execution" in FR.solution_status:
        print("LLM_Request_Execution ", FR.solution_status["LLM_Request_Execution"])
    # print("\n FR.solution_status[zone_dict]: ", FR.solution_status["zone_dict"])


    return jsonify(FR.solution_status)


if __name__ == '__main__':
    app.run()


