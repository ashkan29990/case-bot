from flask import Flask, request, jsonify
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/search')
def search():
    query = request.args.get('q')
    if not query:
        return jsonify({'error': 'query required'}), 400
    
    response = requests.get(
        'https://edaalat.org/request/cases',
        params={'q': query},
        headers={'Referer': 'https://edaalat.org/'}
    )
    return jsonify(response.json())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
