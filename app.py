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

if __name__ == '__main__':
    app.run()



# learn react