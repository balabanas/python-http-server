"""
 Implements a simple HTTP/1.0 Server

"""

import socket


# Define socket host and port
SERVER_HOST = 'localhost'
SERVER_PORT = 8081

# Create socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((SERVER_HOST, SERVER_PORT))
server_socket.listen(1)
print('Listening on port %s ...' % SERVER_PORT)

while 1:
    # Wait for client connections
    client_connection, client_address = server_socket.accept()

    # Get the client request
    try:
        request = client_connection.recv(1024).decode()
    except ConnectionResetError:
        pass
    print(request)

    # Send HTTP response
    response = 'HTTP/1.0 200 OK\n\nHello World'
    try:
        client_connection.sendall(response.encode())
    except ConnectionResetError:
        pass
    client_connection.close()

# Close socket
server_socket.close()
