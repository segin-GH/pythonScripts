from http.server import HTTPServer, BaseHTTPRequestHandler

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Set the response code to 200 (OK)
        self.send_response(200)
        
        # Set the content type to HTML
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        # Open the index.html file and read its contents
        with open('index.html', 'r') as f:
            index_html = f.read()
        
        # Write the contents of the index.html file to the response
        self.wfile.write(index_html.encode())

httpd = HTTPServer(('localhost', 8080), RequestHandler)
httpd.serve_forever()
