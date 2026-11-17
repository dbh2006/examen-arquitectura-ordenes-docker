# Sistema de Órdenes de Venta

**Asignatura:** Arquitectura de Computadoras  
**Proyecto:** Examen práctico con Docker Compose

## Integrantes

Este proyecto fue desarrollado de manera individual.

Dimas Belsasar Hernandez Herrera - 202410110004

## 1. Descripción del proyecto

Este proyecto consiste en un sistema web para administrar órdenes de venta, utilizando Docker Compose, Django, Flask y SQL Server 2022.

El sistema permite crear, consultar, editar y eliminar órdenes, además de agregar productos y calcular automáticamente el total de cada venta.

Su objetivo es poner en práctica el uso de contenedores, redes y almacenamiento persistente con Docker.

## 2. Arquitectura del sistema

El proyecto utiliza tres contenedores principales:

- **SQL Server 2022 (db):** almacena las órdenes y sus productos.
- **Flask (api):** procesa las solicitudes y realiza las operaciones con la base de datos.
- **Django (web):** muestra la interfaz donde el usuario administra las órdenes.

Los servicios se comunican mediante una red bridge llamada `ordenes_net`.

**Flujo de comunicación:**

`Usuario → Django → Flask → SQL Server`

También se utiliza un servicio auxiliar llamado `db-init` para inicializar la base de datos cuando todavía no existe.

## 3. Tecnologías utilizadas

- Docker y Docker Compose
- Python 3.12
- Django
- Flask
- Gunicorn
- Microsoft SQL Server 2022
- HTML y CSS

## 4. Estructura del proyecto

```text
ordenes-docker/
├── api/
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .dockerignore
├── db/
│   ├── init.sql
│   └── init-db.sh
├── web/
│   ├── config/
│   ├── ordenes/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── manage.py
│   └── .dockerignore
├── evidencias/
├── .env.example
├── .gitignore
├── compose.yaml
└── README.md
```

## 5. Requisitos para ejecutar

- Tener instalado Docker Desktop.
- Contar con Docker Compose.
- Tener disponibles los puertos `8000`, `5000` y `1434`.
- Disponer de memoria suficiente para ejecutar los contenedores.

## 6. Configuración y ejecución

**Paso 1.** Descargar el proyecto y abrir su carpeta principal.

**Paso 2.** Crear un archivo `.env` tomando como referencia `.env.example`.

Configurar las variables necesarias, especialmente:

- `MSSQL_SA_PASSWORD`: contraseña de SQL Server.
- `DJANGO_SECRET_KEY`: clave secreta de Django.

**Paso 3.** Abrir una terminal y ejecutar:

```powershell
docker compose up -d --build
```

**Paso 4.** Comprobar los contenedores:

```powershell
docker compose ps
```

**Paso 5.** Abrir el sistema:

- **Interfaz Django:** http://localhost:8000
- **API Flask:** http://localhost:5000/api/ordenes
- **Estado de la API:** http://localhost:5000/health

## 7. Base de datos y persistencia

SQL Server utiliza un volumen llamado `sql_data` para conservar la información.

El archivo `db/init.sql` contiene las instrucciones para crear la base de datos, sus tablas y cinco órdenes de ejemplo.

El servicio `db-init` comprueba si la base de datos existe antes de ejecutar la inicialización.

Gracias al volumen, las órdenes permanecen guardadas después de detener y volver a iniciar los contenedores.

## 8. Operaciones de la API REST

| Método | Ruta | Función |
|---|---|---|
| GET | `/health` | Verificar la conexión |
| GET | `/api/ordenes` | Listar órdenes |
| POST | `/api/ordenes` | Crear orden |
| GET | `/api/ordenes/{id}` | Consultar orden |
| PUT | `/api/ordenes/{id}` | Editar orden |
| DELETE | `/api/ordenes/{id}` | Eliminar orden |
| GET | `/api/ordenes/{id}/detalles` | Consultar productos |
| POST | `/api/ordenes/{id}/detalles` | Agregar producto |
| PUT | `/api/detalles/{id}` | Editar producto |
| DELETE | `/api/detalles/{id}` | Eliminar producto |

### Ejemplo para crear una orden

**Método:** `POST`  
**Ruta:** `/api/ordenes`

```json
{
  "cliente": "Carlos Martínez",
  "estado": "Pendiente"
}
```

### Ejemplo para agregar un producto

**Método:** `POST`  
**Ruta:** `/api/ordenes/1/detalles`

```json
{
  "producto": "Teclado",
  "cantidad": 2,
  "precio_unitario": 850.00
}
```

El total de la orden se actualiza automáticamente al agregar, modificar o eliminar productos.

## 9. Recursos y seguridad

Se configuraron límites de recursos para cada servicio:

| Servicio | Memoria | CPU |
|---|---|---|
| SQL Server | 3 GB | 2 |
| Flask | 512 MB | 1 |
| Django | 512 MB | 1 |

También se utilizaron verificaciones de salud (*healthchecks*), dependencias entre servicios y archivos `.dockerignore`.

Las contraseñas se almacenan en `.env`, archivo que no debe publicarse en GitHub.

## 10. Comandos útiles

**Iniciar los contenedores:**

```powershell
docker compose up -d
```

**Detener los contenedores:**

```powershell
docker compose stop
```

**Ver el estado:**

```powershell
docker compose ps
```

**Consultar los registros:**

```powershell
docker compose logs
```

**Consultar el consumo de recursos:**

```powershell
docker stats
```

**Importante:** no utilizar `docker compose down -v` si se desea conservar la información de la base de datos.

## 11. Evidencias

En la carpeta `evidencias` se incluyen capturas del funcionamiento de los contenedores, la interfaz web, las operaciones CRUD, la persistencia de datos y el consumo de recursos.


## 12. Publicación

El código fuente del proyecto está disponible en GitHub:

- [Repositorio GitHub](https://github.com/dbh2006/examen-arquitectura-ordenes-docker)

Las imágenes de los servicios fueron publicadas en Docker Hub:

- [API Flask](https://hub.docker.com/r/dbhernandez/ordenes-api) — `dbhernandez/ordenes-api:v1.0`
- [Django Web](https://hub.docker.com/r/dbhernandez/ordenes-web) — `dbhernandez/ordenes-web:v1.0`

**Versión:** `v1.0`

## 13. Conclusión

Con este proyecto pude aplicar lo aprendido sobre Docker Compose, integrando Django, Flask y SQL Server en un mismo sistema.

También comprendí mejor cómo se comunican los contenedores y cómo conservar la información mediante volúmenes persistentes.