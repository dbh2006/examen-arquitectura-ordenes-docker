
from flask import Flask, jsonify
import os
import pymssql

app = Flask(__name__)

def conectar_db():
    return pymssql.connect(
        server=os.environ.get("DB_HOST", "db"),
        user=os.environ.get("DB_USER", "sa"),
        password=os.environ["MSSQL_SA_PASSWORD"],
        database=os.environ.get("DB_NAME", "OrdenesDB"),
        port=int(os.environ.get("DB_PORT", "1433"))
    )

def recalcular_total(cursor, orden_id):
    cursor.execute("""
        UPDATE dbo.ordenes
        SET total = (
            SELECT COALESCE(SUM(subtotal), 0)
            FROM dbo.orden_detalle
            WHERE orden_id = %s
        )
        WHERE id = %s
    """, (orden_id, orden_id))

@app.route("/health", methods=["GET"])
def health():
    try:
        conexion = conectar_db()
        conexion.close()

        return jsonify({
            "estado": "ok",
            "mensaje": "API conectada a SQL Server"
        }), 200

    except Exception:
        return jsonify({
            "estado": "error",
            "mensaje": "No se pudo conectar a SQL Server"
        }), 503


@app.route("/api/ordenes", methods=["GET"])
def listar_ordenes():
    try:
        conexion = conectar_db()
        cursor = conexion.cursor(as_dict=True)

        cursor.execute("""
            SELECT id, cliente, fecha, estado, total
            FROM dbo.ordenes
            ORDER BY id
        """)

        ordenes = cursor.fetchall()

        for orden in ordenes:
            orden["fecha"] = str(orden["fecha"])
            orden["total"] = float(orden["total"])

        cursor.close()
        conexion.close()

        return jsonify(ordenes), 200

    except Exception:
        app.logger.exception("Error al consultar las ordenes")
        return jsonify({
            "error": "No se pudieron consultar las ordenes"
        }), 500

from flask import request

# CONSULTAR UNA ORDEN CON SUS DETALLES
@app.route("/api/ordenes/<int:orden_id>", methods=["GET"])
def obtener_orden(orden_id):
    conexion = conectar_db()
    try:
        cursor = conexion.cursor(as_dict=True)

        cursor.execute("""
            SELECT id, cliente, fecha, estado, total
            FROM dbo.ordenes
            WHERE id = %s
        """, (orden_id,))

        orden = cursor.fetchone()

        if not orden:
            return jsonify({"error": "Orden no encontrada"}), 404

        cursor.execute("""
            SELECT id, orden_id, producto, cantidad,
                   precio_unitario, subtotal
            FROM dbo.orden_detalle
            WHERE orden_id = %s
            ORDER BY id
        """, (orden_id,))

        detalles = cursor.fetchall()

        orden["fecha"] = str(orden["fecha"])
        orden["total"] = float(orden["total"])

        for detalle in detalles:
            detalle["precio_unitario"] = float(
                detalle["precio_unitario"]
            )
            detalle["subtotal"] = float(detalle["subtotal"])

        orden["detalles"] = detalles

        return jsonify(orden), 200

    except Exception:
        app.logger.exception("Error al consultar orden")
        return jsonify({"error": "Error interno"}), 500
    finally:
        conexion.close()


# CREAR UNA ORDEN
@app.route("/api/ordenes", methods=["POST"])
def crear_orden():
    datos = request.get_json(silent=True)

    if not isinstance(datos, dict):
        return jsonify({"error": "Se requiere JSON valido"}), 400

    cliente = datos.get("cliente")
    estado = datos.get("estado", "Pendiente")

    if not isinstance(cliente, str) or not cliente.strip():
        return jsonify({"error": "Cliente obligatorio"}), 400

    if len(cliente.strip()) > 150:
        return jsonify({"error": "Cliente demasiado largo"}), 400

    if estado not in ["Pendiente", "Pagada", "Anulada"]:
        return jsonify({"error": "Estado no valido"}), 400

    conexion = conectar_db()

    try:
        cursor = conexion.cursor()

        cursor.execute("""
            INSERT INTO dbo.ordenes (cliente, fecha, estado, total)
            OUTPUT INSERTED.id
            VALUES (%s, CAST(GETDATE() AS DATE), %s, 0)
        """, (cliente.strip(), estado))

        nuevo_id = cursor.fetchone()[0]
        conexion.commit()

        return jsonify({
            "mensaje": "Orden creada correctamente",
            "id": nuevo_id
        }), 201

    except Exception:
        conexion.rollback()
        app.logger.exception("Error al crear orden")
        return jsonify({"error": "Error interno"}), 500
    finally:
        conexion.close()


# ACTUALIZAR UNA ORDEN
@app.route("/api/ordenes/<int:orden_id>", methods=["PUT"])
def actualizar_orden(orden_id):
    datos = request.get_json(silent=True)

    if not isinstance(datos, dict):
        return jsonify({"error": "Se requiere JSON valido"}), 400

    cliente = datos.get("cliente")
    estado = datos.get("estado")

    if not isinstance(cliente, str) or not cliente.strip():
        return jsonify({"error": "Cliente obligatorio"}), 400

    if len(cliente.strip()) > 150:
        return jsonify({"error": "Cliente demasiado largo"}), 400

    if estado not in ["Pendiente", "Pagada", "Anulada"]:
        return jsonify({"error": "Estado no valido"}), 400

    conexion = conectar_db()

    try:
        cursor = conexion.cursor()

        cursor.execute("""
            UPDATE dbo.ordenes
            SET cliente = %s, estado = %s
            WHERE id = %s
        """, (cliente.strip(), estado, orden_id))

        if cursor.rowcount == 0:
            conexion.rollback()
            return jsonify({"error": "Orden no encontrada"}), 404

        conexion.commit()

        return jsonify({
            "mensaje": "Orden actualizada correctamente"
        }), 200

    except Exception:
        conexion.rollback()
        app.logger.exception("Error al actualizar orden")
        return jsonify({"error": "Error interno"}), 500
    finally:
        conexion.close()


# ELIMINAR UNA ORDEN Y SUS DETALLES
@app.route("/api/ordenes/<int:orden_id>", methods=["DELETE"])
def eliminar_orden(orden_id):
    conexion = conectar_db()

    try:
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT id FROM dbo.ordenes WHERE id = %s
        """, (orden_id,))

        if not cursor.fetchone():
            return jsonify({"error": "Orden no encontrada"}), 404

        cursor.execute("""
            DELETE FROM dbo.orden_detalle
            WHERE orden_id = %s
        """, (orden_id,))

        cursor.execute("""
            DELETE FROM dbo.ordenes
            WHERE id = %s
        """, (orden_id,))

        conexion.commit()

        return jsonify({
            "mensaje": "Orden y detalles eliminados"
        }), 200

    except Exception:
        conexion.rollback()
        app.logger.exception("Error al eliminar orden")
        return jsonify({"error": "Error interno"}), 500
    finally:
        conexion.close()

# VALIDAR LOS DATOS DE UN PRODUCTO
def validar_detalle(datos):
    if not isinstance(datos, dict):
        return None, "Se requiere un JSON valido"

    producto = datos.get("producto")
    cantidad = datos.get("cantidad")
    precio = datos.get("precio_unitario")

    if not isinstance(producto, str) or not producto.strip():
        return None, "El producto es obligatorio"

    if len(producto.strip()) > 150:
        return None, "El nombre del producto es demasiado largo"

    if type(cantidad) is not int or cantidad <= 0:
        return None, "La cantidad debe ser un entero positivo"

    from decimal import Decimal, InvalidOperation

    try:
        if isinstance(precio, bool) or precio is None:
            raise ValueError()

        precio_decimal = Decimal(str(precio))

        if not precio_decimal.is_finite():
            raise ValueError()

        if precio_decimal < 0 or precio_decimal > Decimal("9999999999.99"):
            raise ValueError()

        if precio_decimal.as_tuple().exponent < -2:
            raise ValueError()

        if cantidad * precio_decimal > Decimal("9999999999.99"):
            raise ValueError()

    except (InvalidOperation, ValueError, TypeError):
        return None, "El precio debe ser valido, positivo y con maximo 2 decimales"

    return {
        "producto": producto.strip(),
        "cantidad": cantidad,
        "precio_unitario": precio_decimal
    }, None


# LISTAR Y AGREGAR DETALLES DE UNA ORDEN
@app.route("/api/ordenes/<int:orden_id>/detalles",
           methods=["GET", "POST"])
def detalles_orden(orden_id):
    if request.method == "POST":
        datos, error = validar_detalle(request.get_json(silent=True))

        if error:
            return jsonify({"error": error}), 400

    conexion = conectar_db()

    try:
        cursor = conexion.cursor(as_dict=True)

        cursor.execute(
            "SELECT id FROM dbo.ordenes WHERE id = %s",
            (orden_id,)
        )

        if not cursor.fetchone():
            return jsonify({"error": "Orden no encontrada"}), 404

        if request.method == "GET":
            cursor.execute("""
                SELECT id, orden_id, producto, cantidad,
                       precio_unitario, subtotal
                FROM dbo.orden_detalle
                WHERE orden_id = %s
                ORDER BY id
            """, (orden_id,))

            detalles = cursor.fetchall()

            for detalle in detalles:
                detalle["precio_unitario"] = float(
                    detalle["precio_unitario"]
                )
                detalle["subtotal"] = float(detalle["subtotal"])

            return jsonify(detalles), 200

        cursor.execute("""
            INSERT INTO dbo.orden_detalle
                (orden_id, producto, cantidad, precio_unitario)
            OUTPUT INSERTED.id
            VALUES (%s, %s, %s, %s)
        """, (
            orden_id,
            datos["producto"],
            datos["cantidad"],
            datos["precio_unitario"]
        ))

        nuevo_id = cursor.fetchone()["id"]

        recalcular_total(cursor, orden_id)
        conexion.commit()

        return jsonify({
            "mensaje": "Producto agregado correctamente",
            "id": nuevo_id
        }), 201

    except Exception:
        conexion.rollback()
        app.logger.exception("Error al procesar detalles")
        return jsonify({"error": "Error interno"}), 500
    finally:
        conexion.close()


# ACTUALIZAR UN DETALLE
@app.route("/api/detalles/<int:detalle_id>", methods=["PUT"])
def actualizar_detalle(detalle_id):
    datos, error = validar_detalle(request.get_json(silent=True))

    if error:
        return jsonify({"error": error}), 400

    conexion = conectar_db()

    try:
        cursor = conexion.cursor(as_dict=True)

        cursor.execute("""
            SELECT orden_id
            FROM dbo.orden_detalle
            WHERE id = %s
        """, (detalle_id,))

        detalle = cursor.fetchone()

        if not detalle:
            return jsonify({"error": "Detalle no encontrado"}), 404

        orden_id = detalle["orden_id"]

        cursor.execute("""
            UPDATE dbo.orden_detalle
            SET producto = %s,
                cantidad = %s,
                precio_unitario = %s
            WHERE id = %s
        """, (
            datos["producto"],
            datos["cantidad"],
            datos["precio_unitario"],
            detalle_id
        ))

        recalcular_total(cursor, orden_id)
        conexion.commit()

        return jsonify({
            "mensaje": "Detalle actualizado correctamente"
        }), 200

    except Exception:
        conexion.rollback()
        app.logger.exception("Error al actualizar detalle")
        return jsonify({"error": "Error interno"}), 500
    finally:
        conexion.close()


# ELIMINAR UN DETALLE
@app.route("/api/detalles/<int:detalle_id>", methods=["DELETE"])
def eliminar_detalle(detalle_id):
    conexion = conectar_db()

    try:
        cursor = conexion.cursor(as_dict=True)

        cursor.execute("""
            SELECT orden_id
            FROM dbo.orden_detalle
            WHERE id = %s
        """, (detalle_id,))

        detalle = cursor.fetchone()

        if not detalle:
            return jsonify({"error": "Detalle no encontrado"}), 404

        orden_id = detalle["orden_id"]

        cursor.execute("""
            DELETE FROM dbo.orden_detalle
            WHERE id = %s
        """, (detalle_id,))

        recalcular_total(cursor, orden_id)
        conexion.commit()

        return jsonify({
            "mensaje": "Detalle eliminado correctamente"
        }), 200

    except Exception:
        conexion.rollback()
        app.logger.exception("Error al eliminar detalle")
        return jsonify({"error": "Error interno"}), 500
    finally:
        conexion.close()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
