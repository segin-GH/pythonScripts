#! /usr/bin/python3
import os
import sys
import http.server
import socketserver

# Constants for configuration
PORT = 8000
DEFAULT_FILE = '/index.html'  # Default file to serve

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Handler to serve a specific default file for the root URL."""
    
    def do_GET(self):
        if self.path == '/':
            self.path = DEFAULT_FILE
        return super().do_GET()

def start_server(website_directory):
    """Start the HTTP server."""
    os.chdir(website_directory)  # Change to the directory containing your web application
    
    httpd = socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler, bind_and_activate=False)
    httpd.allow_reuse_address = True  # Allow the reuse of the socket address
    httpd.server_bind()
    httpd.server_activate()
    
    with httpd:
        print(f"Serving at port {PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down the server...")
            httpd.shutdown()
            print("Server shut down successfully.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please provide the directory name containing the website files as an argument.")
        sys.exit(1)

    website_directory = sys.argv[1]
    start_server(website_directory)
