import socket
import logging
import select
import selectors

HOST = 'localhost'
PORT = 8081

# selector = selectors.DefaultSelector()


response ="""HTTP/1.0 200 OK
Date: Thu, 26 Apr 2007 19:54:01 GMT
Server: Apache/2.0.54 (Debian GNU/Linux) DAV/2 SVN/1.1.4 mod_python/3.1.3 Last-Modified: Thu, 26 Apr 2007 18:40:24 GMT
Accept-Ranges: bytes
Content-Length: 5
Connection: close
Content-Type: text/html
<HTML>
</HTML>
\r\n\r\n
""".encode('utf-8')

tasks = []
to_read = {}
to_write = {}


def server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    logging.info('Server started')
    while 1:
        yield ('read', server_socket)
        client_socket, addr = server_socket.accept()  # read
        logging.info(f"Connection from {addr}")
        tasks.append(client(client_socket))


def client(client_socket):
    while 1:
        yield ('read', client_socket)
        request = client_socket.recv(4096)  # read

        if not request:
            break
        else:
            # response = 'Hello world'.encode('utf-8')
            yield ('write', client_socket)
            client_socket.send(response)
    client_socket.close()


def event_loop():
    while any([tasks, to_read, to_write]):
        while not tasks:
            ready_to_read, ready_to_write, _ = select.select(to_read, to_write, [])
            for sock in ready_to_read:
                tasks.append(to_read.pop(sock))
            for sock in ready_to_write:
                tasks.append(to_write.pop(sock))
        try:
            task = tasks.pop(0)
            reason, sock = next(task)
            if reason == 'read':
                to_read[sock] = task
            if reason == 'write':
                to_write[sock] = task
        except StopIteration:
            logging.info('Done!')

if __name__ == "__main__":
    log_format: str = '%(asctime)s %(levelname).1s %(message)s'
    logging.basicConfig(format=log_format, filename='', level='INFO',
                        datefmt='%Y-%m-%d %H:%M:%S')
    tasks.append(server())
    event_loop()
