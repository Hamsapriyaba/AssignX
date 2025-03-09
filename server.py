import http.server
import socketserver
import webbrowser
import sqlite3
import json
import os
import urllib
import csv

PORT = 8000
DB_FILE = "database.db"
UPLOAD_FOLDER = "uploads"

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize Database
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_name TEXT NOT NULL,
            assignee TEXT NOT NULL,
            due_date TEXT NOT NULL,
            priority TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# Open Browser Automatically
def open_browser():
    webbrowser.open(f"http://127.0.0.1:{PORT}/index.html")

# Request Handler Class
class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        response = {"success": False, "message": "Unknown action"}

        if self.path == "/add_link":
            try:
                cursor.execute("INSERT INTO links (title, url) VALUES (?, ?)", (data["title"], data["url"]))
                conn.commit()
                response = {"success": True, "message": "Link added successfully"}
            except Exception as e:
                response = {"success": False, "message": str(e)}
        
        elif self.path == "/delete_link":
            try:
                cursor.execute("DELETE FROM links WHERE id = ?", (data["id"],))
                conn.commit()
                response = {"success": True, "message": "Link deleted successfully"}
            except Exception as e:
                response = {"success": False, "message": str(e)}
        
        elif self.path == "/add_task":
            try:
                cursor.execute("""
                    INSERT INTO tasks (task_name, assignee, due_date, priority, status)
                    VALUES (?, ?, ?, ?, ?)
                """, (data["task_name"], data["assignee"], data["due_date"], data["priority"], data["status"]))
                conn.commit()
                response = {"success": True, "message": "Task added successfully"}
            except Exception as e:
                response = {"success": False, "message": str(e)}
        
        elif self.path == "/delete_task":
            try:
                cursor.execute("DELETE FROM tasks WHERE id = ?", (data["id"],))
                conn.commit()
                response = {"success": True, "message": "Task deleted successfully"}
            except Exception as e:
                response = {"success": False, "message": str(e)}
        
        elif self.path == "/upload":
            try:
                filename = self.parse_filename(post_data)
                if filename.endswith('.csv'):
                    with open(os.path.join(UPLOAD_FOLDER, filename), 'wb') as f:
                        f.write(post_data)
                    response = {"success": True, "message": "File uploaded successfully!"}
                else:
                    response = {"success": False, "message": "Only CSV files are allowed."}
            except Exception as e:
                response = {"success": False, "message": str(e)}
        
        conn.close()
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))

    def do_GET(self):
        if self.path == "/get_links":
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, url FROM links")
            links = [{"id": row[0], "title": row[1], "url": row[2]} for row in cursor.fetchall()]
            conn.close()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(links).encode('utf-8'))
        
        elif self.path == "/get_tasks":
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT id, task_name, assignee, due_date, priority, status FROM tasks")
            tasks = [{
                "id": row[0],
                "task_name": row[1],
                "assignee": row[2],
                "due_date": row[3],
                "priority": row[4],
                "status": row[5]
            } for row in cursor.fetchall()]
            conn.close()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(tasks).encode('utf-8'))
        
        elif self.path.startswith("/search"):
            query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get('query', [None])[0]
            if query:
                query = query.lower()
                results = []
                for filename in os.listdir(UPLOAD_FOLDER):
                    if filename.endswith('.csv'):
                        with open(os.path.join(UPLOAD_FOLDER, filename), newline='', encoding='utf-8') as f:
                            reader = csv.reader(f)
                            for row in reader:
                                if any(query in cell.lower() for cell in row):
                                    results.append(row)  # Return the entire row
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(results if results else ["No results found."]).encode('utf-8'))
            else:
                self.send_response(400)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'Error: No search query provided.')
        
        else:
            super().do_GET()

    def parse_filename(self, body):
        # Extract the filename from the request body
        content_type = self.headers['Content-Type']
        if not content_type or 'boundary=' not in content_type:
            raise ValueError("Invalid Content-Type header")

        boundary = content_type.split('boundary=')[1].encode('utf-8')
        boundary = b'--' + boundary

        filename_start = body.find(b'filename="') + len(b'filename="')
        filename_end = body.find(b'"', filename_start)
        if filename_start == -1 or filename_end == -1:
            raise ValueError("Filename not found in request body")

        filename = body[filename_start:filename_end].decode('utf-8')
        return filename

if __name__ == "__main__":
    init_db()
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serving at http://127.0.0.1:{PORT}")
        open_browser()
        httpd.serve_forever()
