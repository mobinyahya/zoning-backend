from flask import Flask, send_file, jsonify, request
from flask_cors import CORS, cross_origin

app = Flask(__name__)
# CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})
CORS(app)  # Global CORS configuration


@app.route('/')
def hello_world():
    return 'Hello, World!'


@app.route('/test')
def shomal():
    return {
        'title': 'Test Title'
    }

@app.route('/api/generate_zones_test', methods=['POST', 'OPTIONS'])
@cross_origin(origin='http://localhost:3000')  # Specific CORS configuration for this route
def generate_zones_test():
    data = request.get_json()
    print("generate_zones_test  was called")
    return send_file('Figures/zone_partition.png', mimetype='image/png')


# @app.route('/api/generate_zones', methods=['POST'])
@app.route('/api/generate_zones', methods=['POST', 'OPTIONS'])
@cross_origin(origin='http://localhost:3000')  # Specific CORS configuration for this route
def generate_zones_backend():
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

    # return jsonify(message='Zone generated successfully!')
    data = request.get_json()

    # Percentage of max allowed FRL deviation from district average/
    frl_dev = data['FRLDeviation']
    # Number of Zones
    Z = data['Number_of_Zones']

    # Percentage of max allowed racial deviation from district average
    # Computed only for Asian, Hispanic, White
    racial_dev = data['Number_of_Zones']

    # Additional request, based on the request box.
    additional_request = data['AdditionalRequest']


    Sample_Latex_formula ={
        'Variables': {
            'A': "Definition of the new variable A, in the formula (if any new variables are defined)",
            'B': "Definition of the new variable B, in the formula (if any new variables are defined)",
        },
        'Formula': 'Theoretical Latex formula, for the constraint that was requested. '
                   'Dont make any changes to the original formula'
    }
    print(Sample_Latex_formula['Variables'])

    return send_file('Figures/zone_partition.png', mimetype='image/png')



if __name__ == '__main__':
    app.run()
