```python
from flask import Flask, request, jsonify, send_from_directory
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from werkzeug.utils import secure_filename
import sqlite3
import os
from datetime import datetime
import pytz

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change in production
app.config['JWT_SECRET_KEY'] = 'your-jwt-secret-key'  # Change in production
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB limit
jwt = JWTManager(app)

# Ensure upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Database setup
def init_db():
    conn = sqlite3.connect('studymate.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, email TEXT UNIQUE, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS uploads 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, user_id INTEGER, upload_time TEXT, 
                  FOREIGN KEY (user_id) REFERENCES users(id))''')
    conn.commit()
    conn.close()

init_db()

# Helper function to get current IST time
def get_ist_time():
    ist = pytz.timezone('Asia/Kolkata')
    return datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')

# Signup endpoint
@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')  # Hash in production

    if not all([username, email, password]):
        return jsonify({'error': 'All fields are required'}), 400

    conn = sqlite3.connect('studymate.db')
    c = conn.cursor()
    c.execute("SELECT username, email FROM users WHERE username = ? OR email = ?", (username, email))
    if c.fetchone():
        conn.close()
        return jsonify({'error': 'Username or email already exists'}), 400

    c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", (username, email, password))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Signup successful', 'redirect': 'index.html'}), 201

# Login endpoint
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')  # Verify hashed password in production

    conn = sqlite3.connect('studymate.db')
    c = conn.cursor()
    c.execute("SELECT id, password FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()

    if not user or user[1] != password:  # Simple check; use hashing
        return jsonify({'error': 'Invalid credentials'}), 401

    access_token = create_access_token(identity={'username': username, 'user_id': user[0]})
    return jsonify({'message': 'Login successful', 'token': access_token, 'redirect': 'studymate.html'}), 200

# Logout endpoint
@app.route('/api/logout', methods=['POST'])
@jwt_required()
def logout():
    return jsonify({'message': 'Logout successful', 'redirect': 'index.html'}), 200

# Upload endpoint (handles both quick and bulk)
@app.route('/api/upload', methods=['POST'])
@jwt_required()
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    files = request.files.getlist('file')  # Supports multiple files for bulk
    user_id = get_jwt_identity()['user_id']

    for file in files:
        if file.filename == '':
            continue
        if file and file.filename.endswith('.pdf') and file.content_length <= app.config['MAX_CONTENT_LENGTH']:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            conn = sqlite3.connect('studymate.db')
            c = conn.cursor()
            c.execute("INSERT INTO uploads (filename, user_id, upload_time) VALUES (?, ?, ?)", 
                      (filename, user_id, get_ist_time()))
            conn.commit()
            conn.close()
        else:
            return jsonify({'error': 'Only PDFs up to 10MB are supported'}), 400

    return jsonify({'message': 'Files uploaded successfully', 'filename': [f.filename for f in files if f.filename]}), 200

# Ask endpoint
@app.route('/api/ask', methods=['POST'])
@jwt_required()
def ask_question():
    data = request.get_json()
    question = data.get('question')
    filename = data.get('filename')

    if not question:
        return jsonify({'error': 'Question is required'}), 400

    # Simulate AI response (replace with actual model integration)
    response = f"Simulated answer to '{question}' based on {filename or 'no document'} at {get_ist_time()} IST."
    return jsonify({'answer': response}), 200

# Serve static files
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if not path or path == 'index.html':
        return send_from_directory('static', 'index.html')
    return send_from_directory('static', path)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```

