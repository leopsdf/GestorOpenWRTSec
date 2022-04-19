import sys
import socket
import selectors
import types

sel = selectors.DefaultSelector()


def accept_wrapper(sock):
    conn, addr = sock.accept()  
    print(f"Conexão aceita de {addr}")
    conn.setblocking(False) 
    # sock.accept() -> conn.setblocking(False) : coloca o socket em modo não bloqueante 
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"") # cria um objeto para armazenar dados que deseja incluit junto com o socket
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)


def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)  # Should be ready to read
        if recv_data:
            data.outb += recv_data
        else:
            print(f"Fechando conexao com {data.addr}")
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            print(f"Echoing {data.outb!r} para {data.addr}")
            sent = sock.send(data.outb)  # Should be ready to write
            data.outb = data.outb[sent:]


if len(sys.argv) != 3:
    print(f"Uso correto: {sys.argv[0]} <host> <port>")
    sys.exit(1)

host, port = sys.argv[1], int(sys.argv[2])
lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
lsock.bind((host, port))
lsock.listen()
print(f"Escutando em {(host, port)}")
lsock.setblocking(False) # configura o socker em modo non-blocking
sel.register(lsock, selectors.EVENT_READ, data=None) # registra o socket a ser monitorado pelo sel.select()

try:
    while True: #
        events = sel.select(timeout=None) #  
        # sel.seletc() espera por eventos em um ou mais socket e então le e grava dados quando estiver pronto
        for key, mask in events:
            if key.data is None:
                accept_wrapper(key.fileobj)
            else:
                service_connection(key, mask)
except KeyboardInterrupt:
    print("Interrupção do teclado capturada, saindo...")
finally:
    sel.close()