from flask import Flask, request, jsonify, Response
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
DB_NAME = "tareas.db"

def init_db():
    """Inicializa la base de datos SQLite y crea la tabla de usuarios si no existe."""
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

# 1. Endpoint de Registro de Usuarios
@app.route("/registro", methods=["POST"])
def registro():
    datos = request.get_json()
    if not datos or "usuario" not in datos or "contraseña" not in datos:
        return jsonify({"status": "error", "mensaje": "Faltan datos de usuario o contraseña"}), 400

    usuario = datos["usuario"].strip()
    password = datos["contraseña"]

    if not usuario or not password:
        return jsonify({"status": "error", "mensaje": "El usuario y la contraseña no pueden estar vacíos"}), 400

    # Hashear la contraseña antes de guardarla (nunca en texto plano)
    password_hasheada = generate_password_hash(password)

    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            # Uso de consulta parametrizada (?) para evitar Inyección SQL
            cursor.execute(
                "INSERT INTO usuarios (usuario, password_hash) VALUES (?, ?)",
                (usuario, password_hasheada)
            )
            conn.commit()
        return jsonify({"status": "success", "mensaje": f"Usuario '{usuario}' registrado con éxito."}), 201
    except sqlite3.IntegrityError:
        return jsonify({"status": "error", "mensaje": "El nombre de usuario ya existe."}), 409
    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 500

# 2. Endpoint de Inicio de Sesión
@app.route("/login", methods=["POST"])
def login():
    datos = request.get_json()
    if not datos or "usuario" not in datos or "contraseña" not in datos:
        return jsonify({"status": "error", "mensaje": "Debe enviar usuario y contraseña"}), 400

    usuario = datos["usuario"]
    password = datos["contraseña"]

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM usuarios WHERE usuario = ?", (usuario,))
        fila = cursor.fetchone()

    # Verificar si el usuario existe y si el hash coincide con la contraseña ingresada
    if fila and check_password_hash(fila[0], password):
        return jsonify({
            "status": "success",
            "mensaje": f"Inicio de sesión exitoso. Bienvenido, {usuario}. Acceso permitido a /tareas."
        }), 200
    else:
        return jsonify({"status": "error", "mensaje": "Credenciales inválidas."}), 401

# 3. Endpoint de Gestión de Tareas (HTML de bienvenida con Autenticación Básica obligatoria)
@app.route("/tareas", methods=["GET"])
def tareas():
    auth = request.authorization

    # Si no envía credenciales, exigir Autenticación Básica (401)
    if not auth or not auth.username or not auth.password:
        return Response(
            "Acceso no autorizado. Debe autenticarse.",
            status=401,
            headers={"WWW-Authenticate": 'Basic realm="Login Required"'}
        )

    # Verificar credenciales en SQLite
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM usuarios WHERE usuario = ?", (auth.username,))
        fila = cursor.fetchone()

    if not fila or not check_password_hash(fila[0], auth.password):
        return Response(
            "Acceso no autorizado. Credenciales inválidas.",
            status=401,
            headers={"WWW-Authenticate": 'Basic realm="Login Required"'}
        )

    usuario_actual = auth.username

    html_bienvenida = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Sistema de Gestión de Tareas</title>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f6f9; text-align: center; padding: 50px; }}
            .card {{ background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); display: inline-block; }}
            h1 {{ color: #2c3e50; }}
            p {{ color: #555; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>¡Bienvenido al Sistema de Gestión de Tareas!</h1>
            <p>Sesión activa para: <strong>{usuario_actual}</strong></p>
            <p>Servidor API REST con Flask y persistencia en SQLite funcionando correctamente.</p>
        </div>
    </body>
    </html>
    """
    return Response(html_bienvenida, mimetype="text/html", status=200)

if __name__ == "__main__":
    init_db()
    print("Servidor escuchando en http://localhost:5000...")
    app.run(host="localhost", port=5000, debug=False)