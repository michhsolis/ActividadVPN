# cliente_gui.py
import socket
import time
import tkinter as tk
from tkinter import messagebox, scrolledtext
import heapq
import os

# ------------------ Funciones de red ------------------

def ping_node(ip, port=9000):
    try:
        s = socket.socket()
        s.settimeout(1)
        start = time.time()
        s.connect((ip, port))
        s.send("ping".encode())
        resp = s.recv(1024).decode()
        s.close()
        if resp == "pong":
            end = time.time()
            return round((end - start) * 1000, 2)
    except:
        return None

def send_file(ip, filename, port=9000, log_callback=None):
    try:
        s = socket.socket()
        s.connect((ip, port))
        s.send(f"file:{os.path.basename(filename)}".encode())
        time.sleep(0.1)
        with open(filename, "rb") as f:
            while chunk := f.read(4096):
                s.send(chunk)
        s.close()
        if log_callback:
            log_callback("✅ Transferencia completada.")
    except Exception as e:
        if log_callback:
            log_callback(f"[!] Error al transferir: {e}")

# ------------------ Construcción del grafo ------------------

def construir_grafo(ip_list, log_callback):
    graph = {ip: {} for ip in ip_list}
    for src in ip_list:
        for dst in ip_list:
            if src == dst:
                continue
            latency = ping_node(dst)
            if latency is not None:
                graph[src][dst] = latency
                log_callback(f"{src} → {dst}: {latency} ms")
            else:
                log_callback(f"{src} → {dst}: sin respuesta")
    return graph

# ------------------ Dijkstra ------------------

def dijkstra(graph, start):
    distances = {node: float('inf') for node in graph}
    distances[start] = 0
    previous_nodes = {node: None for node in graph}
    queue = [(0, start)]

    while queue:
        current_distance, current_node = heapq.heappop(queue)
        if current_distance > distances[current_node]:
            continue
        for neighbor, weight in graph[current_node].items():
            distance = current_distance + weight
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                previous_nodes[neighbor] = current_node
                heapq.heappush(queue, (distance, neighbor))
    return distances, previous_nodes

def reconstruir_ruta(prev, destino):
    ruta = []
    while destino:
        ruta.insert(0, destino)
        destino = prev[destino]
    return ruta

# ------------------ GUI ------------------

class RedGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Análisis de Red con Sockets")

        # IPs
        tk.Label(root, text="IPs de la red (separadas por coma):").grid(row=0, column=0, sticky="e")
        self.entry_ips = tk.Entry(root, width=60)
        self.entry_ips.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(root, text="IP origen:").grid(row=1, column=0, sticky="e")
        self.entry_origen = tk.Entry(root, width=40)
        self.entry_origen.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(root, text="IP destino:").grid(row=2, column=0, sticky="e")
        self.entry_destino = tk.Entry(root, width=40)
        self.entry_destino.grid(row=2, column=1, padx=5, pady=5)

        self.btn_analizar = tk.Button(root, text="Analizar red", command=self.analizar_red)
        self.btn_analizar.grid(row=3, column=0, columnspan=2, pady=10)

        # Transferencia
        tk.Label(root, text="Archivo local:").grid(row=4, column=0, sticky="e")
        self.entry_archivo = tk.Entry(root, width=60)
        self.entry_archivo.grid(row=4, column=1, padx=5, pady=5)

        tk.Label(root, text="IP destino para archivo:").grid(row=5, column=0, sticky="e")
        self.entry_ip_transfer = tk.Entry(root, width=40)
        self.entry_ip_transfer.grid(row=5, column=1, padx=5, pady=5)

        self.btn_transferir = tk.Button(root, text="Transferir archivo", command=self.transferir_archivo)
        self.btn_transferir.grid(row=6, column=0, columnspan=2, pady=10)

        # Salida
        self.output = scrolledtext.ScrolledText(root, width=80, height=20)
        self.output.grid(row=7, column=0, columnspan=2, padx=10, pady=10)

    def log(self, mensaje):
        self.output.insert(tk.END, mensaje + "\n")
        self.output.see(tk.END)

    def analizar_red(self):
        self.output.delete(1.0, tk.END)
        ip_list = [ip.strip() for ip in self.entry_ips.get().split(",")]
        origen = self.entry_origen.get().strip()
        destino = self.entry_destino.get().strip()

        if not origen or not destino or not ip_list:
            messagebox.showwarning("Campos incompletos", "Debes ingresar IPs, origen y destino.")
            return

        self.log("Escaneando red...")
        grafo = construir_grafo(ip_list, self.log)

        if origen not in grafo or destino not in grafo:
            messagebox.showerror("Error", "IP de origen o destino no está en la lista.")
            return

        dist, prev = dijkstra(grafo, origen)
        ruta = reconstruir_ruta(prev, destino)

        if dist[destino] == float('inf'):
            self.log(" No hay ruta disponible.")
        else:
            self.log(f"\nRuta óptima: {' -> '.join(ruta)}")
            self.log(f"Latencia total: {dist[destino]} ms")

    def transferir_archivo(self):
        archivo = self.entry_archivo.get().strip()
        ip_destino = self.entry_ip_transfer.get().strip()

        if not archivo or not ip_destino:
            messagebox.showwarning("Campos vacíos", "Archivo y destino requeridos.")
            return

        self.log(f" Enviando archivo a {ip_destino}...")
        send_file(ip_destino, archivo, log_callback=self.log)

# ------------------ Main ------------------

if __name__ == "__main__":
    root = tk.Tk()
    app = RedGUI(root)
    root.mainloop()
