
import requests

from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect


API_URL = settings.API_URL.rstrip("/")


def solicitar_api(metodo, ruta, datos=None):
    try:
        respuesta = requests.request(
            metodo,
            f"{API_URL}{ruta}",
            json=datos,
            timeout=10
        )

        try:
            contenido = respuesta.json()
        except ValueError:
            contenido = {}

        if not respuesta.ok:
            if isinstance(contenido, dict):
                error = contenido.get("error", "Error de la API")
            else:
                error = "Error de la API"

            return None, error

        return contenido, None

    except requests.RequestException:
        return None, "No se pudo conectar con la API Flask"


def lista_ordenes(request):
    ordenes, error = solicitar_api("GET", "/api/ordenes")

    if error:
        messages.error(request, error)
        ordenes = []

    return render(request, "ordenes/lista.html", {
        "ordenes": ordenes
    })


def detalle_orden(request, orden_id):
    orden, error = solicitar_api(
        "GET", f"/api/ordenes/{orden_id}"
    )

    if error:
        messages.error(request, error)
        return redirect("lista_ordenes")

    return render(request, "ordenes/detalle.html", {
        "orden": orden
    })


def crear_orden(request):
    if request.method == "POST":
        datos = {
            "cliente": request.POST.get("cliente", "").strip(),
            "estado": request.POST.get("estado", "Pendiente")
        }

        resultado, error = solicitar_api(
            "POST", "/api/ordenes", datos
        )

        if error:
            messages.error(request, error)
        else:
            messages.success(request, "Orden creada correctamente")
            return redirect("detalle_orden", orden_id=resultado["id"])

    return render(request, "ordenes/form_orden.html", {
        "titulo": "Nueva orden",
        "orden": None
    })


def editar_orden(request, orden_id):
    orden, error = solicitar_api(
        "GET", f"/api/ordenes/{orden_id}"
    )

    if error:
        messages.error(request, error)
        return redirect("lista_ordenes")

    if request.method == "POST":
        datos = {
            "cliente": request.POST.get("cliente", "").strip(),
            "estado": request.POST.get("estado", "Pendiente")
        }

        _, error = solicitar_api(
            "PUT", f"/api/ordenes/{orden_id}", datos
        )

        if error:
            messages.error(request, error)
        else:
            messages.success(request, "Orden actualizada")
            return redirect("detalle_orden", orden_id=orden_id)

    return render(request, "ordenes/form_orden.html", {
        "titulo": "Editar orden",
        "orden": orden
    })


def eliminar_orden(request, orden_id):
    if request.method == "POST":
        _, error = solicitar_api(
            "DELETE", f"/api/ordenes/{orden_id}"
        )

        if error:
            messages.error(request, error)
        else:
            messages.success(request, "Orden eliminada")

        return redirect("lista_ordenes")

    return redirect("detalle_orden", orden_id=orden_id)


def agregar_detalle(request, orden_id):
    if request.method == "POST":
        try:
            datos = {
                "producto": request.POST.get("producto", "").strip(),
                "cantidad": int(request.POST.get("cantidad", "0")),
                "precio_unitario": request.POST.get(
                    "precio_unitario", "0"
                )
            }
        except ValueError:
            messages.error(request, "Cantidad no valida")
            return redirect("detalle_orden", orden_id=orden_id)

        _, error = solicitar_api(
            "POST",
            f"/api/ordenes/{orden_id}/detalles",
            datos
        )

        if error:
            messages.error(request, error)
        else:
            messages.success(request, "Producto agregado")

    return redirect("detalle_orden", orden_id=orden_id)


def editar_detalle(request, detalle_id):
    if request.method != "POST":
        return redirect("lista_ordenes")

    orden_id = request.POST.get("orden_id")

    try:
        datos = {
            "producto": request.POST.get("producto", "").strip(),
            "cantidad": int(request.POST.get("cantidad", "0")),
            "precio_unitario": request.POST.get(
                "precio_unitario", "0"
            )
        }
    except ValueError:
        messages.error(request, "Cantidad no valida")
        return redirect("detalle_orden", orden_id=orden_id)

    _, error = solicitar_api(
        "PUT", f"/api/detalles/{detalle_id}", datos
    )

    if error:
        messages.error(request, error)
    else:
        messages.success(request, "Producto actualizado")

    return redirect("detalle_orden", orden_id=orden_id)


def eliminar_detalle(request, detalle_id):
    if request.method != "POST":
        return redirect("lista_ordenes")

    orden_id = request.POST.get("orden_id")

    _, error = solicitar_api(
        "DELETE", f"/api/detalles/{detalle_id}"
    )

    if error:
        messages.error(request, error)
    else:
        messages.success(request, "Producto eliminado")

    return redirect("detalle_orden", orden_id=orden_id)
