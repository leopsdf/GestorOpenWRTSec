# link excelente: https://realpython.com/python-sockets/

import socket

HOST = "127.0.0.1"  # (localhost) host pode ser um nome de host, endereço IP ou string vazia
PORT = 6653  # Porta dos switches para conexão TCP

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s: # tipo AF_INET -> IPv4 | SOCK_STREAM -> protocolo TCP
    s.bind((HOST, PORT)) # O método .bind() é usado para associar o soquete a uma interface de rede e número de porta específicos
    s.listen() # permite que um servidor aceite conexões | comando: 'netstat -an' permite ve ser o ip e porta estão escutando mesmo
    conn, addr = s.accept() # espera por uma conexão | retorna um novo objeto socket e uma tupla com o endereço do cliente (host, port) para conexões IPv4
    with conn:
        print(f"Conectado ao {addr}") # mensagem de conexão sucedida
        while True: # Loop infinito
            data = conn.recv(1024) # lê as informações enviadas pelo cliente
            if not data:
                break
            conn.sendall(data) # reenvia as informações do cliente
