# python-http-server
Custom HTTP Server on 'vanilla' Python

# Goal
To develop custom web server and implement certain parts of the HTTP protocol:
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
9. Accept spaces and `%XX` in the file names

# Architecture
1. We create TCP server socket to accept incoming connections, and create client sockets from them.
2. Then we create pool of workers using multiprocessing package and Pool
3. On accept of a new connection the newly created socket is passed for handling to a `main` function to one of the worker from the pool, in async mode.
4. The worker itself is implemented as a class `GETHEADHTTPWorker`, so the responsibility of a `main` function is just to create a class's instance and call `client` method to invoke request reading and processing.


# Test suite
* https://github.com/s-stupnikov/http-test-suite
* The address `http://localhost/httptest/wikipedia_russia.html` is correctly displayed by a browser
* Load test `ab -n 50000 -c 100 -r http://localhost:80/`

## Load test results
```root@6b01fecf04a0:/# ab -n 50000 -c 100 -r http://localhost:8081/
This is ApacheBench, Version 2.3 <$Revision: 1879490 $>
Copyright 1996 Adam Twiss, Zeus Technology Ltd, http://www.zeustech.net/
Licensed to The Apache Software Foundation, http://www.apache.org/

Benchmarking localhost (be patient)
Completed 5000 requests
Completed 10000 requests
Completed 15000 requests
Completed 20000 requests
Completed 25000 requests
Completed 30000 requests
Completed 35000 requests
Completed 40000 requests
Completed 45000 requests
Completed 50000 requests
Finished 50000 requests


Server Software:        ServerName
Server Hostname:        localhost
Server Port:            8081

Document Path:          /
Document Length:        156 bytes

Concurrency Level:      100
Time taken for tests:   354.303 seconds
Complete requests:      50000
Failed requests:        0
Total transferred:      14850000 bytes
HTML transferred:       7800000 bytes
Requests per second:    141.12 [#/sec] (mean)
Time per request:       708.605 [ms] (mean)
Time per request:       7.086 [ms] (mean, across all concurrent requests)
Transfer rate:          40.93 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    1  28.5      0    1023
Processing:    22  707 172.5    674    4016
Waiting:       17  706 172.5    673    4015
Total:         22  708 179.9    674    5037

Percentage of the requests served within a certain time (ms)
  50%    674
  66%    751
  75%    804
  80%    836
  90%    933
  95%   1010
  98%   1103
  99%   1207
 100%   5037 (longest request)
 ```




# Memo
## To test with ubuntu
* `docker run -it -v C:/projects/opdp/05_automatization/python-http-server:/home/root/myproject ubuntu /bin/bash`
* `apt update`
* `apt-get install python3.10`
* `apt-get install curl`
* `apt-get install apache2-utils`
* `cd /home/root/myproject`
* `python3.10 httpd.py`

* `docker ps -a` then copypaste container's id
* `docker exec -it 6b01fecf04a0 /bin/bash`

## Web server run on Windows
If use `ubuntu` only for ab load test, and the webserver is run on Windows host:
* `ab -n 50000 -c 100 -r http://host.docker.internal:80` # choose the appropriate port. I'd rather run it not on 80, but on some other, say 8081
