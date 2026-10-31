# Sistema de Gestión de Tareas distribuido — PFO 3

**Materia:** Programación sobre redes

**Año:** 3º E

**Alumna:** Cristina Laura Murguía Báez

**Repositorio:** [Gestor-tareas-distribuido](https://github.com/crismurbaez/Gestor-tareas-distribuido)

---

## 1. Diagrama del sistema

Arquitectura distribuida cliente-servidor: los clientes envían solicitudes a través de un
balanceador de carga, que las reparte entre varios servidores workers. Cada servidor worker mantiene
su propio pool de hilos y se comunica con los demás mediante una cola de mensajes (RabbitMQ). La
persistencia se resuelve con almacenamiento distribuido (PostgreSQL + S3).

![Diagrama del sistema](diagrama/diagrama.png)

| # | Componente | Rol |
|---|---|---|
| 1 | **Clientes** | Aplicaciones web y móviles que envían solicitudes al sistema. |
| 2 | **Balanceador de carga** | Recibe todas las solicitudes y las reparte entre los servidores workers (Nginx / HAProxy). |
| 3 | **Servidores workers** | Procesan las solicitudes. Cada servidor tiene su propio pool de hilos para atender varias tareas en paralelo. |
| 4 | **Cola de mensajes (RabbitMQ)** | Canal de comunicación entre servidores: permite que los workers intercambien y distribuyan tareas entre sí. |
| 5 | **Almacenamiento distribuido** | PostgreSQL guarda los datos estructurados y S3 los archivos. Ambos son accesibles desde todos los servidores. |

---

## 2. Código del servidor y cliente

- **`servidor.py`**: un socket TCP principal acepta conexiones y las encola de inmediato en una
  `queue.Queue`. Un pool de 3 hilos *worker* consume esa cola concurrentemente, ejecuta la lógica de
  negocio contra SQLite y devuelve la respuesta codificada en JSON.
- **`cliente.py`**: abre un socket TCP por petición, envía un diccionario serializado en JSON y
  espera la respuesta JSON del servidor.

Cada mensaje viaja con un prefijo de longitud de 4 bytes (big-endian) seguido del cuerpo JSON en
UTF-8, para que un `recv()` no corte el mensaje a la mitad.

| Acción       | Campos enviados           | Respuesta                     |
|--------------|---------------------------|-------------------------------|
| `registro`   | `usuario`, `password`     | `status`, `mensaje`           |
| `login`      | `usuario`, `password`     | `status`, `mensaje`           |
| `get_tareas` | `auth` (booleano)         | `status`, `mensaje`, `tareas` |

### Ejecución

```powershell
pip install -r requirements.txt
python servidor.py
```

En otra terminal:

```powershell
python cliente.py
```

El servidor crea la base `tareas_distribuido.db` y queda escuchando en `localhost:5000`. En el menú
del cliente: **1** registrar usuario, **2** iniciar sesión, **3** ver tareas, **4** salir.
