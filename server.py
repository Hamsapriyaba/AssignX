import http.server
import socketserver
import os
import csv
import zipfile  # For DOCX files
import re  # For PDF files

PORT = 8080  # Changed to 8080

class FileSearchHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open('index.html', 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_error(404, "File Not Found")

    def do_POST(self):
        if self.path == '/search':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            # Parse the multipart form data manually
            boundary = self.headers['Content-Type'].split('boundary=')[1]
            parts = post_data.split(b'--' + boundary.encode())

            file_data = None
            search_term = None

            for part in parts:
                if b'name="file"' in part:
                    file_data = part.split(b'\r\n\r\n')[1].rstrip(b'\r\n')
                elif b'name="search"' in part:
                    search_term = part.split(b'\r\n\r\n')[1].decode().strip()

            if not file_data or not search_term:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'Missing file or search term.')
                return

            # Save the uploaded file temporarily
            file_path = os.path.join('/tmp', 'uploaded_file')
            with open(file_path, 'wb') as f:
                f.write(file_data)

            # Search in the file
            result = self.search_in_file(file_path, search_term)
            os.remove(file_path)

            # Send the result back to the client
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(result.encode())

    def search_in_file(self, file_path, search_term):
        if file_path.endswith('.csv'):
            return self.search_in_csv(file_path, search_term)
        elif file_path.endswith('.pdf'):
            return self.search_in_pdf(file_path, search_term)
        elif file_path.endswith('.docx'):
            return self.search_in_docx(file_path, search_term)
        else:
            return 'Unsupported file type.'

    def search_in_csv(self, file_path, search_term):
        result = []
        with open(file_path, newline='') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if any(search_term.lower() in cell.lower() for cell in row):
                    result.append(', '.join(row))
        return '<br>'.join(result) if result else 'No match found.'

    def search_in_pdf(self, file_path, search_term):
        result = []
        with open(file_path, 'rb') as pdf_file:
            # Basic PDF text extraction using regex
            pdf_content = pdf_file.read()
            text = self.extract_text_from_pdf(pdf_content)
            if search_term.lower() in text.lower():
                result.append(text)
        return '<br>'.join(result) if result else 'No match found.'

    def extract_text_from_pdf(self, pdf_content):
        # Simple regex-based text extraction (not perfect but works for basic PDFs)
        text = re.sub(rb'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', b' ', pdf_content)  # Remove non-printable characters
        text = text.decode('latin-1', errors='ignore')  # Decode bytes to string
        return text

    def search_in_docx(self, file_path, search_term):
        result = []
        # DOCX files are ZIP archives containing XML files
        with zipfile.ZipFile(file_path) as docx_file:
            # Extract the main document content
            if 'word/document.xml' in docx_file.namelist():
                with docx_file.open('word/document.xml') as xml_file:
                    xml_content = xml_file.read()
                    text = self.extract_text_from_docx(xml_content)
                    if search_term.lower() in text.lower():
                        result.append(text)
        return '<br>'.join(result) if result else 'No match found.'

    def extract_text_from_docx(self, xml_content):
        # Simple XML parsing to extract text
        text = re.sub(r'<[^>]+>', ' ', xml_content.decode('utf-8'))  # Remove XML tags
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        return text.strip()

with socketserver.TCPServer(("localhost", PORT), FileSearchHandler) as httpd:

    print(f"Serving at port {PORT}")
    httpd.serve_forever()