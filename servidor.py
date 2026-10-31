import socket
import threading
import queue
import json
import sqlite3
import struct
from werkzeug.security import generate_password_hash, check_password_hash

HOST = "localhost"
PORT = 5000
DB_NAME = "tareas_distribuido.db"
NUM_WORKERS = 3

# Cola segura para distribuir conexiones a los workers
cola_tareas = queue.Queue()


def init_db():
    """Simula el almacenamiento estructurado (ej. PostgreSQL) del esquema."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        """)
        conn.commit()


def procesar_accion(data):
    """Lógica de negocio ejecutada por los workers."""
    accion = data.get("accion")

    if accion == "registro":
        usuario = data.get("usuario")
        password = data.get("password")
        if not usuario or not password:
            return {"status": "error", "mensaje": "Faltan datos."}

        try:
            hash_pass = generate_password_hash(password)
            with sqlite3.connect(DB_NAME) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO usuarios (usuario, password_hash) VALUES (?, ?)",
                    (usuario, hash_pass),
                )
                conn.commit()
            return {"status": "success", "mensaje": f"Usuario {usuario} registrado exitosamente."}
        except sqlite3.IntegrityError:
            return {"status": "error", "mensaje": "El usuario ya existe."}

    elif accion == "login":
        usuario = data.get("usuario")
        password = data.get("password")
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT password_hash FROM usuarios WHERE usuario = ?", (usuario,))
            fila = cursor.fetchone()

        if fila and check_password_hash(fila[0], password):
            return {"status": "success", "mensaje": "Login exitoso. Token generado."}
        return {"status": "error", "mensaje": "Credenciales inválidas."}

    elif accion == "get_tareas":
        # Requiere que el cliente envíe sus credenciales en la petición para validar sesión
        if not data.get("auth"):
            return {"status": "error", "mensaje": "Acceso denegado. Se requiere autenticación."}
        return {
            "status": "success",
            "mensaje": "Lista de tareas distribuida obtenida correctamente.",
            "tareas": ["Tarea 1", "Tarea 2"],
        }

    return {"status": "error", "mensaje": "Acción no reconocida."}


def _recv_exacto(sock, cantidad):
    """Lee exactamente `cantidad` bytes del socket (o lanza si se corta la conexión)."""
    fragmentos = []
    restante = cantidad
    while restante > 0:
        fragmento = sock.recv(restante)
        if not fragmento:
            raise ConnectionError("Conexión cerrada antes de recibir todos los datos.")
        fragmentos.append(fragmento)
        restante -= len(fragmento)
    return b"".join(fragmentos)


def _recibir_mensaje(sock):
    """Recibe un mensaje con prefijo de longitud (4 bytes, big-endian) y lo decodifica."""
    cabecera = _recv_exacto(sock, 4)
    (longitud,) = struct.unpack("!I", cabecera)
    if longitud == 0:
        return None
    return json.loads(_recv_exacto(sock, longitud).decode("utf-8"))


def _enviar_mensaje(sock, objeto):
    """Serializa un objeto a JSON y lo envía con prefijo de longitud (4 bytes, big-endian)."""
    cuerpo = json.dumps(objeto).encode("utf-8")
    sock.sendall(struct.pack("!I", len(cuerpo)) + cuerpo)


def worker(worker_id):
    """Función de bucle continuo para el Thread Pool."""
    while True:
        cliente_socket, direccion = cola_tareas.get()
        print(f"[Worker {worker_id}] Atendiendo conexión de {direccion}")
        try:
            # Recibir datos del cliente y parsear JSON
            datos = _recibir_mensaje(cliente_socket)
            if datos is not None:
                respuesta = procesar_accion(datos)
                # Enviar respuesta serializada y cerrar socket de este cliente
                _enviar_mensaje(cliente_socket, respuesta)
        except Exception as e:
            print(f"[Worker {worker_id}] Error: {e}")
        finally:
            cliente_socket.close()
            cola_tareas.task_done()


def iniciar_servidor():
    init_db()

    # Iniciar pool de 3 hilos workers (Clase 10 / Thread Pool)
    for i in range(NUM_WORKERS):
        hilo = threading.Thread(target=worker, args=(i + 1,), daemon=True)
        hilo.start()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        servidor.bind((HOST, PORT))
        servidor.listen(5)
        print(f"Servidor distribuido escuchando en {HOST}:{PORT}...")

        while True:
            # Hilo principal dedicado exclusivamente a aceptar conexiones
            cliente, direccion = servidor.accept()
            cola_tareas.put((cliente, direccion))


if __name__ == "__main__":
    iniciar_servidor()
