import socket

HOST = "127.0.0.1"  # O hostname ou IP do servidor
PORT = 6653  # porta utilizada pelo servidor

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s: # cria o obj socket | AF_INET p/ IPv4 | SOCK_STREAM -> p/ TCP
    s.connect((HOST, PORT)) # conecta ao servidor
    s.sendall(b"Hello, world") # manda a mensagem
    data = s.recv(1024) # lê a mensagem

print(f"Recebido: {data!r}")