from flask import Flask, request, jsonify
from flask_restful import Api, Resource
import sqlite3
from functools import wraps


app = Flask(__name__)
api = Api(app)
API_TOKEN = "your_secret_token_here"

conn = sqlite3.connect('cards.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    responsible TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

conn.commit()
conn.close()


def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None

        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(" ")[1]

        if not token or token != API_TOKEN:
            return jsonify({'message': 'Token is missing or invalid'}), 403

        return f(*args, **kwargs)

    return decorated_function


class Card(Resource):
    @token_required
    def post(self):
        if not request.json or not 'title' in request.json or not 'responsible' in request.json:
            return {'error': 'Bad request'}, 400
        card = {
            'title': request.json['title'],
            'description': request.json['description'],
            'responsible': request.json['responsible'],
        }
        self.add_card_to_db(card['title'], card['description'], card['responsible'])
        return {'message': 'Card added successfully'}, 201

    def add_card_to_db(self, title, description, responsible):
        conn = sqlite3.connect('cards.db')
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO cards (title, description, responsible)
        VALUES (?, ?, ?)
        ''', (title, description, responsible))
        conn.commit()
        conn.close()


class UserCards(Resource):
    @token_required
    def get(self, username):
        if not username or len(username.strip()) == 0:
            return jsonify({'error': 'Invalid username provided'}), 400

        conn = sqlite3.connect('cards.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
        SELECT * FROM cards WHERE responsible = ? ORDER BY timestamp DESC
        ''', (username,))
        rows = cursor.fetchall()
        conn.close()

        cards = [dict(row) for row in rows]

        return jsonify(cards)


class AllCards(Resource):
    @token_required
    def get(self):
        conn = sqlite3.connect('cards.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
        SELECT * FROM cards ORDER BY timestamp DESC
        ''')
        rows = cursor.fetchall()
        conn.close()

        cards = [dict(row) for row in rows]

        return jsonify(cards)


api.add_resource(UserCards, '/task/<string:username>')
api.add_resource(Card, '/task/save')
api.add_resource(AllCards, '/task')

if __name__ == '__main__':
    app.run(debug=True)