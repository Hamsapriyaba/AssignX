import http.server
import socketserver
import webbrowser
import os
import sqlite3
import json

PORT = 8000
DB_FILE = "users.db"

# Initialize Database
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# Open index.html automatically
def open_browser():
    webbrowser.open(f"http://127.0.0.1:{PORT}/index.html")

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        user = json.loads(post_data.decode('utf-8'))
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        response = {"success": False, "message": "Unknown action"}
        
        if user["action"] == "signup":
            try:
                cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (user["username"], user["password"]))
                conn.commit()
                response = {"success": True, "message": "Signup successful"}
            except sqlite3.IntegrityError:
                response = {"success": False, "message": "User already exists"}
        
        elif user["action"] == "login":
            cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (user["username"], user["password"]))
            if cursor.fetchone():
                response = {"success": True, "message": "Login successful"}
            else:
                response = {"success": False, "message": "Invalid credentials"}
        
        conn.close()
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))

# Start server
if __name__ == "__main__":
    init_db()
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serving at http://127.0.0.1:{PORT}")
        open_browser()
        httpd.serve_forever()
