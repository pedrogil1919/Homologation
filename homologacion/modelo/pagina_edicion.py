'''
Created on 14 feb 2025

Módulo para construir la página donde nos aparecerán todos los puntos de
homologación, en función de la zona y el equipo.

@author: pedrogil
'''

from functools import partial
import tkinter

import mariadb

from modelo.desplazamiento_tabla import Desplazamiento


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
        self.__marco = marco
        # Y el número de zona que estamos editando.
        self.__zona = zona

        # Obtenemos el nombre y el dorsal del equipo.
        self.__equipo, nombre = conexion.datos_equipo(fila)

        # Obtenemos la lista de puntos a homologar.
        # NOTA: realizamos la consulta en este punto, antes de construir la
        # interfaz, ya que es posible que el equipo esté bloquedo por otro
        # usuario, y no podamos continuar.
        lista_puntos = self.__conexion.lista_puntos_homologacion(
            self.__equipo, self.__zona)

        ########################################################################
        ########################################################################
        # Construimos una cabecera para incluir el nombre del equipo.
        cabecera = "(%i) %s - Zona %s" % (self.__equipo, nombre, zona)
        tkinter.Label(self.__marco, text=cabecera, height=1).grid(
            row=0, column=0, sticky="nsew")
        # Otro marco donde mostrar los puntos de homologación.
        marco_canvas = tkinter.Frame(self.__marco, bg="gray")
        marco_canvas.grid(row=1, column=0, sticky="nsew")
        # Y añadimos un marco con dos botones en la parte inferior de la página.
        botones = tkinter.Frame(self.__marco, bg="gray90")
        botones.grid(row=2, column=0, sticky="nsew")

        b1 = tkinter.Button(botones, text="Cancelar", command=self.cancelar)
        b2 = tkinter.Button(botones, text="Guardar", command=self.guardar)

        b1.pack(side=tkinter.RIGHT, padx=10, pady=10)
        b2.pack(side=tkinter.RIGHT, padx=10, pady=10)

        b1.bind("<Return>", lambda __: self.cancelar())
        b2.bind("<Return>", lambda __: self.guardar())
        b2.focus_set()

        # Ajustamos para que todo el espacio sobrante lo ocupe el marco que
        # mostrará los puntos de homologación.
        self.__marco.columnconfigure(index=0, weight=1)
        self.__marco.rowconfigure(index=0, weight=0)
        self.__marco.rowconfigure(index=1, weight=1)
        self.__marco.rowconfigure(index=2, weight=0)
        ########################################################################
        ########################################################################
        # Creamos un canvas para que se pueda añadir una barra de desplazamiento
        # vertical cuando el número de puntos sea grande.
        self.__canvas = tkinter.Canvas(marco_canvas, bg="blue")
        self.__canvas.grid(row=0, column=0, sticky="nsew")
        self.__barra = tkinter.Scrollbar(
            marco_canvas, orient=tkinter.VERTICAL, command=self.__canvas.yview)
        self.__barra.grid(row=0, column=1, sticky="ns")
        self.__canvas.config(yscrollcommand=self.__barra.set)

        # Adaptamos el ancho de todo esto al del marco donde lo hemos colocado.
        marco_canvas.rowconfigure(0, weight=1)
        # Y para las columnas, la que contiene la barra de desplazamiento debe
        # tener una anchura fija,
        marco_canvas.columnconfigure(1, minsize=self.__barra.winfo_reqwidth())
        # Y el resto se lo queda el marco que contiene los datos.
        marco_canvas.columnconfigure(0, weight=1)
        ########################################################################
        ########################################################################

        # Construimos el marco donde mostrar todos los puntos a homologar.
        self.__pagina = tkinter.Frame(self.__canvas, bg="yellow")
        self.__canvas.create_window(
            (1, 1), window=self.__pagina, anchor="nw", tags="frame")

        # Los añadimos al marco cada uno debajo del anterior.
        for fila, elemento in enumerate(lista_puntos):
            # Obtenemos el color de fondo en función de si el punto está
            # suprado o no.
            color = COLOR_SI if elemento["valor"] == 0 else COLOR_NO
            etiqueta = tkinter.Label(
                self.__pagina, text=elemento["descripcion"], bg=color,
                anchor="w", justify=tkinter.LEFT, padx=10, pady=5)
            etiqueta.grid(row=fila, column=0, sticky="nsew", pady=1)

            # Asociamos el evento del ratón con la función que permite cambiar
            # el estado del punto.
            punto = elemento["ID_HOMOLOGACION_PUNTO"]
            etiqueta.bind("<Button-1>", partial(
                self.__actualizar_punto, punto, etiqueta))

        self.__pagina.columnconfigure(0, weight=1)
        self.__canvas.bind("<Configure>", self.__actualizar_tamaño)

        # Añadimos un módulo para implementar las funciones de desplazamiento
        # vertical de la página si el número de puntos a revisar es elevado y
        # no coge en la ventana.
        self.__vertical = Desplazamiento(
            self.__canvas, self.__pagina, self.__barra)

    def guardar(self):
        """
        Guardar todos los datos realizados hasta el momento y finalizar.

        """
        self.__conexion.guardar()
        for control in self.__marco.winfo_children():
            control.destroy()
        # Lanzamos el evento de desbloqueo del módulo llamante.
        self.__desbloquear()

    def cancelar(self):
        """
        Cancelar todos los datos realizados hasta el momento y finalizar.

        """
        self.__conexion.cancelar()
        for control in self.__marco.winfo_children():
            control.destroy()
        # Lanzamos el evento de desbloqueo del módulo llamante.
        self.__desbloquear()

################################################################################
################################################################################
    def __actualizar_punto(self, punto, etiqueta, evento=None):
        """
        Alterna el valor de un punto de homologación.

        """
        # Alternamos el valor del punto de homologación.
        try:
            valor = self.__conexion.actualizar_punto_homologacion(
                self.__equipo, punto, self.__zona)
        except mariadb.OperationalError as e:
            if e.errno == 1205:
                # Time out:
                tkinter.messagebox.showerror(
                    "Tiempo de espera superado",
                    "Datos del equipo bloqueado por otro usuario. "
                    "Espere a que termine para poder edtirlo")
            elif e.errno == 1644:
                #
                tkinter.messagebox.showerror(
                    "Error en los datos del equipo", e)
            return
        # Y al mismo tiempo determinamos el color con el que representarlo en
        # la página.
        color = COLOR_SI if valor == 0 else COLOR_NO
        etiqueta.config(bg=color)

    def __actualizar_tamaño(self, evento=None):
        # Ajustamos el ancho del frame que contiene las etiquetas al mismo
        # ancho que el canvas que lo contiene.
        ancho = self.__canvas.winfo_width()
        self.__canvas.itemconfig('frame', width=ancho)
        # Ajustamos el parámetro wrraplength para que las etiquetas sean
        # multilinea para aquellos puntos que sean muy largos.
        # NOTA: hay que tener en cuenta que el ancho de la etiqueta es igual
        # a la longitud del texto, más el margen (padx * 2).
        for control in self.__pagina.winfo_children():
            control.config(wraplength=ancho - 2*control["padx"])

        # Actualizamos la página, para que se recalcule el espacio requerido
        # una vez se sepa el número de líneas que ocupa cada etiqueta.
        self.__pagina.update_idletasks()
        # Fijamos el area de scroll del canvas.
        r = self.__canvas.bbox("frame")
        self.__canvas.configure(scrollregion=(2, 2, r[2], r[3]))

        # Y la altura de la página, ya que no se ajusta solo.
        self.__canvas.itemconfig(
            'frame', height=self.__pagina.winfo_reqheight())

        # Comprobamos si debemos habilitar o no las funciones de desplazamiento
        # vetical de la página.
        self.__vertical.desp_vertical = True
