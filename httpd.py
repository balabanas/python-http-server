import socket
import logging
import select
import selectors

# import ssl

HOST = 'localhost'
PORT = 8081

selector = selectors.DefaultSelector()

to_monitor = []

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


def send_message(client_socket):
    request = client_socket.recv(1024)

    if request:
        logging.info(f"Got request: {request.decode('utf-8')}")
        data = f"{response}\r\n".encode('utf-8')
        client_socket.send(data)
        logging.info(f"Sent to {client_socket.getpeername()}, data: {data}")
    else:
        client_socket.close()


def accept_connections(server_socket):
    client_socket, a = server_socket.accept()
    logging.info(f'Received connection from {a}')
    to_monitor.append(client_socket)


def event_loop(server_socket):
    while 1:
        ready_to_read, _, _ = select.select(to_monitor, [], [])
        for sock in ready_to_read:
            if sock is server_socket:
                accept_connections(sock)
            else:
                send_message(sock)


if __name__ == "__main__":
    log_format: str = '%(asctime)s %(levelname).1s %(message)s'
    logging.basicConfig(format=log_format, filename='', level='INFO',
                        datefmt='%Y-%m-%d %H:%M:%S')
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,
                 1)  # socket option level, socket option, reuse address after close
    s.bind((HOST, PORT))
    s.listen(5)
    logging.info('Server started')
    to_monitor.append(s)
    event_loop(s)
