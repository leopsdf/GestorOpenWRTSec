import sys
import socket
import selectors
import types

sel = selectors.DefaultSelector()
messages = [b"Messagem 1 do client.", b"Messagem 2 do client."]


def start_connections(host, port, num_conns):
    server_addr = (host, port)
    for i in range(0, num_conns):
        connid = i + 1
        print(f"Comecando conexao {connid} para {server_addr}")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(False)
        sock.connect_ex(server_addr)
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        data = types.SimpleNamespace(
            connid=connid,
            msg_total=sum(len(m) for m in messages),
            recv_total=0,
            messages=messages.copy(),
            outb=b"",
        )
        sel.register(sock, events, data=data)


def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)  # Deve estar pronto para ser lido
        if recv_data:
            print(f"Recebido {recv_data!r} da conexao {data.connid}")
            data.recv_total += len(recv_data)
        if not recv_data or data.recv_total == data.msg_total:
            print(f"Fechando conexao {data.connid}")
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:
        if not data.outb and data.messages:
            data.outb = data.messages.pop(0)
        if data.outb:
            print(f"Enviando {data.outb!r} para a conexao {data.connid}")
            sent = sock.send(data.outb)  # Deve estar pronto pra ser escrito
            data.outb = data.outb[sent:]


if len(sys.argv) != 4:
    print(f"Uso correto: {sys.argv[0]} <host> <port> <num_connections>")
    sys.exit(1)

host, port, num_conns = sys.argv[1:4]
start_connections(host, int(port), int(num_conns))

try:
    while True:
        events = sel.select(timeout=1)
        if events:
            for key, mask in events:
                service_connection(key, mask)
        # Verifica se há um soquete sendo monitorado para continuar.
        if not sel.get_map():
            break
except KeyboardInterrupt:
    print("Interrupcao do teclado capturada, saindo...")
finally:
    sel.close()