import argparse
import datetime
import logging
import multiprocessing
import os
import random
import socket
import urllib

import select

HOST = 'localhost'
PORT = 8081
SERVER_NAME = 'ServerName'

# tasks = []
# to_read = {}
# to_write = {}


class Response:
    """"Keeps response elements and packs them to a complete response before sending back to a client"""
    status = "HTTP/1.0 405 Method Not Allowed"
    headers = {
        'Server': SERVER_NAME,
        'Connection': 'close',
        'Content-Length': 0,
    }
    body = b''

    def __init__(self):
        self.headers['Data'] = datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')

    def pack_response(self):
        headers = '\r\n'.join([f'{k}: {v}' for k, v in self.headers.items()])
        header = f"{self.status}\r\n{headers}\r\n\r\n"
        header = header.encode('utf-8')
        return header + self.body


class GETHEADHTTPWorker:
    def __init__(self, pn, queue, droot, log_level):
        self.logger = logging.getLogger(f'worker{pn}')
        self.logger.setLevel(log_level)
        handler = logging.StreamHandler()
        handler.setLevel(log_level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.info(f"Worker {pn} created")
        self.pn = pn
        self.tasks = []
        self.queue = queue
        self.abs_root = os.path.abspath(droot)
        self.event_loop(self.pn, self.tasks, self.queue)

    def event_loop(self, pn, tasks, queue):
        to_read = {}
        to_write = {}
        # while any([tasks, to_read, to_write]):
        while 1:
            try:
                new_connection = queue.get_nowait()
                to_read[new_connection] = self.client(new_connection)
            except:
                pass
            if any([tasks, to_read, to_write]):
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
                    pass
                    # logging.info('Done!')

    def get_url(self, path: str) -> (str, dict, bytes):
        """Returns response components with body content from files if path is valid, or error status, if not"""
        path = urllib.parse.urlparse(path)
        path = urllib.parse.unquote(path.path)
        request_abs_path = os.path.abspath(os.path.join(self.abs_root, path.lstrip('/')))
        self.logger.debug(request_abs_path)
        if not request_abs_path.startswith(self.abs_root):
            return "HTTP/1.0 403 Forbidden", {}, b''
        if path.split('/')[-1]:  # file requested
            _, file_extension = os.path.splitext(request_abs_path)
            proc = ContentTypeFactory.get_content_type_processor(request_abs_path, file_extension)
            return proc.read()
        elif os.path.exists(os.path.join(request_abs_path, 'index.html')):  # dir requested, and index.html exists
            proc = ContentTypeFactory.get_content_type_processor(os.path.join(request_abs_path, 'index.html'), '.html')
            return proc.read()
        return "HTTP/1.0 404 Not Found", {}, b''

    def client(self, client_socket):
        while 1:
            if not client_socket._closed:
                yield ('read', client_socket)
                try:
                    request = client_socket.recv(28096)  # read
                    # logging.info(f"Request: {request}")
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
                response = Response()

                yield ('write', client_socket)
                if method in ['GET', 'HEAD']:
                    headers: bytes
                    body: bytes
                    status, headers, body = self.get_url(path)
                    response.status = status
                    response.headers.update(headers)
                    if method == 'GET':
                        response.body = body
                else:
                    response.headers['Allow'] = "GET, HEAD"

                try:
                    client_socket.sendall(response.pack_response())
                    logging.info(f"Sent response: {response.pack_response()}")
                    client_socket.shutdown(socket.SHUT_WR)
                    client_socket.close()
                except ConnectionResetError:
                    pass

        # logging.info(f"Closing connection: {client_socket}")
        # client_socket.shutdown(socket.SHUT_WR)
        # client_socket.close()



class ContentTypeProcessor:
    def __init__(self, path='', read_mode='r'):
        self.path = path
        self.read_mode = read_mode

    def read(self) -> (str, dict, bytes):
        try:
            with open(self.path, 'rb') as f:
                content = f.read()
        except (FileNotFoundError, PermissionError):
            headers = {'Content-Length': 0}
            return "HTTP/1.0 404 Not Found", headers, b''
        content_type = self.get_content_type()
        content_len = len(content)
        headers = {
            'Content-Length': content_len,
            'Content-Type': content_type
        }
        return "HTTP/1.0 200 OK", headers, content

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


def main(i, queue, document_root, log_level):
    GETHEADHTTPWorker(i, queue, document_root, log_level)


if __name__ == "__main__":
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    parser.add_argument('-w', default=2, nargs='?', help='Number of workers')
    parser.add_argument('-r', default='html', nargs='?', help='Path to DOCUMENT_ROOT, relative to httpd.py')
    parser.add_argument('--log_level', type=str, default='INFO', nargs='?', help='Log level')
    args: argparse.Namespace = parser.parse_args()
    log_level = getattr(logging, args.log_level.upper(), None)
    if not isinstance(log_level, int):
        raise ValueError(f"Invalid log level: {args.log_level}")
    # log_format: str = '%(asctime)s %(levelname).1s %(message)s'
    logging.basicConfig(filename='', datefmt='%Y-%m-%d %H:%M:%S', level=log_level)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    logging.info('Server started')

    processes = []
    queues = []
    for i in range(args.w):
        queue = multiprocessing.Queue()
        process = multiprocessing.Process(target=main, args=(i, queue, args.r, log_level))
        process.start()
        processes.append(process)
        queues.append(queue)

    while 1:
        try:
            client_socket, addr = server_socket.accept()  # read
            logging.info(f"Connection from {addr}.")
            queues[random.randint(0, args.w-1)].put(client_socket)
        except KeyboardInterrupt:
            break

    for process in processes:
        process.join()