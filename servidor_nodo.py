# servidor_nodo.py
import socket
import threading
import os

def handle_client(conn, addr):
    try:
        msg = conn.recv(1024).decode()
        if msg == "ping":
            conn.send("pong".encode())
        elif msg.startswith("file:"):
            filename = msg.split(":")[1]
            with open(f"recibido_{filename}", "wb") as f:
                while True:
                    chunk = conn.recv(4096)
                    if not chunk:
                        break
                    f.write(chunk)
            print(f"[+] Archivo recibido de {addr}: {filename}")
    except Exception as e:
        print(f"[!] Error con {addr}: {e}")
    finally:
        conn.close()

def start_server(port=9000):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('', port))
    server.listen()
    print(f"Servidor escuchando en puerto {port}")
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

if __name__ == "__main__":
    start_server()