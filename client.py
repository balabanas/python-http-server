import socket

HOST = 'localhost'
PORT = 8081


def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1.0)
    # s.setblocking(False)
    s.connect((HOST, PORT))
    s.send('Hello'.encode('utf-8'))
    while 1:
        data = s.recv(2)
        if not data:
            break
        print(data.decode('utf-8'))
    s.close()


if __name__ == '__main__':
    main()
