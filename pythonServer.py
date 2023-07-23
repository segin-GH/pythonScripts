#! /usr/bin/python3

import os
import sys
import http.server
import socketserver

# Constants for configuration
PORT = 8000
DEFAULT_FILE = "/index.html"  # Default file to serve


class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Handler to serve a specific default file for the root URL."""

    def do_GET(self):
        if self.path == "/":
            self.path = DEFAULT_FILE
        return super().do_GET()

    def do_post(self):
        pass


def start_server(website_directory):
    """Start the HTTP server."""
    os.chdir(website_directory)  # Change to the directory containing your web application
    with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
        print(f"Serving at port {PORT}")
        httpd.serve_forever()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please provide the directory name containing the website files as an argument.")
        sys.exit(1)

    website_directory = sys.argv[1]
    start_server(website_directory)
