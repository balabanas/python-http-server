import datetime
import os
import socket
import logging
import urllib

import select
import selectors

HOST = 'localhost'
PORT = 8081
DOCUMENT_ROOT = 'html'
SERVER_NAME = 'ServerName'


tasks = []
to_read = {}
to_write = {}


def get_index(path: str) -> (bytes, bytes):
    server_name = f"\r\nServer: {SERVER_NAME}"
    date = f"\r\nDate: {datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')}"
    if path.split('/')[-1]:  # file requested
        return get_file(f"{path}")
    elif os.path.exists(f"{DOCUMENT_ROOT}{path}index.html"):  # dir requested, and index.html exists
        return get_file(f"{path}index.html")
    else:  # dir requested, but no index.html there
        return f"HTTP/1.0 404 Not Found\r\nContent-Length:0{server_name}{date}\r\n\r\n".encode('utf-8'), b''

    # try:
    #     items = os.listdir(f"{DOCUMENT_ROOT}{path}")
    # except (FileNotFoundError, NotADirectoryError):
    #     return "HTTP/1.0 404 Not Found\r\nContent-Length:0\r\n\r\n".encode('utf-8'), b''
    # response = f"<h1>Index of {path}</h1>"
    # response += "<ul>"
    # for item in items:
    #     response += f"<li>{item}</li>"
    # response += "</ul>"
    # logging.info(items)
    # body = response
    # body = f"<html><head></head><body>{body}</body></html>"
    # body_len = len(body)
    # return f"HTTP/1.0 200 OK\r\nContent-Type: text/html\r\nContent-Length: {body_len}\r\n\r\n".encode('utf-8'), body.encode('utf-8')


class ContentTypeProcessor:
    def __init__(self, path='', read_mode='r'):
        self.path = path
        self.read_mode = read_mode

    def read(self):
        server_name = f"\r\nServer: {SERVER_NAME}"
        date = f"\r\nDate: {datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')}"
        try:
            with open(self.path, 'rb') as f:
                content = f.read()
        except (FileNotFoundError, PermissionError):
            return f"HTTP/1.0 404 Not Found\r\nContent-Length:0{server_name}{date}\r\n\r\n".encode('utf-8'), b''
        content_type = self.get_content_type()
        content_len = len(content)
        headers = f"HTTP/1.0 200 OK\r\nContent-Type: {content_type}\r\nConnection: close\r\nContent-Length: {content_len}{server_name}{date}\r\n\r\n".encode('utf-8')

        return headers, content

    def get_content_type(self):
        pass


class ContentTypeProcessorCSS(ContentTypeProcessor):
    def get_content_type(self):
        return 'text/css'


class ContentTypeProcessorHTML(ContentTypeProcessor):
    def get_content_type(self):
        return 'text/html'


class ContentTypeProcessorPlainText(ContentTypeProcessor):
    def get_content_type(self):
        return 'text/plain'


class ContentTypeProcessorGIF(ContentTypeProcessor):
    def get_content_type(self):
        return 'image/gif'


class ContentTypeProcessorJPEG(ContentTypeProcessor):
    def get_content_type(self):
        return 'image/jpeg'

class ContentTypeProcessorJS(ContentTypeProcessor):
    def get_content_type(self):
        return 'text/javascript'

class ContentTypeProcessorPNG(ContentTypeProcessor):
    def get_content_type(self):
        return 'image/png'

class ContentTypeProcessorSWF(ContentTypeProcessor):
    def get_content_type(self):
        return 'application/x-shockwave-flash'


class ContentTypeFactory:
    @staticmethod
    def get_content_type_processor(path: str, ext: str) -> ContentTypeProcessor:
        if ext == '.css':
            return ContentTypeProcessorCSS(path, 'r')
        elif ext == '.html':
            return ContentTypeProcessorHTML(path, 'r')
        elif ext == '.gif':
            return ContentTypeProcessorGIF(path, 'rb')
        elif ext in ['.jpeg', '.jpg']:
            return ContentTypeProcessorJPEG(path, 'rb')
        elif ext == '.png':
            return ContentTypeProcessorPNG(path, 'rb')
        elif ext == '.swf':
            return ContentTypeProcessorSWF(path, 'rb')
        elif ext == '.js':
            return ContentTypeProcessorJS(path, 'r')
        else:
            return ContentTypeProcessorPlainText(path, 'r')


def get_file(path: str) -> bytes:
    full_path = f'{DOCUMENT_ROOT}{path}'
    _, file_extension = os.path.splitext(full_path)
    proc = ContentTypeFactory.get_content_type_processor(full_path, file_extension)
    # try:
    #     with open(f'{DOCUMENT_ROOT}{path}', 'r') as fin:
    #         content = fin.read()
    #         _, file_extension = os.path.splitext(f'{DOCUMENT_ROOT}{path}')
    #         proc = ContentTypeFactory.get_content_type_processor(file_extension)
    #         content_type = proc.get_content_type()
    #     content_len = len(content)
    #     response = f"HTTP/1.0 200 OK\r\nContent-Type: {content_type}\r\nConnection: close\r\nContent-Length: {content_len}\r\n\r\n{content}".encode('utf-8')
    # except (FileNotFoundError, PermissionError):
    #     response = "HTTP/1.0 404 Not Found\r\nContent-Length:0\r\n\r\n".encode('utf-8')
    return proc.read()

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

        if not client_socket._closed:
            yield ('read', client_socket)
            try:
                request = client_socket.recv(28096)  # read
                logging.info(f"Request: {request}")
            except ConnectionResetError:
                break

        else:
            break

        if not request:
            break
        else:
            request = request.decode('utf-8')
            request_lines = request.splitlines()
            try:
                method, path, protocol = request_lines[0].split()
            except ValueError:  # bad request, not implemented
                break

            path = urllib.parse.urlparse(path)
            path = urllib.parse.unquote(path.path)

            yield ('write', client_socket)
            if method in ['GET', 'HEAD']:
                headers: bytes
                body: bytes

                headers, body = get_index(path)
                if method == 'GET':
                    response = headers + body
                else:
                    response = headers


                #TODO: 403, 404
            else:
                server_name = f"\r\nServer: {SERVER_NAME}"
                date = f"\r\nDate: {datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')}"
                response = f"HTTP/1.0 405 Method Not Allowed\r\nContent-Length: 13\r\nAllow: GET, HEAD{server_name}{date}\r\n\r\nNot implemented".encode('utf-8')
            try:
                print(response)
                client_socket.sendall(response)
                logging.info(f"Sent response: {response}")
                # yield ('close', client_socket)
                client_socket.shutdown(socket.SHUT_WR)
                client_socket.close()
            except ConnectionResetError:
                pass

            # client_socket.shutdown(socket.SHUT_WR)
            # client_socket.close()
            # logging.info(f"Connection closed: {client_socket}")
    # logging.info(f"Closing connection: {client_socket}")
    # client_socket.shutdown(socket.SHUT_WR)
    # client_socket.close()


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
            # elif reason == 'close':
            #     to_write.pop(sock)

        except StopIteration:
            logging.info('Done!')


if __name__ == "__main__":
    log_format: str = '%(asctime)s %(levelname).1s %(message)s'
    logging.basicConfig(format=log_format, filename='', level='INFO',
                        datefmt='%Y-%m-%d %H:%M:%S')
    tasks.append(server())
    event_loop()
