# from flask import Flask, jsonify, render_template

# app = Flask(__name__)

# # @app.route('/health', methods=['GET'])
# # def health_check():
# #     return render_template('health.html')

# @app.route('/')
# def home():
#     return render_template('index.html')


# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5000)

from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/health')
def health():
    return render_template('health.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)