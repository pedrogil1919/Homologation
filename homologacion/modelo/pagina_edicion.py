'''
Created on 14 feb 2025

Módulo para construir la página donde nos aparecerán todos los puntos de
homologación, en función de la zona y el equipo.

@author: pedrogil
'''

from functools import partial
import tkinter

import mariadb

from leer_constantes import leer_fuente
from modelo.desplazamiento_tabla import Desplazamiento
from modelo.etiqueta_punto import Etiqueta


class Pagina(object):

    def __init__(self, marco, conexion, fila, zona,
                 desbloquear, color_punto, color_borde="black",
                 margen_x=10, margen_y=5, indentacion=10):
        """
        Argumentos:
        - marco: Frame de tkinter donde construir la página
        - conexion
        - fila: fila de la tabla a editar
        - zona: zona de homologación a editar.
        - desbloquear: Función, si es necesaria, para desbloquear al módulo
          llamante, ya que inicialmente, esta página está pensada para bloquear
          al módulo llamante mientras no la cerremos.
        - color_punto: función que devuelve el color de un punto en función de
          su valor. Toma como argumento un entero, y devuelve un color

        """
        # Guardamos la referencia a la función que habrá que llamar cuando
        # cerremos la ventana.
        self.__desbloquear = desbloquear
        # Guardamos la referencia a la base de datos.
        self.__conexion = conexion
        self.__marco = marco
        # Y el número de zona que estamos editando.
        self.__zona = zona
        # Ancho de la indentacion de etiquetas
        Etiqueta.indentacion = indentacion
        Etiqueta.funcion_color = staticmethod(color_punto)
        # Función que determina el color de una etiqueta en función de su valor.
        self.__color_punto = color_punto
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
        fuente, color_fuente = leer_fuente("pagina")
        tkinter.Label(
            self.__marco, text=cabecera, height=1, font=fuente,
            fg=color_fuente).grid(row=0, column=0, sticky="nsew")
        # Otro marco donde mostrar los puntos de homologación.
        marco_canvas = tkinter.Frame(self.__marco)
        marco_canvas.grid(row=1, column=0, sticky="nsew")
        # Y añadimos un marco con dos botones en la parte inferior de la página.
        botones = tkinter.Frame(self.__marco)
        botones.grid(row=2, column=0, sticky="nsew")

        b1 = tkinter.Button(botones, text="Cancelar", command=self.cancelar)
        b2 = tkinter.Button(botones, text="Guardar", command=self.guardar)

        b1.pack(side=tkinter.RIGHT, padx=10, pady=10)
        b2.pack(side=tkinter.RIGHT, padx=10, pady=10)

        b1.bind("<Return>", lambda __: self.cancelar())
        b2.bind("<Return>", lambda __: self.guardar())
        b1.bind("<KP_Enter>", lambda __: self.cancelar())
        b2.bind("<KP_Enter>", lambda __: self.guardar())
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
        self.__canvas = tkinter.Canvas(marco_canvas)
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
        self.__pagina = tkinter.Frame(self.__canvas, bg=color_borde)
        self.__canvas.create_window(
            (1, 1), window=self.__pagina, anchor="nw", tags="frame")

        fuente, color_fuente = leer_fuente("puntos")

        # Creamos una lista temporal con todas las etiquetas, para poder
        # ocultar y desocultarlas en función del valor de su sección.
        lista_etiquetas = {}

        for elemento, fila, desc in self.__lista_puntos(lista_puntos):
            elemento["fila"] = fila
            punto = elemento["FK_HOMOLOGACION_PUNTO"]
            nivel = elemento["nivel"]
            valor = elemento["valor"]
            seccion = elemento["seccion"]

            # self.__añadir_etiqueta(etiqueta, fila, nivel)
            # Asociamos el evento del ratón con la función que permite cambiar
            # el estado del punto.
            seccion = elemento["seccion"]
            if seccion == 0:
                # Primero obtenemos las etiquetas que dependen de esta. Tened en
                # cuenta que de acuerdo al proceso de ordenación de los puntos
                # que realiza el generador de este bucle, los puntos
                # dependientes se generan antes que la sección de la que
                # depende, y por lo tanto, aquí ya tendremos las etiquetas
                # construidas.
                lista_etiquetas_desc = [
                    v for k, v in lista_etiquetas.items() if k in desc]
            else:
                lista_etiquetas_desc = None

            # Obtenemos el color de fondo en función de si el punto está
            # validado o no, o se trata de una sección.
            # color = self.__color_punto(valor, seccion)

            etiqueta = Etiqueta(
                self.__pagina, punto, fila, nivel, seccion, valor,
                lista_etiquetas_desc,
                text=elemento["descripcion"],
                font=fuente, fg=color_fuente,
                anchor="w", justify=tkinter.LEFT, pady=margen_y, padx=margen_x)

            etiqueta.actualizar(valor)
            etiqueta.bind("<Button-1>", partial(
                self.__actualizar_punto, punto, seccion, etiqueta))

            lista_etiquetas[fila] = etiqueta

        self.__pagina.columnconfigure(0, weight=1)
        self.__canvas.bind("<Configure>", self.__actualizar_tamaño)
        self.__pagina.bind("<Configure>",  self.__actualizar_tamaño)

        # Añadimos un módulo para implementar las funciones de desplazamiento
        # vertical de la página si el número de puntos a revisar es elevado y
        # no coge en la ventana.
        self.__vertical = Desplazamiento(
            self.__canvas, self.__pagina, self.__barra)

    def __lista_puntos(self, lista):
        """
        Devuelve la lista de puntos para la página

        La lista de puntos debe llevar el formato de la vista
        Homologacion_ListaPuntos, cuyo orden es (equipo, zona, nivel, seccion,
        punto) y devuelve un generador que itera sobre todos los puntos. Los
        valores devueltos son:
        - registro de la vista anterior
        - numero de orden (ver nota debajo)
        - número de registros subsigientes que son dependientes de éste.

        """
        # Convertimos la lista de puntos, en un diccionario de listas de puntos,
        # separadas por niveles.
        lista_aux = []
        actual = 0
        nivel_actual = lista[0]["nivel"]
        for indice, elemento in enumerate(lista):
            if elemento["nivel"] == nivel_actual:
                continue
            lista_aux += [lista[actual:indice]]
            nivel_actual = elemento["nivel"]
            actual = indice
        # El último nivel de la lista hay que generarlo fuera ya del bucle.
        lista_aux += [lista[actual:indice+1]]
        for el, ind, desc in self.__lista_puntos_jerarquico(lista_aux, 1):
            yield el, ind, desc

    def __lista_puntos_jerarquico(self, listas, indice, seccion=None):
        """
        Generador que toma una lista devuelta por la vista ListaPuntos, cuyo
        orden es (nivel, seccion, punto), y las devuelve colocando después de
        cada sección, los puntos que dependen de dicha sección.

        """
        for elemento in listas[0]:
            if seccion is None or elemento["FK_HOMOLOGACION_SECCION"] == seccion:
                ultimo = indice
                desc = []
                if elemento["seccion"] == 0:
                    for e, i, h in self.__lista_puntos_jerarquico(
                            listas[1:], indice + 1,
                            elemento["FK_HOMOLOGACION_PUNTO"]):
                        yield e, i, h
                        if i > ultimo:
                            ultimo = i
                        desc += [i]
                yield elemento, indice, desc
                indice = ultimo + 1

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
    def __actualizar_punto(self, punto, seccion, etiqueta, evento=None):
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

        etiqueta.actualizar(valor)
        self.__actualizar_tamaño()

    def __actualizar_tamaño(self, evento=None):

        # Actualizamos la página, para que se recalcule el espacio requerido
        # una vez se sepa el número de líneas que ocupa cada etiqueta.
        self.__pagina.update_idletasks()
        # Fijamos el area de scroll del canvas.
        r = self.__canvas.bbox("frame")
        self.__canvas.configure(scrollregion=(2, 2, r[2], r[3]))

        # Comprobamos si debemos habilitar o no las funciones de desplazamiento
        # vetical de la página.
        self.__vertical.desp_vertical = True

        altura = self.__pagina.winfo_reqheight()
        # Y la altura de la página, ya que no se ajusta solo.
        self.__canvas.itemconfig('frame', height=altura)

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

    def get_equipo(self):
        return self.__equipo

    equipo = property(get_equipo, None, None, None)
