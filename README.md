# python-http-server
Custom HTTP Server on 'vanilla' Python

## Goal
To develop my own web server and implement certain parts of the HTTP protocol:
* Do not use libraries that assist with HTTP operations.
* Test the server under load.

The server is capable of:
1. Scaling on several workers; the number of workers is specified with the `-w` command line argument.
2. Responding with 200, 403, or 404 on GET and HEAD requests.
3. Responding with 405 on other requests.
4. Serving files with arbitrary paths in the `DOCUMENT_ROOT` directory. For example, calling `/file.htm` should serve the contents of `DOCUMENT_ROOT/file.html`.
5. Setting `DOCUMENT_ROOT` as the command line argument `-r`.
6. Serving `index.html` as a directory index. Serving `DOCUMENT_ROOT/directory/index.html` in response to a `/directory/` request.
7. For successful GET requests, responding with the headers `Date`, `Server`, `Content-Length`, `Content-Type`, and `Connection`.
8. Returning the correct `Content-Type` for `.html`, `.css`, `.js`, `.jpg`, `.jpeg`, `.png`, `.gif`, and `.swf` files.
