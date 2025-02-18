'''
Created on 3 feb 2025

@author: pedrogil
'''

import sys
import tkinter

import base_datos
# from pagina_edicion import Pagina
from tabla_equipos import TablaEquipos


def temporizador_refrescar():
    ventana_principal.after(500, temporizador_refrescar)
    tabla_equipos.refrescar_tabla()


bd = base_datos.Conexion(
    "homologador",
    "homologador",
    "localhost",
    "eurobot_current")

# Ventana principal
ventana_principal = tkinter.Tk()

# Creamos una cabecera para la aplicación.
cab = tkinter.Frame(ventana_principal, bg="green", height=50)
cab.grid(row=0, column=0, sticky="nsew", columnspan=2)

# Creamos un marco donde colocar la tabla
tabla = tkinter.Frame(ventana_principal, bg="yellow")
tabla.grid(row=1, column=0, sticky="nsew")

# Creamos otro marco donde aparecerán los puntos a validar.
puntos = tkinter.Frame(ventana_principal, bg="blue")
puntos.grid(row=1, column=1, sticky="nsew")

ventana_principal.columnconfigure(0, weight=1)
ventana_principal.columnconfigure(1, weight=3)
ventana_principal.rowconfigure(1, weight=1)

tabla_equipos = TablaEquipos(bd, tabla)

ventana_principal.minsize(tabla_equipos.ancho, 300)

# Iniciamos la ventana completamente maximizada. Tener en cuenta que esto
# depende del sistema operativo.
if sys.platform == "linux" or sys.platform == "linux2":
    ventana_principal.attributes("-zoomed", True)
elif sys.platform == "darwin":
    raise RuntimeError("Aplicación no diseñada para MAC")
elif sys.platform == "win32":
    ventana_principal.state('zoomed')

temporizador_refrescar()

ventana_principal.mainloop()
