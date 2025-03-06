import http.server
import socketserver
import webbrowser
import sqlite3
import json

PORT = 8000
DB_FILE = "users.db"

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

def open_browser():
    webbrowser.open(f"http://127.0.0.1:{PORT}/index.html")

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        response = {"success": False, "message": "Unknown action"}

        if self.path == "/signup":
            try:
                cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (data["username"], data["password"]))
                conn.commit()
                response = {"success": True, "message": "User registered successfully"}
            except sqlite3.IntegrityError:
                response = {"success": False, "message": "Username already exists"}

        elif self.path == "/login":
            cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (data["username"], data["password"]))
            user = cursor.fetchone()
            if user:
                response = {"success": True, "message": "Login successful"}
            else:
                response = {"success": False, "message": "Invalid username or password"}

        conn.close()

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))

if __name__ == "__main__":
    init_db()
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serving at http://127.0.0.1:{PORT}")
        open_browser()
        httpd.serve_forever()
