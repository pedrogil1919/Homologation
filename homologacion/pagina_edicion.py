'''
Created on 14 feb 2025

Módulo para construir la página donde nos aparecerán todos los puntos de
homologación, en función de la zona y el equipo.

@author: pedrogil
'''

from functools import partial
import tkinter

import mariadb


COLOR_SI = "PaleGreen1"
COLOR_NO = "coral1"


class Pagina(object):

    def __init__(self, desbloquear, marco, conexion, fila, zona):
        """
        Argumentos:
        - desbloquear: Función, si es necesaria, para desbloquear al módulo
          llamante, ya que inicialmente, esta página está pensada para bloquear
          al módulo llamante mientras no la cerremos.
        - marco: Frame de tkinter donde construir la página
        - conexion
        - fila: fila de la tabla a editar
        - zona: zona de homologación a editar.

        """
        # Guardamos la referencia a la función que habrá que llamar cuando
        # cerremos la ventana.
        self.__desbloquear = desbloquear
        # Guardamos la referencia a la base de datos.
        self.__conexion = conexion
        # Y el marco y la zona que estamos editando.
        self.__marco = marco
        self.__zona = zona

        # Obtenemos el nombre y el dorsal del equipo.
        self.__equipo, nombre = conexion.datos_equipo(fila)
        # Construimos una cabecera para incluir el nombre del equipo.
        cabecera = "%s (Zona %s)" % (nombre, zona)
        tkinter.Label(marco, text=cabecera, height=1).grid(
            row=0, column=0, sticky="nsew")

        # Construimos el marco donde mostrar todos los puntos a homologar.
        pagina = tkinter.Frame(marco, bg="gray90")
        pagina.grid(row=1, column=0, sticky="nsew")

        # Y añadimos dos botones en la parte inferior de la página.
        botones = tkinter.Frame(marco, bg="gray90")
        botones.grid(row=2, column=0, sticky="nsew")

        tkinter.Button(botones, text="Cancelar", command=self.cancelar).pack(
            side=tkinter.RIGHT, padx=10, pady=10)
        tkinter.Button(botones, text="Guardar", command=self.guardar).pack(
            side=tkinter.RIGHT, padx=10, pady=10)

        # Ajustamos para que todo el espacio sobrante lo ocupe el marco que
        # mostrará los puntos de homologación.
        marco.columnconfigure(index=0, weight=1)
        marco.rowconfigure(index=0, weight=0)
        marco.rowconfigure(index=1, weight=1)
        marco.rowconfigure(index=2, weight=0)

        # Obtenemos la lita de puntos a homologar.
        lista_puntos = conexion.lista_puntos_homologacion(
            self.__equipo, self.__zona)
        # Los añadimos al marco cada uno debajo del anterior.
        for elemento in lista_puntos:
            # Obtenemos el color de fondo en función de si el punto está
            # suprado o no.
            color = COLOR_SI if elemento["valor"] == 0 else COLOR_NO
            etiqueta = tkinter.Label(
                pagina, text=elemento["descripcion"], bg=color,
                anchor="w", padx=15, pady=5)
            etiqueta.pack(fill=tkinter.X, expand=False)
            # Asociamos el evento del ratón con la función que permite cambiar
            # el estado del punto.
            punto = elemento["ID_HOMOLOGACION_PUNTO"]
            etiqueta.bind("<Button-1>", partial(
                self.actualizar_punto, punto, etiqueta))

        # En el caso de la edición de páginas, lo hacemos mediante transacción,
        # por lo que sólo es posible actualizar la base de datos pulsando el
        # botón guardar.
        self.__conexion.abrir_transaccion()

    def actualizar_punto(self, punto, etiqueta, evento=None):
        """
        Alterna el valor de un punto de homologación.

        """
        # Alternamos el valor del punto de homologación.
        try:
            valor = self.__conexion.actualizar_punto_homologacion(
                self.__equipo, punto, self.__zona)
        except mariadb.OperationalError as e:
            tkinter.messagebox.showerror("Error en los datos del equipo", e)
        # Y al mismo tiempo determinamos el color con el que representarlo en
        # la página.
        color = COLOR_SI if valor == 0 else COLOR_NO
        etiqueta.config(bg=color)

    def guardar(self):
        """
        Guardar todos los datos realizados hasta el momento y finalizar.

        """
        self.__conexion.cerrar_transaccion()
        for control in self.__marco.winfo_children():
            control.destroy()
        # Lanzamos el evento de desbloqueo del módulo llamante.
        self.__desbloquear()

    def cancelar(self):
        """
        Cancelar todos los datos realizados hasta el momento y finalizar.

        """
        self.__conexion.cancelar_transaccion()
        for control in self.__marco.winfo_children():
            control.destroy()
        # Lanzamos el evento de desbloqueo del módulo llamante.
        self.__desbloquear()
