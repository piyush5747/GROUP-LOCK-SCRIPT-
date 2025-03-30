from flask import Flask, request, jsonify, render_template_string
import sqlite3
import hashlib

app = Flask(__name__)

# Database Setup
def init_db():
    conn = sqlite3.connect('groups.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS locked_groups (
            group_uid TEXT PRIMARY KEY,
            admin_uid TEXT NOT NULL,
            admin_token TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Function to hash token (for security)
def hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()

@app.route('/', methods=['GET'])
def index():
    return render_template_string('''
        <html>
            <head>
                <title>Group Lock System</title>
                <style>
                    body { background: linear-gradient(45deg, #ff6b6b, #f7a6b1); color: white; font-family: Arial, sans-serif; text-align: center; padding: 20px; }
                    input, button, select { margin: 10px; padding: 10px; font-size: 16px; border: none; border-radius: 5px; }
                    button { cursor: pointer; background: #333; color: white; }
                </style>
            </head>
            <body>
                <h1>Group Lock System</h1>
                <form action="/lock" method="POST">
                    <input type="text" name="admin_uid" placeholder="Admin UID" required><br>
                    <input type="password" name="admin_token" placeholder="Admin Token" required><br>
                    <input type="text" name="group_uid" placeholder="Group UID" required><br>
                    <button type="submit">Lock Group</button>
                </form>
                <form action="/unlock" method="POST">
                    <input type="text" name="admin_uid" placeholder="Admin UID" required><br>
                    <input type="password" name="admin_token" placeholder="Admin Token" required><br>
                    <input type="text" name="group_uid" placeholder="Group UID" required><br>
                    <button type="submit">Unlock Group</button>
                </form>
            </body>
        </html>
    ''')

@app.route('/lock', methods=['POST'])
def lock_group():
    admin_uid = request.form.get('admin_uid')
    admin_token = hash_token(request.form.get('admin_token'))
    group_uid = request.form.get('group_uid')

    conn = sqlite3.connect('groups.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM locked_groups WHERE group_uid = ?', (group_uid,))
    if cursor.fetchone():
        conn.close()
        return jsonify({"status": "error", "message": "Group already locked."})

    cursor.execute('INSERT INTO locked_groups (group_uid, admin_uid, admin_token) VALUES (?, ?, ?)',
                   (group_uid, admin_uid, admin_token))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": f"Group {group_uid} locked successfully."})

@app.route('/unlock', methods=['POST'])
def unlock_group():
    admin_uid = request.form.get('admin_uid')
    admin_token = hash_token(request.form.get('admin_token'))
    group_uid = request.form.get('group_uid')

    conn = sqlite3.connect('groups.db')
    cursor = conn.cursor()

    cursor.execute('SELECT admin_token FROM locked_groups WHERE group_uid = ?', (group_uid,))
    result = cursor.fetchone()

    if not result:
        conn.close()
        return jsonify({"status": "error", "message": "Group is not locked."})

    stored_token = result[0]

    if stored_token == admin_token:
        cursor.execute('DELETE FROM locked_groups WHERE group_uid = ?', (group_uid,))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": f"Group {group_uid} unlocked successfully."})
    else:
        conn.close()
        return jsonify({"status": "error", "message": "Unauthorized: Invalid token or UID."})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)