'''
Created on 3 feb 2025

@author: pedrogil
'''

import sys
import tkinter

import base_datos
from tabla import Tabla


def temporizador_refrescar():
    ventana_principal.after(1000, temporizador_refrescar)
    refrescar_tabla()


def refrescar_tabla():
    lista = bd.equipos_registrados()
    lista = Tabla.formatear_lista_tabla(lista)
    tabla_equipos.refrescar(lista)


def rueda_raton(event):
    print("rueda")


# Ventana principal
ventana_principal = tkinter.Tk()

# Creamos una cabecera para la aplicación.
cab = tkinter.Frame(ventana_principal, bg="green", height=20)
cab.grid(row=0, column=0, sticky="nsew")

# Creamos un marco donde colocar la tabla
tabla = tkinter.Frame(ventana_principal, bg="yellow", height=10)
tabla.grid(row=1, column=0, sticky="nsew")

ventana_principal.columnconfigure(0, minsize=200, weight=1)
ventana_principal.rowconfigure(1, weight=1)

# Y sobre este marco creamos la tabla
bd = base_datos.Conexion("homologador", "homologador",
                         "localhost", "eurobot_current")

campos_cabecera = bd.cabecera_vista_equipos()
cabecera = [columna["Field"] for columna in campos_cabecera]

ancho = [150, 400, 40, 40, 40]
ajuste = [0, 1, 0, 0, 0]
fuente_cabecera = ("HELVETICA", 20, "bold")
# fuente_datos = ("HELVETICA", 20, "roman")
fuente_datos = ("HELVETICA", 15, "bold")

lista = bd.equipos_registrados()
lista = Tabla.formatear_lista_tabla(lista)
tabla_equipos = Tabla(tabla, cabecera, lista, ancho, ajuste, 50,
                      45, fuente_cabecera, fuente_datos)

ventana_principal.minsize(tabla_equipos.ancho_tabla, 300)

tabla.bind("<Button-4>", rueda_raton)
tabla.bind("<Button-5>", rueda_raton)

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
