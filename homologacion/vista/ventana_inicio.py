'''
Created on 10 may 2024

Visualizar una ventana de inicio con el logo de la competición.

@author: pedrogil
'''

from PIL import Image, ImageTk
import tkinter
import screeninfo

from leer_constantes import leer_ventana_inicio, leer_conexion, leer_fuente


def crear_ventana_inicio():
    # Leemos en primer lugar los datos del servidor del archivo de configuración
    servidor = leer_conexion()
    # Y leemos los datos para mostrar la ventana de inicio.
    directorio, imagen, tiempo = leer_ventana_inicio()
    # directorio = leer_ventana_inicio()
    # Creamos la splash window para mostrar mientras abrimos la conexión.
    splash_window = tkinter.Tk()
    # Eliminar los bordes de la ventana y cargar la imagen de inicio.
    splash_window.overrideredirect(True)
    splash_image = ImageTk.PhotoImage(Image.open(directorio+imagen))
    splash_label = tkinter.Label(splash_window, image=splash_image)
    splash_label.pack()
    servidor_label = tkinter.Label(
        splash_window, text="Conectando con %s..." % servidor["HOST"],
        font=leer_fuente())
    servidor_label.pack()
    # Centrar la ventana en la pantalla.
    monitor = screeninfo.get_monitors()
    ancho_pantalla = monitor[0].width
    alto_pantalla = monitor[0].height
    ancho_ventana = splash_label.winfo_reqwidth()
    alto_ventana = splash_label.winfo_reqheight()

    x = (ancho_pantalla-ancho_ventana)/2
    y = (alto_pantalla-alto_ventana)/2
    splash_window.geometry("+%i+%i" % (x, y))
    splash_window.update()
    return splash_window, tiempo
################################################################################
