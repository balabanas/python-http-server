import argparse
import datetime
import logging
import multiprocessing
import os
import random
import socket
import time
import urllib

import select

HOST = 'localhost'
PORT = 8081
SERVER_NAME = 'ServerName'


class Response:
    """"Keeps response elements and packs them to a complete response before sending back to a client"""
    def __init__(self):
        self.status = "HTTP/1.0 400 Bad Request"
        self.headers = {
            'Server': SERVER_NAME,
            'Connection': 'close',
            'Content-Length': 0,
        }
        self.body = b''
        self.headers['Data'] = datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')

    def pack_response(self):
        headers = '\r\n'.join([f'{k}: {v}' for k, v in self.headers.items()])
        header = f"{self.status}\r\n{headers}\r\n\r\n"
        header = header.encode('utf-8')
        return header + self.body


class GETHEADHTTPWorker:
    # def __init__(self, pn, queue, droot, log_level, server_socket):
    def __init__(self, socket):
        # self.logger = logging.getLogger(f'worker{os.getpid()}')
        # self.logger.setLevel(log_level)
        # handler = logging.StreamHandler()
        # handler.setLevel(log_level)
        # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        # handler.setFormatter(formatter)
        # self.logger.addHandler(handler)
        logging.info(f"{multiprocessing.current_process().name} running...")
        # self.pn = pn
        # self.tasks = []
        # self.queue = queue
        self.abs_root = os.path.abspath('html')
        # self.event_loop(self.queue, server_socket)

    # def event_loop(self, socket):
    #     # print(client_socket)
    #     # while 1:
    #         # if not queue:
    #         #     socket = client_socket
    #         # else:
    #         # _ = worker_queue.get()
    #         # request_socket, addr = server_socket.accept()
    #         # self.logger.info(f"Handling request from {socket.getpeername()}")
    #         self.logger.info(f"Handling request from {request_socket.getpeername()}")
    #         # print('socket', socket)
    #         self.client(request_socket)

    def get_url(self, path: str) -> (str, dict, bytes):
        """Returns response components with body content from files if path is valid, or error status, if not"""
        path = urllib.parse.urlparse(path)
        path = urllib.parse.unquote(path.path)
        request_abs_path = os.path.abspath(os.path.join(self.abs_root, path.lstrip('/')))
        # self.logger.debug(request_abs_path)
        logging.debug(request_abs_path)
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

    def client(self, current_socket):
        request = current_socket.recv(28096)  # read
        # print(request)
        logging.debug(f"{multiprocessing.current_process().name} got request {request.decode()}")
        response = Response()
        if request:
            method: str = ''
            path: str = ''
            request = request.decode('utf-8')
            request_lines = request.splitlines()
            try:
                method, path, protocol = request_lines[0].split()
            except ValueError:  # bad request
                pass

            if method in ['GET', 'HEAD']:
                status, headers, body = self.get_url(path)
                response.status = status
                response.headers.update(headers)
                match method:
                    case 'GET':
                        # response.headers['Content-Length'] = 0
                        response.body = body
                    # case 'HEAD':
                    #     response.headers['Content-Length'] = 0

            elif not method:
                response.status = "HTTP 405 Method Not Allowed "
                response.headers['Allow'] = "GET, HEAD"

        current_socket.sendall(response.pack_response())
        # print(f"Sent response: {response.pack_response()}")
        # logging.info(f"Sent to {client_socket}: {response.pack_response()}")

        current_socket.shutdown(socket.SHUT_WR)
        # time.sleep(0.1)
        current_socket.close()
        # print(f"Closed socket: {current_socket}")


class ContentTypeProcessor:
    """Read contents from disk by path, and returns it in response components, or 404"""
    content_type = 'text/plain'

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
        return self.content_type


class ContentTypeProcessorCSS(ContentTypeProcessor):
    content_type = 'text/css'


class ContentTypeProcessorHTML(ContentTypeProcessor):
    content_type = 'text/html'


class ContentTypeProcessorPlainText(ContentTypeProcessor):
    content_type = 'text/plain'


class ContentTypeProcessorGIF(ContentTypeProcessor):
    content_type = 'image/gif'


class ContentTypeProcessorJPEG(ContentTypeProcessor):
    content_type = 'image/jpeg'


class ContentTypeProcessorJS(ContentTypeProcessor):
    content_type = 'text/javascript'


class ContentTypeProcessorPNG(ContentTypeProcessor):
    content_type = 'image/png'


class ContentTypeProcessorSWF(ContentTypeProcessor):
    content_type = 'application/x-shockwave-flash'


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


# def main(i, queue, document_root, log_level, server_socket):
def main(socket, log_level):
    logger = logging.getLogger()
    logger.setLevel(log_level)

    worker = GETHEADHTTPWorker(socket)
    # print(os.getpid())
    worker.client(socket)


if __name__ == "__main__":
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    parser.add_argument('-w', default=2, nargs='?', help='Number of workers')
    parser.add_argument('-r', default='html', nargs='?', help='Path to DOCUMENT_ROOT, relative to httpd.py')
    parser.add_argument('--log_level', type=str, default='DEBUG', nargs='?', help='Log level')
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

    pool = multiprocessing.Pool(args.w)  # use 4 worker processes

    # processes = []
    # queues = []
    # for i in range(args.w):
    #     queue = multiprocessing.Queue()
    #     process = multiprocessing.Process(target=main, args=(i, queue, args.r, log_level, server_socket))
    #     process.start()
    #     processes.append(process)
    #     queues.append(queue)
    #
    n = 0
    while 1:
        try:
            # logging.info("Before sel")
            n += 1
            # ready_to_read, _, _ = select.select([server_socket], [], [])
            client_socket, addr = server_socket.accept()  # read
            # logging.info(f'Accepted from {addr}')

            pool.apply_async(main, args=(client_socket, log_level))

            # request = client_socket.recv(28096)  # read
            # client_socket.send(f'hello, hi_{n}'.encode())
            # client_socket.close()
            # logging.info("After sel")
            # logging.info(f"Connection from {addr}.")
            # qn = random.randint(0, args.w-1)
            # queues[qn].put(1)
            # logging.info(f"Put to a queue {qn}")
            # queues[0].put(client_socket)
    #         print(queues[0].qsize())
    #         serv = GETHEADHTTPWorker(0, None, args.r, log_level, client_socket)
    #         serv.client(client_socket)
            # serv.event_loop()
        except KeyboardInterrupt:
            break
    #
    # for process in processes:
    #     process.join()
