import socket
import logging
import select
import selectors

HOST = 'localhost'
PORT = 8081

selector = selectors.DefaultSelector()


response ="""HTTP/1.0 200 OK
Date: Thu, 26 Apr 2007 19:54:01 GMT
Server: Apache/2.0.54 (Debian GNU/Linux) DAV/2 SVN/1.1.4 mod_python/3.1.3 Last-Modified: Thu, 26 Apr 2007 18:40:24 GMT
Accept-Ranges: bytes
Content-Length: 5
Connection: close
Content-Type: text/html
<HTML>
</HTML>
"""

def server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,
                 1)  # socket option level, socket option, reuse address after close
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    logging.info('Server started')
    # server_file = server_socket.makefile('rw')
    selector.register(fileobj=server_socket, events=selectors.EVENT_READ, data=accept_connections)


def send_message(client_socket):
    request = client_socket.recv(1024)
    # request = client_file.readline()
    if request:
        logging.info(f"Got request: {request.decode('utf-8')}")
        data = f"{response}\r\n".encode('utf-8')
        client_socket.send(data)
        # client_file.write(data)
        # client_file.flush()
        logging.info(f"Sent to {client_socket.getpeername()}, data: {data}")
    else:
        selector.unregister(client_socket)
        client_socket.close()


def accept_connections(server_socket):
    client_socket, a = server_socket.accept()
    # client_file = client_socket.makefile('rw')
    logging.info(f'Received connection from {a}')
    selector.register(fileobj=client_socket, events=selectors.EVENT_READ, data=send_message)


def event_loop():
    while 1:
        events = selector.select()
        for key, _ in events:
            callback = key.data
            callback(key.fileobj)


if __name__ == "__main__":
    log_format: str = '%(asctime)s %(levelname).1s %(message)s'
    logging.basicConfig(format=log_format, filename='', level='INFO',
                        datefmt='%Y-%m-%d %H:%M:%S')
    server()
    event_loop()
