import requests

BASE_URL = "http://localhost:5000"
sesion_creada = None  # Guardará (usuario, contraseña) tras iniciar sesión

def registrar_usuario():
    usuario = input("Ingrese nombre de usuario: ")
    password = input("Ingrese contraseña: ")
    payload = {"usuario": usuario, "contraseña": password}
    
    response = requests.post(f"{BASE_URL}/registro", json=payload)
    datos = response.json()
    print(f"[{response.status_code}] {datos.get('mensaje')}")

def iniciar_sesion():
    global sesion_creada
    usuario = input("Usuario: ")
    password = input("Contraseña: ")
    payload = {"usuario": usuario, "contraseña": password}
    
    response = requests.post(f"{BASE_URL}/login", json=payload)
    datos = response.json()
    print(f"[{response.status_code}] {datos.get('mensaje')}")
    
    if response.status_code == 200:
        sesion_creada = (usuario, password)

def ver_tareas():
    if not sesion_creada:
        print("Aviso: Primero debes iniciar sesión (Opción 2) para acceder a tus tareas.")
        return

    # Se envían las credenciales mediante HTTP Basic Auth al endpoint GET /tareas
    response = requests.get(f"{BASE_URL}/tareas", auth=sesion_creada)
    if response.status_code == 200:
        print("\n--- Respuesta HTML del Servidor (GET /tareas) ---")
        print(response.text)
        print("-------------------------------------------------")
    else:
        print(f"Error [{response.status_code}]: {response.text}")

def main():
    while True:
        print("\n=== SISTEMA DE GESTIÓN DE TAREAS ===")
        print("1. Registrar usuario (POST /registro)")
        print("2. Iniciar sesión (POST /login)")
        print("3. Ver tareas / HTML de bienvenida (GET /tareas)")
        print("4. Salir")
        
        opcion = input("Seleccione una opción: ")
        
        try:
            if opcion == "1":
                registrar_usuario()
            elif opcion == "2":
                iniciar_sesion()
            elif opcion == "3":
                ver_tareas()
            elif opcion == "4":
                print("Saliendo del cliente...")
                break
            else:
                print("Opción no válida.")
        except requests.exceptions.ConnectionError:
            print("Error: No se pudo conectar al servidor. Asegúrate de ejecutar 'python servidor.py' primero.")
        except Exception as e:
            print(f"Ocurrió un error inesperado: {e}")

if __name__ == "__main__":
    main()