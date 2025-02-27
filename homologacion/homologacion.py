'''
Created on 3 feb 2025

@author: pedrogil
'''

import sys
import time
from tkinter import PhotoImage
import tkinter

from leer_constantes import abrir_archivo_xml, leer_conexion, leer_ancho_pagina
from leer_constantes import leer_logos
from modelo.base_datos import Conexion
from vista.tabla_equipos import TablaEquipos
from vista.ventana_inicio import crear_ventana_inicio


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
            "Cerrar aplicación", "¿Quiere cerrar la aplicación?"):
        return
    ventana_principal.destroy()


def temporizador_refrescar():
    """
    Función para refrescar los datos de la tabla de forma periódica.

    """
    ventana_principal.after(500, temporizador_refrescar)
    tabla_equipos.refrescar_tabla()
    estadisticas.config(text=conexion.resumen_equipos())


################################################################################
# Abrir archivo de configuración.
################################################################################
try:
    archivo_config = sys.argv[1]
except Exception:
    archivo_config = "constantes.xml"
# Abrir archivo xml con las constantes.
try:
    abrir_archivo_xml(archivo_config)
except Exception as error:
    tkinter.messagebox.showerror("Archivo de configuracion", error)
    exit(1)

################################################################################
# Realizar conexión con la base de datos y ventana de inicio
################################################################################
conexion = leer_conexion()
tiempo_inicio = time.time()
ventana_inicio, tiempo = crear_ventana_inicio()
try:
    conexion = Conexion(
        conexion["USER"],
        conexion["PASS"],
        conexion["HOST"],
        conexion["BASE"])
except ValueError as error:
    ventana_inicio.destroy()
    tkinter.messagebox.showerror(
        "Error", "%s Revise el archivo de configuración. "
        "Se cerrará la aplicación." % error)
    exit()

# Antes de cerrar la ventana de inicio, esperamos al menos el tiempo indicado
# en el archivo de configuración, ya que si la conexión es rápida apenas se
# muestra esta primera ventana.
while(time.time() - tiempo_inicio < tiempo):
    time.sleep(0.1)
# Eliminamos la ventana para poder crear la ventana principal.
ventana_inicio.destroy()

################################################################################
# Crear diseño de la ventana principal
################################################################################
# Ventana principal
ventana_principal = tkinter.Tk()

imagenes = leer_logos()
# Creamos una cabecera para la aplicación.
cabecera = tkinter.Frame(ventana_principal)
cabecera.grid(row=0, column=0, sticky="nsew")
imagen = PhotoImage(file=imagenes["CABECERA"])

# Agregar imagen dentro del Frame usando Label
tkinter.Label(cabecera, image=imagen).pack(padx=10, pady=10)

# Creamos un marco donde colocar la tabla
tabla = tkinter.Frame(ventana_principal, bg="yellow")
tabla.grid(row=1, column=0, sticky="nsew")

# Creamos otro marco donde aparecerán los puntos a validar.
puntos = tkinter.Frame(ventana_principal)
puntos.grid(row=0, column=1, sticky="nsew", rowspan=2)

# Creamos un marco para mostrar la barra de estado.
barra_estado = tkinter.Frame(ventana_principal)
barra_estado.grid(row=2, column=0, columnspan=2, sticky="ews")
# Y las etiquetas dentro de la barra de estado para mostrar la información.
tkinter.Label(barra_estado, text=conexion).pack(
    side=tkinter.LEFT, padx=10)
estadisticas = tkinter.Label(barra_estado, text=conexion.resumen_equipos())
estadisticas.pack(side=tkinter.RIGHT, padx=10)

################################################################################
# Crear tabla y página de edición de puntos.
################################################################################
# Crear objeto donde se colocará la tabla de equipos.
tabla_equipos = TablaEquipos(tabla, conexion, puntos)

ancho_pagina = leer_ancho_pagina()

# Fijamos el ancho mínimo de la ventana igual al áncho mínimo de la tabla de
# equipos.
ventana_principal.minsize(tabla_equipos.ancho+ancho_pagina, 300)

################################################################################
# Configuración del grid de la ventana principal.
################################################################################
# Configuración del ajuste de tamaños.
ventana_principal.columnconfigure(0, weight=1, minsize=tabla_equipos.ancho)
ventana_principal.columnconfigure(1, weight=5, minsize=ancho_pagina)
ventana_principal.rowconfigure(1, weight=1)

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
