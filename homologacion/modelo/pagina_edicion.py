'''
Created on 14 feb 2025

Módulo para construir la página donde nos aparecerán todos los puntos de
homologación, en función de la zona y el equipo, y el campo comentario

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
        Genera la página con sus puntos de homologación

        Al construir la página, se añaden todos los puntos, junto con sus
        secciones, y les asigna el color y los oculta o desoculta en función
        de su valor.

        Argumentos:
        - marco: Frame de tkinter donde construir la página
        - conexion
        - fila: índice del equipo que estamos editando.
        - zona: zona de homologación que estamos editando.
        - desbloquear: Función, si es necesaria, para desbloquear al módulo
          llamante, ya que inicialmente, esta página está pensada para bloquear
          al módulo llamante mientras no la cerremos. Esta función es llamada
          justo al finalizar la edición de esta página. Si el módulo llamante
          no se bloquea, se puede pasar None. La función debe devolver True si
          se sigue adelante con el desbloqueo, o False si no (por ejemplo, por
          que el usuario ha cancelado la operación).
        - color_punto: función que devuelve el color de un punto en función de
          su valor. Toma como argumento dos enteros, el valor del punto, y el
          nivel de sección, y devuelve un color de tkinter.
        - color_borde: color de los bordes entre etiquetas
        - margen_x, margen_y: margen para el texto de las etiquetas (píxeles)
        - indentacion: indentación para separar entre diferentes niveles de
          sección (píxeles)

        """
        ########################################################################
        ########################################################################
        # Guardamos:
        # la referencia a la función que habrá que llamar cuando
        # cerremos la ventana.
        self.__desbloquear = desbloquear
        # la referencia a la base de datos.
        self.__conexion = conexion
        # la referencia la marco donde insertar las etiquetas de los puntos.
        self.__marco = marco
        # el número de zona que estamos editando.
        self.__zona = zona
        # Fijamos el ancho de la indentacion de etiquetas. Se trata de un
        # parámetro global, así que lo fijamos a nivel de clase.
        Etiqueta.indentacion = indentacion
        # Y también fijamos la función que determina el color de la etiqueta,
        # que también es global a todos los objetos.
        Etiqueta.funcion_color = staticmethod(color_punto)
        ########################################################################
        ########################################################################

        # Obtenemos el nombre y el dorsal del equipo.
        self.__dorsal, nombre = conexion.datos_equipo(fila)

        # Obtenemos la lista de puntos a homologar, y los comentarios.
        # NOTA: realizamos la consulta en este punto, antes de construir la
        # interfaz, ya que es posible que el equipo esté bloquedo por otro
        # usuario, y no podamos continuar.
        lista_puntos, comentario = self.__conexion.lista_puntos_homologacion(
            self.__dorsal, self.__zona)

        ########################################################################
        ########################################################################
        # Construimos una cabecera para incluir el nombre del equipo.
        cabecera = "(%i) %s - Zona %s" % (self.__dorsal, nombre, zona)
        fuente, color_fuente = leer_fuente("pagina")
        tkinter.Label(
            self.__marco, text=cabecera, height=1, font=fuente,
            fg=color_fuente).grid(row=0, column=0, sticky="nsew", pady=5)

        # Otro marco donde mostrar los puntos de homologación.
        marco_canvas = tkinter.Frame(self.__marco)
        marco_canvas.grid(row=1, column=0, sticky="nsew")

        fuente, color_fuente = leer_fuente("coment")
        # Añadimos un campo de texto para incluir comentarios.
        self.__campo_comentarios = tkinter.Text(
            self.__marco, height=4, font=fuente, fg=color_fuente, wrap="word")
        self.__campo_comentarios.grid(
            row=3, column=0, sticky="nsew", padx=10, pady=(1, 10))
        fuente = (fuente[0], fuente[1], "bold")
        tkinter.Label(self.__marco, text="Comentarios:",
                      font=fuente, fg=color_fuente).grid(
            row=2, column=0, sticky="w", padx=20, pady=(10, 1))

        # Asociamos el evento de pérdida de foco a guardar el texto que haya en
        # ese momento en el campo.
        self.__campo_comentarios.bind(
            "<FocusOut>", self.__guardar_comentario)
        # Asociamos la tecla enter del tecldo interno y externo a perder el
        # foco, de tal forma que provoca la ejecución del código anterior, y da
        # el foco al botón de guardar.
        self.__campo_comentarios.bind("<Return>", self.__campo_perder_foco)
        self.__campo_comentarios.bind("<KP_Enter>", self.__campo_perder_foco)
        # A asociamos la tecla Tab también a perder el foco, evitando que se
        # introduzca un tabulador en el texto. Esto permite utilizar la tecla
        # Tab para altarnar entre los 2 botones y el campo de comentarios.
        self.__campo_comentarios.bind("<Tab>", self.__campo_perder_foco)
        # Aprovechamos cuando el campo de comentarios coja el foco para anular
        # el desplazamiento de los puntos, y así podemos hacer scrollo sobre el
        # campo de texto.
        self.__campo_comentarios.bind("<FocusIn>", self.__campo_ganar_foco)

        # Iniciamos el campo con el texto que tuviera ya el campo en la bd.
        if comentario is not None:
            self.__campo_comentarios.insert("1.0", comentario)

        # Y añadimos un marco con dos botones en la parte inferior de la página.
        botones = tkinter.Frame(self.__marco)
        botones.grid(row=4, column=0, sticky="nsew")

        # Creamos los dos botones. Aquí es importante crear el botón de guardar
        # el primero, para que la secuencia del Tab de el foco primero al botón
        # guardar, ya que si da primero al de cancelar, puede dar lugar a
        # confusiones al usuario.
        self.__boton_guardar = tkinter.Button(
            botones, text="Guardar", command=self.__guardar)
        self.__boton_cancelar = tkinter.Button(
            botones, text="Cancelar", command=self.__cancelar)

        self.__boton_cancelar.pack(side=tkinter.RIGHT, padx=10, pady=10)
        self.__boton_guardar.pack(side=tkinter.RIGHT, padx=10, pady=10)

        self.__boton_cancelar.bind("<Return>", self.__cancelar)
        self.__boton_guardar.bind("<Return>", self.__guardar)
        self.__boton_cancelar.bind("<KP_Enter>", self.__cancelar)
        self.__boton_guardar.bind("<KP_Enter>", self.__guardar)
        self.__boton_guardar.focus_set()

        ########################################################################
        ########################################################################
        # Ajustamos para que todo el espacio sobrante lo ocupe el marco que
        # mostrará los puntos de homologación.
        self.__marco.rowconfigure(index=0, weight=0)
        self.__marco.rowconfigure(index=1, weight=1)
        self.__marco.rowconfigure(index=2, weight=0)
        self.__marco.rowconfigure(index=3, weight=0)
        self.__marco.rowconfigure(index=4, weight=0)
        # Y se ocupe toda el espacio en horizontal.
        self.__marco.columnconfigure(index=0, weight=1)

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
        # y lo añadimos dentro del canvas para que se pueda hacer scroll cuando
        # el número de etiquetas sea grande.
        self.__canvas.create_window(
            (1, 1), window=self.__pagina, anchor="nw", tags="frame")

        ########################################################################
        ########################################################################
        # Construcción de la página con las etiquetas de los puntos.
        # Leemos la fuente que emplearemos para los puntos.
        fuente, color_fuente = leer_fuente("puntos")

        # Creamos una lista temporal con todas las etiquetas, para poder
        # ocultar y desocultarlas en función del valor de su sección. Como las
        # etiquetas irán asignadas a los eventos de las propias etiquetas, no
        # es necesario conservar una copia global de todas las etiquetas.
        lista_etiquetas = {}

        # Iteramos sobre todos los puntos de hommologación (ver definición del
        # generador __lis_puntos para más detalles).
        for elemento, fila, descendientes, numero in self.__lista_puntos(lista_puntos):
            # Obtenemos los datos del registro de la base de datos
            # correspondiente a este punto.
            punto = elemento["FK_HOMOLOGACION_PUNTO"]
            nivel = elemento["nivel"]
            valor = elemento["valor"]
            seccion = elemento["seccion"]

            # Asociamos el evento del ratón con la función que permite cambiar
            # el estado del punto.

            # Antes de crear y añadir la etiqueta al marco, comprobamos si se
            # trata de una sección o un punto normal.
            seccion = elemento["seccion"]
            if seccion == 0:
                # Si se trata de una sección:
                # Primero obtenemos las etiquetas que dependen de esta. Tened en
                # cuenta que de acuerdo al proceso de ordenación de los puntos
                # que realiza el generador de este bucle, los puntos
                # dependientes se generan antes que la sección de la que
                # depende, y por lo tanto, aquí ya tendremos las etiquetas
                # construidas que necesitamos, aunque no estén construidas
                # todas.
                lista_etiquetas_desc = [
                    v for k, v in lista_etiquetas.items() if k in descendientes]
                # Definimos el tipoo de evento para las etiquetas. En caso de
                # tratarse de una sección, le asignamos el doble click.
                evento = "<Double-1>"
            else:
                # En caso de ser un punto, no tendrá descendientes.
                lista_etiquetas_desc = None
                # Si se trata de un punto, le asignamos el click.
                evento = "<Button-1>"

            # Construimos la etiqueta para este punto.
            etiqueta = Etiqueta(
                self.__pagina, punto, fila, nivel, seccion, valor,
                lista_etiquetas_desc,
                text="%s-%s" % (numero, elemento["descripcion"]),
                font=fuente, fg=color_fuente,
                anchor="w", justify=tkinter.LEFT, pady=margen_y, padx=margen_x)
            # Actualizamos la apariencia de la etiqueta en función de su valor.
            etiqueta.actualizar(valor)
            # Asignamos el evento del ratón para que se actualice su valor.
            # NOTA: En función de si es punto o sección, el evento se activa
            # con click o doble click.
            etiqueta.bind(evento, partial(
                self.__actualizar_punto, punto, etiqueta))

            # Añadimos la etiqueta a la lista global, por si hay que asignarla
            # para otra etiqueta de nivel superior
            lista_etiquetas[fila] = etiqueta

        # Hacemos que el ancho del marco que contiene a los puntos tome todo el
        # tamaño sobrante de la ventana.
        self.__pagina.columnconfigure(0, weight=1)

        # Ajustamos el evento de cambio de tamaño del canvas, por si la ventana
        # que lo contiene se hace más grande.
        self.__canvas.bind("<Configure>", self.__actualizar_tamaño)
        # y el tamaño del marco que contiene las etiquetas, que ocurre al
        # activar u ocultar una sección.
        self.__pagina.bind("<Configure>",  self.__actualizar_tamaño)

        # Añadimos un módulo para implementar las funciones de desplazamiento
        # vertical de la página si el número de puntos a revisar es elevado y
        # no coge en la ventana.
        self.__vertical = Desplazamiento(
            self.__canvas, self.__pagina, self.__barra)

################################################################################
################################################################################
    def __guardar(self, evento=None):
        """
        Guardar todos los datos realizados hasta el momento y finalizar.

        """
        try:
            # Antes de finalizar, comprobamos si el usuario quiere guardar,
            # o bien se ha confundido.
            if not self.__desbloquear("¿Guardar datos?"):
                # En caso de que el usuario no quiera guardar, salimos y
                # esperamos a que el usuario vuelva a pulsar alguno de los
                # botones.
                return
        except Exception:
            # Es posible que el módulo llamante no nos pase ninguna función, ya
            # que no necesita bloquearse. En ese caso, simplemente ignoramos
            # la función.
            pass
        # NOTA: Si el usuario pulsa Guardar sin hacer que el campo de
        # comentarios pierda el foco, es posible que no se haya guardado los
        # comentarios.
        self.__boton_guardar.focus_set()
        self.__conexion.guardar()
        for control in self.__marco.winfo_children():
            control.destroy()
        # Lanzamos el evento de desbloqueo del módulo llamante.

    def __cancelar(self, evento=None):
        """
        Cancelar todos los datos realizados hasta el momento y finalizar.

        """
        # Lanzamos el evento de desbloqueo del módulo llamante.
        try:
            if not self.__desbloquear("¿Cancelar modificaciones?"):
                return
        except Exception:
            pass
        self.__conexion.cancelar()
        for control in self.__marco.winfo_children():
            control.destroy()

    def __campo_ganar_foco(self, evento=None):
        # Anulamos el desplazamiento vertical de la tabla de puntos, para
        # poder hacer scroll sobre el propio campo.

        self.__vertical.desp_vertical = False

    def __campo_perder_foco(self, evento=None):
        """
        Guardar comentario cuando el campo pierde el foco.

        """
        # Devolvemos el desplazamiento vertical a la tabla de puntos.
        self.__vertical.desp_vertical = True
        self.__boton_guardar.focus_set()
        # Con esta instrucción, evitamos que si hemos llegado aquí al
        # haber pulsado la tecla Tab, se incluya un tabulador en el texto.
        return "break"

    def __guardar_comentario(self, evento=None):
        """
        Guardar los comentarios en la base de datos.

        """
        comentario = self.__campo_comentarios.get("1.0", "end-1c")
        self.__conexion.actualizar_comentario(
            self.__dorsal, self.__zona, comentario)

################################################################################
################################################################################

    def __lista_puntos(self, lista):
        """
        Devuelve la lista de puntos para la página

        La lista de puntos debe llevar el formato de la vista
        Homologacion_ListaPuntos, cuyo orden es (equipo, zona, nivel, seccion,
        punto) y devuelve un generador que itera sobre todos los puntos. Los
        valores devueltos son:
        - registro de la vista de la base de datos
        - numero de orden (ver nota debajo)
        - registros de niveles inferiores que son dependientes de éste (sección)
        - numeración de la sección, subsección, etc, del tipo 1.1.2

        """
        # Convertimos la lista de puntos, en un diccionario de listas de puntos,
        # separadas por niveles. Recordemos que la lista viene ordenada por
        # "nivel" antes que por "seccion" y "punto".
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

        # En este punto, tenemos la lista completa separada en varias listas,
        # tantas como distintos niveles tengamos, donde la primera lista sería
        # la de nivel 1, y así sucesivamente.
        # Y a continuación, implementamos un generador que devuelve el número
        # de fila al que le corresponde en función de su posición y de los
        # descendientes que tenga éste.
        # NOTA: Esto no es posible obtenerlo de forma simple con SQL, por eso
        # se hace en este punto.
        yield from self.__lista_puntos_jerarquico(lista_aux, 1)

    def __lista_puntos_jerarquico(self, listas, indice, prefijo="", seccion=None):
        """
        Generador recursivo, para devolver el orden de cada punto.

        El generador toma la lista de listas de puntos, ordenadas por nivel
        de sección, y devuelve el número de orden en función de su posición y
        de sus descendientes, y los descendientes de este.

        NOTA: El orden en el que se devuelven los datos no es el orden que le
        corresponde en la tabla. En general, se devuelven antes los
        descendientes que el propio elemento. Por lo tanto, el número de orden
        debe emplearse para ordenarlos.

        Para comprender este generador, se debe consultar también la tabla
        HomologacionPunto y la vista Homologacion_ListaPuntos

        Argumentos:
        - listas: ver arriba
        - indice: número de orden actual, para poder numerar cada punto con su
          número de orden correcto.
        - prefijo: valor actual del número de sección, como una cadena de texto,
          a la cual se le añade el número de la subsección correspondiente.
        - seccion: cuando estamos recorriendo todos los elementos de una
          sección, este argumento nos vale para saber si este punto pertenece
          a esta sección o no.

        """
        # Variable para llevar la numeración de la subsección en la que nos
        # encontramos.
        orden = 1
        # Recorremos todos los elementos de la lista actual.
        for elemento in listas[0]:
            # Comprobamos si este punto pertenece a la sección que estamos
            # recorriendo, ya que en cada lista, tenemos todos los puntos de
            # un mismo nivel para todas las secciones existentes.
            # Seccion None sólo ocurre para los puntos de primer nivel.
            if seccion is None or elemento["FK_HOMOLOGACION_SECCION"] == seccion:
                # Componemos el número de la sección, añadiendo el número de
                # subsección al prefijo de la sección que lo contiene.
                numero = "%s%s." % (prefijo, orden)
                # La variable ultimo nos permite saber cual es el último indice
                # asignado, para poder numerar los siguientes puntos a partir
                # de este.
                ultimo = indice
                # Necesitamos generar también la lista de puntos que son
                # descendientes de esta sección.
                desc = []
                # si se trata de una sección:
                if elemento["seccion"] == 0:
                    # Recorremos todos los puntos del siguiente nivel, para
                    # comprobar cuales pertenecen a esta sección.
                    for e, i, h, n in self.__lista_puntos_jerarquico(
                            listas[1:], indice + 1, numero,
                            elemento["FK_HOMOLOGACION_PUNTO"]):
                        # Devolvemos el elemento, el índice y la lista de
                        # descendientes de este punto.
                        # Generamos el texto para el número de sección.
                        yield e, i, h, n
                        # Y añadimos el nuevo elemento a la lista de
                        # descendientes de esta sección.
                        desc += [i]
                        # Además, tomamos nota del valor más alto añadido, ya
                        # que para el siguiente punto deberemos empezar a
                        # numerar a continuación de éste.
                        if i > ultimo:
                            ultimo = i
                yield elemento, indice, desc, numero
                orden += 1
                # Y avanzamos el índice tantas unidades como puntos hayamos
                # devuelto para esta sección.
                indice = ultimo + 1

    def __actualizar_punto(self, punto, etiqueta, evento=None):
        """
        Alterna el valor de un punto de homologación entre True y False 

        """
        # En caso de que hayamos perdido el desplazamiento vertical de la
        # tabla de puntos, ddams el foco de nuevo al botón de guardar. De esta
        # forma, se ejecuta el código para habilitar el desplazamiento a la
        # tabla de puntos, y se guarda cualquier modificación del comentario.
        # Además, al dar el foco al botón, ya no se volverá a deshabilitar el
        # desplazamiento hasta que no se vuelva a entrar al campo de
        # comentarios.
        if not self.__vertical.desp_vertical:
            self.__boton_guardar.focus_set()

        # Alternamos el valor del punto de homologación.
        try:
            valor = self.__conexion.actualizar_punto_homologacion(
                self.__dorsal, punto, self.__zona)
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
            else:
                raise e
            return

        # Actualizamos la apariencia de la etiqueta, y de sus descendientes si
        # los tuviera.
        etiqueta.actualizar(valor)
        # Y también comprobamos si el tamaño de todo el marco ha cambiado, en
        # caso de que alguna sección haya hecho aparecer o desaparecer
        # etiquetas.
        self.__actualizar_tamaño()

    def __actualizar_tamaño(self, evento=None):
        """
        Actualizar los tamaños y funciones de scroll del canvas.

        """
        # Actualizamos la página, para que se recalcule el espacio requerido
        # una vez se sepa el número de líneas que ocupa cada etiqueta.
        self.__pagina.update_idletasks()
        # Fijamos el area de scroll del canvas.
        r = self.__canvas.bbox("frame")
        self.__canvas.configure(scrollregion=(1, 1, r[2], r[3]))

        # Ajustamos la altura del marco que contiene las etiquetas para
        # adaptarnos al número de etiquetas visibles en este momento.
        altura = self.__pagina.winfo_reqheight()
        self.__canvas.itemconfig('frame', height=altura)

        # Ajustamos el ancho del frame que contiene las etiquetas al mismo
        # ancho que el canvas que lo contiene.
        ancho = self.__canvas.winfo_width()
        self.__canvas.itemconfig('frame', width=ancho)

        # Ajustamos el parámetro wrraplength para que las etiquetas sean
        # multilinea para aquellos puntos que tengan el texto muy largo.
        # NOTA: hay que tener en cuenta que el ancho de la etiqueta es igual
        # a la longitud del texto, más el margen (padx * 2).
        for control in self.__pagina.winfo_children():
            ancho_etiqueta = control.winfo_width()
            control.config(wraplength=ancho_etiqueta - 2*control["padx"])

        # Actualizamos la página, para que se recalcule el espacio requerido
        # una vez se sepa el número de líneas que ocupa cada etiqueta.
        self.__pagina.update_idletasks()
        # Comprobamos si debemos habilitar o no las funciones de desplazamiento
        # vetical de la página.
        self.__vertical.desp_vertical = True

    def get_equipo(self):
        return self.__dorsal

    equipo = property(get_equipo, None, None, None)
