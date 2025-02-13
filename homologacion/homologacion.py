'''
Created on 3 feb 2025

@author: pedrogil
'''

import sys
import tkinter

from base_datos import estado
import base_datos
from tabla import Tabla


def temporizador_refrescar():
    ventana_principal.after(500, temporizador_refrescar)
    refrescar_tabla()


def refrescar_tabla():
    lista = bd.lista_equipos(estado)
    lista = Tabla.formatear_lista_tabla(lista)
    tabla_equipos.refrescar(lista)


def evento(fila, columna, evento=None):
    print(fila, columna)


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
bd = base_datos.Conexion(
    "homologador",
    "homologador",
    "localhost",
    "eurobot_current")


def seleccionar_estado(es):
    global estado
    estado = es
    refrescar_tabla()
    return estado


# Añadimos botones para cambiar entre los distintos estados del equipo.
tkinter.Button(cab, text="Inscritos",
               command=lambda: seleccionar_estado(estado.INSCRITO)).pack(side=tkinter.LEFT)

tkinter.Button(cab, text="Registrados",
               command=lambda: seleccionar_estado(estado.REGISTRADO)).pack(side=tkinter.LEFT)

tkinter.Button(cab, text="Homologados",
               command=lambda: seleccionar_estado(estado.HOMOLOGADO)).pack(side=tkinter.LEFT)

ancho = [150, 400, 50, 50, 40, 40, 40]
ajuste = [0, 1, 0, 0, 0, 0, 0]
alineacion = ["center", "w", "center", "center", "center", "center", "center"]
fuente_cabecera = ("HELVETICA", 20, "bold")
# fuente_datos = ("HELVETICA", 20, "roman")
fuente_datos = ("HELVETICA", 15, "bold")

cabecera = bd.cabecera_vista_equipos()

tabla_equipos = Tabla(tabla, cabecera, ancho, ajuste, alineacion,
                      50, 45, fuente_cabecera, fuente_datos)

estado = seleccionar_estado(estado.INSCRITO)


# lista = bd.lista_equipos(estado)

tabla_equipos.añadir_evento("<Double-1>", 4, evento)
tabla_equipos.añadir_evento("<Double-1>", 5, evento)
tabla_equipos.añadir_evento("<Double-1>", 6, evento)

# lista = Tabla.formatear_lista_tabla(lista)
# tabla_equipos.refrescar(lista)

ventana_principal.minsize(tabla_equipos.ancho_tabla, 300)

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
