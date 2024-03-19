from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'


@app.route('/mobin')
def shomal():
    return {
        'title': 'koskesh'
    }


@app.route('/api/generate_zones', methods=['POST'])
def generate_zones():
    return 'Zone generated successfully!'




if __name__ == '__main__':
    app.run()



# learn react