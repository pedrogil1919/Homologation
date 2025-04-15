'''
Created on 3 feb 2025

Módulo principal para realizar la homologación de los equipos.

@author: pedrogil
'''

import sys
import time
from tkinter import PhotoImage
import tkinter

from leer_constantes import abrir_archivo_xml, leer_ancho_pagina
from leer_constantes import leer_logos
from leer_datos_conexion import abrir_xml_conexion, leer_conexion
from modelo.base_datos import Conexion
from vista.tabla_equipos import TablaEquipos
from vista.ventana_inicio import crear_ventana_inicio

class CapturarError:
    """
    Copiado de tkinter.CallWrapper

    Añadido para poder sacar un mensaje al usuario y poder terminar la
    aplicación en caso de excepción inesperada. Esto altera el funcionamiento
    normal de gestión de excepciones, que imprime el mensaje en la consola pero
    no finaliza la aplicación, por lo que es complicado darse cuenta del error,
    sobre todo si tenemos la ventana principal encima de la consola.

    """

    def __init__(self, func, subst, widget):
        self.func = func
        self.subst = subst
        self.widget = widget

    def __call__(self, *args):
        """Apply first function SUBST to arguments, than FUNC."""
        try:
            if self.subst:
                args = self.subst(*args)
            return self.func(*args)
        except Exception:
            self.widget._report_exception()
            raise

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
    abrir_xml_conexion("../entrada.xml")
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

# Captura de errores dentro de la interfaz gráfica. (ver comentario justo antes
#   del mainloop). La función CapturarError está definida en el módulo errores.
# IMPORTANTE: Esta llamada tiene que estar definida antes de crear ningún
# control de la ventana, si se hace después, no atenderá a los errores
# producidos en dichos controles.
tkinter.CallWrapper = CapturarError

ventana_principal.title("Homologación Eurobot Spain")
# Abrimos el icono para la ventana.
datos_logos = leer_logos()
icono = tkinter.PhotoImage(file=datos_logos["ICONO"])
ventana_principal.iconphoto(True, icono)

# Creamos una cabecera para la aplicación.
cabecera = tkinter.Frame(ventana_principal)
cabecera.grid(row=0, column=0, sticky="nsew")

# Agregar imagen dentro del Frame usando Label
imagenes = leer_logos()
imagen_cabecera = PhotoImage(file=imagenes["CABECERA"])
tkinter.Label(cabecera, image=imagen_cabecera).pack(padx=10, pady=10)

# Creamos un marco donde colocar la tabla
tabla = tkinter.Frame(ventana_principal, bg="yellow")
tabla.grid(row=1, column=0, sticky="nsew")

# Creamos otro marco al lado derecho donde incluiremos los elementos para
# crear la página de edición de puntos de homologación.
area = tkinter.Frame(ventana_principal)
area.grid(row=0, column=1, sticky="nsew", rowspan=2)

# Creamos un marco donde aparecerán los puntos de homologación. La llamada a la
# función pack se hace dentro de la clase TablaEquipos, en función de si
# estamos editando un equipo o se encuentra vacía.
puntos = tkinter.Frame(area)
# Y añadimos otro marco con el fondo, para mostrar cuando no estamos mostrando
# ningún equipo.
fondo = tkinter.Frame(area)
area.columnconfigure(0, weight=1)
area.rowconfigure(0, weight=1)
imagen_logo = PhotoImage(file=imagenes["LOGO"])
tkinter.Label(fondo, borderwidth=0, image=imagen_logo).pack(expand=True)

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
tabla_equipos = TablaEquipos(tabla, conexion, puntos, fondo)

ancho_pagina = leer_ancho_pagina()

# Fijamos el ancho mínimo de la ventana igual al áncho mínimo de la tabla de
# equipos más el ancho requerido para la página de edición de puntos.
ventana_principal.minsize(tabla_equipos.ancho+ancho_pagina, 300)

################################################################################
# Configuración del grid de la ventana principal.
################################################################################
# Configuración del ajuste de tamaños.
ventana_principal.columnconfigure(0, weight=0, minsize=tabla_equipos.ancho)
ventana_principal.columnconfigure(1, weight=1, minsize=ancho_pagina)
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

try:
    ventana_principal.mainloop()
except Exception as e:
    tkinter.messagebox.showerror("Error", "%s. Se cerrará la aplicación." % e)
