'''
Created on 3 feb 2025

@author: pedrogil
'''

import sys
import tkinter

from modelo import base_datos
from modelo.tabla_equipos import TablaEquipos


def cerrar_aplicacion(__=None):
    """
    Control de finalización de la aplicación.

    Comprueba que no estemos editando un equipo antes de cerrar.

    """
    # si estamos editando un equipo, no dejamos cerrar la
    # aplicación.
    if tabla_equipos.edicion:
        tkinter.messagebox.showinfo(
            "Cerrar aplicación",
            "Guarde los cambios del equipo antes de finalizar.")
        return
    # Preguntamos al usuario si quiere finalizar la aplicación.
    if not tkinter.messagebox.askokcancel(
            "Finalizar", "¿Quiere cerrar la aplicación?"):
        return
    ventana_principal.destroy()


def temporizador_refrescar():
    """
    Función para refrescar los datos de la tabla de forma periódica.

    """
    ventana_principal.after(500, temporizador_refrescar)
    tabla_equipos.refrescar_tabla()
    estadisticas.config(text=bd.resumen_equipos())


# Abrir conexión.
bd = base_datos.Conexion(
    "homologador",
    "homologador",
    "localhost",
    "eurobot_current")

# Ventana principal
ventana_principal = tkinter.Tk()

# Creamos una cabecera para la aplicación.
cabecera = tkinter.Frame(ventana_principal, bg="green", height=50)
cabecera.grid(row=0, column=0, sticky="nsew", columnspan=2)

# Creamos un marco donde colocar la tabla
tabla = tkinter.Frame(ventana_principal, bg="yellow")
tabla.grid(row=1, column=0, sticky="nsew")

# Creamos otro marco donde aparecerán los puntos a validar.
puntos = tkinter.Frame(ventana_principal)
puntos.grid(row=1, column=1, sticky="nsew")

# Creamos un marco para mostrar la barra de estado.
barra_estado = tkinter.Frame(ventana_principal)
barra_estado.grid(row=2, column=0, columnspan=2, sticky="ews")
tkinter.Label(barra_estado, text=bd).pack(
    side=tkinter.LEFT, padx=10)
estadisticas = tkinter.Label(barra_estado, text=bd.resumen_equipos())
estadisticas.pack(side=tkinter.RIGHT, padx=10)

# Configuración del ajuste de tamaños.
ventana_principal.columnconfigure(0, weight=0)
ventana_principal.columnconfigure(1, weight=1)
ventana_principal.columnconfigure(2, weight=0)
ventana_principal.rowconfigure(1, weight=1)

# Crear objeto donde se colocará la tabla de equipos.
tabla_equipos = TablaEquipos(tabla, bd, puntos)

# Fijamos el ancho mínimo de la ventana igual al áncho mínimo de la tabla de
# equipos.
ventana_principal.minsize(tabla_equipos.ancho, 300)

# Iniciamos la ventana completamente maximizada. Tener en cuenta que esto
# depende del sistema operativo.
if sys.platform == "linux" or sys.platform == "linux2":
    ventana_principal.attributes("-zoomed", True)
elif sys.platform == "darwin":
    raise RuntimeError("Aplicación no diseñada para MAC")
elif sys.platform == "win32":
    ventana_principal.state('zoomed')

# Tecla Escape para salir de la aplicación
ventana_principal.bind("<Escape>", cerrar_aplicacion)
ventana_principal.protocol("WM_DELETE_WINDOW", cerrar_aplicacion)
# Activamos el temporizador.
temporizador_refrescar()

ventana_principal.mainloop()
