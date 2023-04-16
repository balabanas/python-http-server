import argparse
import datetime
import logging
import multiprocessing
import os
import socket

HOST = 'localhost'
PORT = 80
SERVER_NAME = 'ServerName'


def url_decode(url_encoded_string):
    """Decodes urlencoded strings into `normal` strings"""
    decoded_string = ""
    index = 0
    while index < len(url_encoded_string):
        if url_encoded_string[index] == '%':
            decoded_string += chr(int(url_encoded_string[index+1:index+3], 16))
            index += 3
        else:
            decoded_string += url_encoded_string[index]
            index += 1
    return decoded_string


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
    def __init__(self, doc_root):
        logging.info(f"{multiprocessing.current_process().name} running...")
        self.abs_root = os.path.abspath(doc_root)

    def get_url(self, path: str) -> (str, dict, bytes):
        """Returns response components with body content from files if path is valid, or error status, if not"""
        logging.debug(f"{multiprocessing.current_process().name} - start get_url")
        path = url_decode(path)
        path = path.split('?')[0]
        logging.debug(f"{multiprocessing.current_process().name} - path parsed, {path}")
        request_abs_path = os.path.abspath(os.path.join(self.abs_root, path.lstrip('/')))
        logging.debug(f"Serving from path {request_abs_path}")
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
        logging.debug(f"{multiprocessing.current_process().name} Got request {request.decode()}")
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
                        response.body = body

            elif not method:
                response.status = "HTTP 405 Method Not Allowed "
                response.headers['Allow'] = "GET, HEAD"

        current_socket.send(response.pack_response())
        logging.debug(f"Sent to {current_socket}: {response.pack_response()}")
        current_socket.shutdown(socket.SHUT_WR)
        current_socket.close()


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


def main(worker_socket, doc_root, worker_log_level):
    logger = logging.getLogger()
    logger.setLevel(worker_log_level)
    try:
        worker = GETHEADHTTPWorker(doc_root)
        worker.client(worker_socket)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    parser.add_argument('-w', default=4, nargs='?', help='Number of workers')
    parser.add_argument('-r', default='html', nargs='?', help='Path to DOCUMENT_ROOT, relative to httpd.py')
    parser.add_argument('--log_level', type=str, default='ERROR', nargs='?', help='Log level')
    args: argparse.Namespace = parser.parse_args()
    log_level = getattr(logging, args.log_level.upper(), None)
    if not isinstance(log_level, int):
        raise ValueError(f"Invalid log level: {args.log_level}")
    logging.basicConfig(filename='', datefmt='%Y-%m-%d %H:%M:%S', level=log_level)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    logging.info('Server started')
    pool = multiprocessing.Pool(args.w)
    while 1:
        try:
            client_socket, addr = server_socket.accept()
            pool.apply_async(main, args=(client_socket, args.r, log_level))
            logging.info(f"Connection from {addr}")
        except KeyboardInterrupt:
            pool.terminate()
            break

    pool.close()
    pool.join()
    server_socket.close()
