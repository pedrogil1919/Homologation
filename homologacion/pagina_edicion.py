'''
Created on 14 feb 2025

Módulo para construir la página donde nos aparecerán todos los puntos de
homologación, en función de la zona y el equipo.

@author: pedrogil
'''

from functools import partial
import tkinter

COLOR_SI = "PaleGreen1"
COLOR_NO = "coral1"


class Pagina(object):

    def __init__(self, desbloquear, marco, conexion, fila, zona):

        self.__desbloquear = desbloquear
        self.__marco = marco
        # Construimos una etiqueta para incluir el nombre del equipo.
        self.__conexion = conexion
        self.__zona = zona
        self.__equipo, nombre = conexion.datos_equipo(fila)
        tkinter.Label(marco, text=nombre, height=1).grid(
            row=0, column=0, sticky="nsew")

        pagina = tkinter.Frame(marco, bg="gray90")
        pagina.grid(row=1, column=0, sticky="nsew")

        botones = tkinter.Frame(marco, bg="gray90")
        botones.grid(row=2, column=0, sticky="nsew")

        tkinter.Button(botones, text="Cancelar", command=self.cancelar).pack(
            side=tkinter.RIGHT, padx=10, pady=10)
        tkinter.Button(botones, text="Guardar", command=self.guardar).pack(
            side=tkinter.RIGHT, padx=10, pady=10)

        marco.columnconfigure(index=0, weight=1)
        marco.rowconfigure(index=0, weight=0)
        marco.rowconfigure(index=1, weight=1)
        marco.rowconfigure(index=2, weight=0)

        lista_puntos = conexion.lista_puntos_homologacion(
            self.__equipo, self.__zona)
        for elemento in lista_puntos:
            color = COLOR_SI if elemento["valor"] == 0 else COLOR_NO
            etiqueta = tkinter.Label(
                pagina, text=elemento["descripcion"], bg=color)
            etiqueta.pack(fill=tkinter.X, expand=False)
            punto = elemento["ID_HOMOLOGACION_PUNTO"]
            etiqueta.bind("<Button-1>", partial(
                self.actualizar_punto, punto, etiqueta))

        self.__conexion.abrir_transaccion()

    def actualizar_punto(self, punto, etiqueta, evento=None):
        valor = self.__conexion.actualizar_putno_homologacion(
            self.__equipo, punto, self.__zona)
        color = COLOR_SI if valor == 0 else COLOR_NO
        etiqueta.config(bg=color)

    def guardar(self):
        self.__conexion.cerrar_transaccion()
        for control in self.__marco.winfo_children():
            control.destroy()
        self.__desbloquear()

    def cancelar(self):
        self.__conexion.cancelar_transaccion()
        for control in self.__marco.winfo_children():
            control.destroy()
        self.__desbloquear()
