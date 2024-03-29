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

# @app.route('/api/generate_zones', methods=['POST'])
@app.route('/api/generate_zones', methods=['POST', 'OPTIONS'])
@cross_origin(origin='http://localhost:3000')  # Specific CORS configuration for this route
def generate_zones():
    # return jsonify(message='Zone generated successfully!')
    data = request.get_json()

    # Percentage of max allowed FRL deviation from district average/
    frl_dev = data['FRLDeviation']
    # Number of Zones
    Z = data['Number_of_Zones']

    # Percentage of max allowed racial deviation from district average
    # Computed only for Asian, Hispanic, White
    racial_dev = data['RacialDeviation']

    # Additional request, based on the request box.
    additional_request = data['AdditionalRequest']

    print(f'Received ethnic diversity value: {ethnic_diversity}')

    return send_file('Figures/zone_partition.png', mimetype='image/png')



if __name__ == '__main__':
    app.run()
