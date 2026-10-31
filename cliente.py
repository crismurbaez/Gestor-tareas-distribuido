import socket
import json
import struct

HOST = "localhost"
PORT = 5000


def _recv_exacto(sock, cantidad):
    """Lee exactamente `cantidad` bytes del socket (o lanza si se corta la conexión)."""
    fragmentos = []
    restante = cantidad
    while restante > 0:
        fragmento = sock.recv(restante)
        if not fragmento:
            raise ConnectionError("El servidor cerró la conexión inesperadamente.")
        fragmentos.append(fragmento)
        restante -= len(fragmento)
    return b"".join(fragmentos)


def enviar_peticion(datos):
    """Abre un socket, envía la petición JSON, espera la respuesta y cierra."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as cliente:
        try:
            cliente.connect((HOST, PORT))
            cuerpo = json.dumps(datos).encode("utf-8")
            # Prefijo de longitud (4 bytes, big-endian) para delimitar el mensaje
            cliente.sendall(struct.pack("!I", len(cuerpo)) + cuerpo)

            (longitud,) = struct.unpack("!I", _recv_exacto(cliente, 4))
            respuesta = _recv_exacto(cliente, longitud).decode("utf-8")
            return json.loads(respuesta)
        except ConnectionRefusedError:
            return {"status": "error", "mensaje": "El servidor distribuido está fuera de línea."}
        except (ConnectionError, OSError):
            return {"status": "error", "mensaje": "Se perdió la conexión con el servidor distribuido."}


def main():
    sesion_activa = False

    while True:
        print("\n--- GESTOR DE TAREAS DISTRIBUIDO ---")
        print("1. Registrar Usuario")
        print("2. Iniciar Sesión")
        print("3. Ver Tareas")
        print("4. Salir")

        opcion = input("Seleccione una opción: ")

        if opcion == "1":
            usr = input("Nuevo usuario: ")
            pwd = input("Contraseña: ")
            res = enviar_peticion({"accion": "registro", "usuario": usr, "password": pwd})
            print(f"> {res['mensaje']}")

        elif opcion == "2":
            usr = input("Usuario: ")
            pwd = input("Contraseña: ")
            res = enviar_peticion({"accion": "login", "usuario": usr, "password": pwd})
            print(f"> {res['mensaje']}")
            if res["status"] == "success":
                sesion_activa = True

        elif opcion == "3":
            if not sesion_activa:
                print("> Error: Debe iniciar sesión primero.")
            else:
                res = enviar_peticion({"accion": "get_tareas", "auth": True})
                print(f"> Respuesta del sistema: {res.get('tareas', res['mensaje'])}")

        elif opcion == "4":
            print("Saliendo del sistema...")
            break
        else:
            print("Opción inválida.")


if __name__ == "__main__":
    main()
