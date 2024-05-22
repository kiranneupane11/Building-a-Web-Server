import io
import socket
import sys


class WSGIServer(object):
    address_family = socket.AF_INET
    socket_type = socket.SOCK_STREAM
    request_queue_size = 1

    def __init__(self, server_address):
        # Create a listening socket
        # HINT: Use socket.socket to create a socket and set socket options
        # HINT: Bind the socket to the server_address and start listening
        self.listen_socket = listen_socket = socket.socket(self.address_family,self.socket_type)
        # Allow to reuse the same address
        listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind
        listen_socket.bind(server_address)
        # Activate
        listen_socket.listen(self.request_queue_size)
        # Get server host name and port
        host, port = self.listen_socket.getsockname()[:2]
        self.server_name = socket.getfqdn(host)
        self.server_port = port
        # Return headers set by Web framework/Web application
        self.headers_set = []
        pass

    def set_app(self, application):
        # HINT: Store the application callable
        self.application = application
        pass

    def serve_forever(self):
        # HINT: Enter an infinite loop to wait for client connections
        listen_socket=self.listen_socket
        while True:
            # HINT: Accept a new client connection
            self.client_connection, client_address =listen_socket.accept()
            # Handle one request and close the client connection. Then
            # loop over to wait for another client connection
            self.handle_one_request()
            pass

    def handle_one_request(self):
        # HINT: Receive request data from the client connection
        self.request_data = request_data =self.client_connection.recv(1024)
        # HINT: Decode the request data and print it for debugging
        self.request_data = request_data = request_data.decode('utf-8')
        print(''.join(
            f'< {line}\n' for line in request_data.splitlines()
        ))
        # HINT: Parse the request data and construct the WSGI environment
        self.parse_request(request_data)
        env = self.get_environ()
        # HINT: Call the application with the environment and start_response
        result = self.application(env, self.start_response)
        # HINT: Send the constructed response back to the client
        self.finish_response(result)
        pass

    def parse_request(self, text):
        # HINT: Split the request line into method, path, and version
        request_line = text.splitlines()[0]
        request_line = request_line.rstrip('\r\n')
        # Break down the request line into components
        (self.request_method,  # GET
         self.path,            # /hello
         self.request_version  # HTTP/1.1
         ) = request_line.split()
        pass

    def get_environ(self):
        env = {}
        # HINT: Populate the WSGI environment with required WSGI variables
        env['wsgi.version']      = (1, 0)
        env['wsgi.url_scheme']   = 'http'
        env['wsgi.input']        = io.StringIO(self.request_data)
        env['wsgi.errors']       = sys.stderr
        env['wsgi.multithread']  = False
        env['wsgi.multiprocess'] = False
        env['wsgi.run_once']     = False
        # Required CGI variables
        env['REQUEST_METHOD']    = self.request_method    # GET
        env['PATH_INFO']         = self.path              # /hello
        env['SERVER_NAME']       = self.server_name       # localhost
        env['SERVER_PORT']       = str(self.server_port)  # 8888
        return env

    def start_response(self, status, response_headers, exc_info=None):
        # HINT: Set the status and headers for the HTTP response
        server_headers = [
            ('Date', 'Tue, 21 May 2024 12:35:55 GMT'),
            ('Server', 'WSGIServer 0.2'),
        ]
        self.headers_set = [status, response_headers + server_headers]
        pass

    def finish_response(self, result):
        # HINT: Construct the HTTP response from status, headers, and body
        try:
            status, response_headers = self.headers_set
            response = f'HTTP/1.1 {status}\r\n'
            for header in response_headers:
                response += '{0}: {1}\r\n'.format(*header)
            response += '\r\n'
            for data in result:
                response += data.decode('utf-8')
            # Print formatted response data a la 'curl -v'
            print(''.join(
                f'> {line}\n' for line in response.splitlines()
            ))
            response_bytes = response.encode()
            self.client_connection.sendall(response_bytes)
        finally:
            self.client_connection.close()


SERVER_ADDRESS = (HOST, PORT) = '', 8888


def make_server(server_address, application):
    # HINT: Create an instance of WSGIServer and set the application
    server = WSGIServer(server_address)
    server.set_app(application)
    return server


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit('Provide a WSGI application object as module:callable')
    app_path = sys.argv[1]
    module, application = app_path.split(':')
    module = __import__(module)
    application = getattr(module, application)
    # HINT: Use make_server to create the server and start serving
    httpd=make_server(SERVER_ADDRESS, application)
    print(f'WSGIServer: Serving HTTP on port {PORT} ...\n')
    httpd.serve_forever()
    pass
