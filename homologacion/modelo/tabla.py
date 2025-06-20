'''
Created on 3 feb 2025

Definición de la estructura de tabla para mostrar resultados de vistas de la
base de datos.

La tabla se rellena con datos insertados dentro de un diccionario, donde la
clave del diccionario es un número entero que indica la fila donde se debe
introducir los datos de este elemento del diccionario.

La lista de claves puede estar incompleta, y no tienen por que venir en orden,
aunque la propia tabla, al representarlos, las ordena por dicha clave.

Por ejemplo:

datos = {
    1: [dato11, dato12, dato13],
    6: [dato61, dato62, dato63],
    4: [dato41, dato42, dato43]}
    
La tabla quedaría:
|------------------------|
|dato11 | dato12 | dato13|
|dato41 | dato42 | dato43|
|dato61 | dato62 | dato63|
|------------------------|

Entre los parámetros de la tabla figura el ancho, en píxeles, de cada columna.
Si el ancho es 0, significa que no se debe añadir esa columna.

@author: pedrogil
'''


from functools import partial
import tkinter

from modelo.desplazamiento_tabla import Desplazamiento

# Variable auxiliar para convertir códigos de alinación con los códigos
# requiridos por el argumento anchor de tkinter.
ANCHOR = {
    "C": "center",
    "L": "w",
    "R": "e"}


class Tabla(object):

    def __init__(self, marco, cabecera,
                 ancho=(100,),
                 ajuste=(0,),
                 alineacion=("C",),
                 alto_cabecera=20,
                 alto_datos=20,
                 color_borde="black",
                 color_fondo="gray",
                 color_cabecera="blue",
                 color_filas="white",
                 fuente_cabecera=("LIBERATION SANS", 20, ""),
                 color_fuente_cabecera="black",
                 fuente_filas=("LIBERATION SANS", 12, ""),
                 color_fuente_filas="black"):
        """
        Construcción de la tabla, y configuración.

        parámetros:
        - marco: marco de tkinter donde se construirá la tabla. La tabla se
          ajustará al tamaño de dicho marco.
        - cabecera: textos para la cabecera. Será una lista con tantos elementos
          como columnas deba tener la tabla.
        - ancho: ancho mínimo en píxeles para cada una de las columnas.
        - ajuste: indica, si la tabla se hace más grande que la suma de los
          anchos mínimos, cómo se reparte el espacio sobrante:
          - 0: No se redimensiona.
          - 1: Se redimensiona completamente.
          - valores entre 0 y 1: hace que el reparto sea proporcional entre
            cada una de las columnas que tienen un valor distinto de 0.
        - alineacion: alineación del texto para cada columna (L, C, R).
        - alto_cabecera, en pixeles
        - alto_datos, en píxeles
        - color_xxx
        - fuente_cabecera (familia, tamaño, atributos)
        - fuente_datos (familia, tamaño, atributos)

        NOTA: Antes de construir la tabla, se chequea que todos los parámetros
        anteriores tengan el mismo número de elementos. Si no es así, se
        lanza una excepción de tipo ValueError.

        """
        # ancho, ajuste, alineacion,
        # alto_cabecera, alto_datos,

        # Guardamos los datos de configuración de la tabla que sean necesarios
        # fuera del constructor.
        # Ancho de las columnas.
        self.__ancho = ancho
        # Altura de las filas de los datos
        self.__alto_datos = alto_datos
        # Y las fuentes para los textos.
        self.__color_filas = color_filas
        self.__fuente_filas = fuente_filas
        self.__color_fuente_filas = color_fuente_filas
        # Guardamos la forma de alinear el texto de las etiquetas.
        self.__alineacion = alineacion
        # Comprobamos que todos los argumentos tengan el mismo número de
        # elementos.
        self.__columnas = len(ancho)
        if len(ajuste) != self.__columnas:
            raise ValueError(
                "Error tabla: lista de ajustes de columnas incorrecta")
        if len(alineacion) != self.__columnas:
            raise ValueError(
                "Error tabla: lista de alineación de columnas incorrecta")

        ########################################################################
        ########################################################################
        # Construimos un marco para la cabecera
        marco_cabecera = tkinter.Frame(marco, bg=color_borde)
        marco_cabecera.grid(row=0, column=0, sticky="nsew")
        # Construimos otro marco para las filas de datos:
        marco_canvas = tkinter.Frame(marco, bg=color_fondo)
        marco_canvas.grid(row=1, column=0, sticky="nsew")

        # Adaptamos el ancho del grid al tamaño del contenedor.
        marco.columnconfigure(index=0, weight=1)
        # Respecto a la altura, fijamos una altura para la cabecera
        # y el resto lo debe ocupar la parte de los datos.
        marco.rowconfigure(index=0, minsize=alto_cabecera, weight=0)
        marco.rowconfigure(index=1, weight=1)
        ########################################################################
        ########################################################################

        # Creamos un Canvas para que se pueda añadir una barra de desplazamiento
        # vertical cuando el número de filas sea grande.
        self.__canvas = tkinter.Canvas(marco_canvas, bg=color_fondo)
        # y lo ponemos a la izquierda del marco anterior.
        self.__canvas.grid(row=0, column=0, sticky="nsew")
        # Añadimos la barra de deslizamiento.
        self.__barra = tkinter.Scrollbar(
            marco_canvas, orient=tkinter.VERTICAL, command=self.__canvas.yview)
        # Y ponemos la barra de desplazamiento a la izquierda.
        self.__barra.grid(row=0, column=1, sticky="ns")
        #  Esta instrucción permite que el elemento central del scroll (thumb)
        # se desplace de acuerdo a la parte visible de la tabla.
        self.__canvas.config(yscrollcommand=self.__barra.set)

        # Adaptamos el ancho de todo esto al del marco donde lo hemos colocado.
        marco_canvas.rowconfigure(0, weight=1)
        # Y para las columnas, la que contiene la barra de desplazamiento debe
        # tener una anchura fija,
        marco_canvas.columnconfigure(1, minsize=self.__barra.winfo_reqwidth())
        # Y el resto se lo queda el marco que contiene los datos.
        marco_canvas.columnconfigure(0, weight=1)

        # Finalmente, construimos el marco donde crearemos la tabla con las
        # filas de datos.
        self.__marco_tabla = tkinter.Frame(self.__canvas, bg=color_borde)
        # Este marco debe ir dentro del canvas para que se pueda desplazar.
        self.__canvas.create_window(
            (1, 1), window=self.__marco_tabla, anchor="nw", tags="frame")

        # Creamos una lista para todos los campos de la cabecera, ya que
        # podemos necesitarla para añadir eventos u otras cosas a dichos
        # campos.
        self.__cabecera = {}

        # Dentro de la cabecera añadimos los datos.
        for col, dato in enumerate(cabecera):
            # NOTA: En todos los casos, cada celda está formada por un marco
            # de tamaño inicial indicado. Esto es necesario, porque es la única
            # forma que tenemos de especificar el tamaño en píxeles. Si
            # fijásemos el tamaño de las etiquetas, estas vienen en función del
            # tamaño de la fuente, y por lo tanto puede variar entre la
            # cabecera y el resto de filas.
            if ancho[col] == 0:
                # Si el ancho es 0, nos indican que no debemos añadir esta
                # columna.
                continue
            marco_aux = tkinter.Frame(
                marco_cabecera, width=self.__ancho[col], height=alto_cabecera)
            marco_aux.grid(row=0, column=col, sticky="nsew", padx=1, pady=1)
            # Esta instrucción hace que el marco no se expanda si se expande
            # su contenido, en este caso, en función del texto de la celda.
            marco_aux.pack_propagate(False)
            # Y añadimos la etiqueta a la cabecera.
            etiqueta_aux = tkinter.Label(
                marco_aux, bg=color_cabecera, fg=color_fuente_cabecera,
                text=dato, font=fuente_cabecera)
            etiqueta_aux.pack(fill=tkinter.BOTH, expand=True)
            # Añadimos la etiqueta a la lista de controles de la cabecera.
            self.__cabecera[col] = etiqueta_aux

            # Ajustamos los anchos de las columnas para las filas.
            self.__marco_tabla.columnconfigure(col, weight=ajuste[col])
            # Ajustamos los anchos de las columnas para la cabecera.
            marco_cabecera.columnconfigure(col, weight=ajuste[col])

        # Añadimos una última columna, del tamaño de la barra de desplazamiento,
        # para que conserven el mismo tamaño la cabecera y el resto de filas.
        marco_cabecera.columnconfigure(
            self.__columnas, minsize=self.__barra.winfo_reqwidth(), weight=0)

        # Guardamos el ancho actual del marco, que se corresponderá con el
        # ancho mínimo, para que la ventana contenedora se ajuste su valor
        # mínimo a esta medida.
        marco.update_idletasks()
        self.__ancho_tabla = marco_cabecera.winfo_reqwidth()

        # Asociamos eventos para que se ajuste todo cuando cambie el tamaño del
        # canvas (porque se ha redimensionado la ventana principal) o el marco
        # (porque se han añadido / quitado filas).
        self.__marco_tabla.bind("<Configure>", self.__actualizar_tamaño)
        self.__canvas.bind("<Configure>", self.__actualizar_tamaño)

        # Creamos un diccionario para guardar la lista de etiquetas que
        # representan las celdas, para poder acceder a ellas cuando queramos
        # actualizar o borrar filas.
        self.__controles = {}
        # Creamos una lista de todos los eventos que tenemos que añaidr en las
        # celdas de las tablas.
        self.__eventos = {}
        # Función para configurar el color de las celdas para cada columna.
        # Si para una columna concreta la clave no existe en el diccionario,
        # la celda se representará con el color por defecto.
        self.__color_columna = {}

        # Al iniciar la tabla, permitimos la activación del desplazamiento
        # vertical de la tabla.
        self.__vertical = Desplazamiento(
            self.__canvas, self.__marco_tabla, self.__barra)


################################################################################
################################################################################
    def refrescar(self, datos, solo_actualizar=False):
        """
        Actualizar los datos de la tabla. La función debe recibir los datos
        en un formato similar al descrito en la función formatear_lista_tabla.
        La función determina qué filas han desaparecido y qué filas aparecen
        para eliminarlas / añadirlas. Para el resto de filas, actualiza los
        valores de las etiquetas.

        La variable solo_actualizar indica que sólo hay que actualizar las
        filas pasadas como datos, no hay que eliminar o añadir nuevas fila.
        Esta opción es necesaria si queremos actualizar sólo unas filas sin
        necesidad de estar mandando el resto de filas que no deben ser
        refrescadas.

        """
        # Guardamos el total de filas que tenemos antes de añadir o eliminar
        # ninguna fila.
        total = len(self.__controles)
        # Determinamos las filas que existn en datos y no en controles, es
        # decir, las nuevas filas añadidas. Para ello, convertimos los
        # diccionarios en sets.
        s1 = set(self.__controles.keys())
        s2 = set(datos.keys())

        if not solo_actualizar:
            # Filas añadidas.
            añadir = s2 - s1
            # Filas eliminadas.
            borrar = s1 - s2
            # Borramos las filas que desaparecen:
            for f in borrar:
                self.borrar_fila(f)

            # Añadimos las nuevas filas:
            for f in añadir:
                self.añadir_fila(f, datos[f])

        # Resto de filas.
        actualizar = s1 & s2
        # Actualizamos el resto de filas.
        for f in actualizar:
            self.refrescar_fila(f, datos[f])

        # Solo si hay un cambio en el número de filas, refrescamos el tamaño
        # de la tabla, ya que en ocasiones la actualización no se produce.
        if len(self.__controles) != total:
            self.__marco_tabla.update_idletasks()
            self.__actualizar_tamaño()

    def añadir_fila(self, fila, valores):
        """
        Añadir una nueva fila. Implica crear los marcos y etiquetas asociadas.

        """
        # Comprobamos si la fila está repetida.
        if fila in self.__controles:
            raise ValueError("Fila repetida")

        if len(valores) != self.__columnas:
            raise ValueError(
                "Error añadir fila: número de columnas incorrecto")

        # Guardamos en sendos diccionarios los marcos y etiquetas que creamos
        # para representar la fila.
        fila_celdas = {}
        fila_marcos = {}
        for columna, dato in enumerate(valores):
            if self.__ancho[columna] == 0:
                # Si el ancho es 0, nos indican que no debemos añadir esta
                # columna
                continue
            # Creamos el marco que contendrá la etiqueta.
            marco_celda = tkinter.Frame(self.__marco_tabla,
                                        width=self.__ancho[columna],
                                        height=self.__alto_datos)
            marco_celda.grid(
                row=fila, column=columna, sticky="nsew", padx=1, pady=1)
            marco_celda.pack_propagate(False)
            # Y creamos la etiqueta dentro del marco anterior.
            etiqueta_celda = tkinter.Label(
                marco_celda, fg=self.__color_fuente_filas,
                text=dato, font=self.__fuente_filas,
                anchor=ANCHOR[self.__alineacion[columna]], padx=10)
            # Asighamos el color de la celda en función de la configuración
            self.__color_celda(fila, columna, etiqueta_celda)
            etiqueta_celda.pack(fill=tkinter.BOTH, expand=True)
            # comprobamos si hay que añadir también eventos a la etiqueta.
            for ev in self.__eventos.get(columna, []):
                # En este caso, el primer elemento incluye el nombre del
                # evento, y el segundo el noombre de la función.
                evento = ev[0]
                funcion = ev[1]
                etiqueta_celda.bind(evento, partial(funcion, fila))

            fila_celdas[columna] = etiqueta_celda
            fila_marcos[columna] = marco_celda
        # Actualizamos la lista de controles añadidos.
        self.__controles[fila] = {"L": fila_celdas, "F": fila_marcos}

    def borrar_fila(self, fila):
        """
        Elimina la fila indicada.

        """
        try:
            controles = self.__controles[fila]
        except KeyError:
            return
        # Eliminamos los controles de la interfaz, ya que sólo elimnandolos de
        # la lista no es suficiente para que desaparezcan.
        for control in controles['F'].values():
            control.destroy()
        del self.__controles[fila]

    def refrescar_fila(self, fila, valores):
        """
        Actualiza el texto de la fila indicada.

        """
        try:
            controles = self.__controles[fila]
        except KeyError:
            raise ValueError("Fila a actualizar no existe.")

        if len(valores) != self.__columnas:
            raise ValueError(
                "Error al actualizar fila: número de columnas incorrecto")

        etiquetas = controles['L']
        for columna in etiquetas:
            etiqueta = etiquetas[columna]
            # Asignamos el texto de la celda.
            valor = valores[columna]
            etiqueta.config(text=valor if valor is not None else "")
            # y su color, en fucnión del valor.
            self.__color_celda(fila, columna, etiqueta)

################################################################################
################################################################################
    def añadir_evento(self, evento, columna, funcion):
        """
        Añade un evento en una columna determinada para todas las filas
        existentes y las nuevas a añadir. El evento debe ser un string del tipo
        requerido por la función bind de tkinter (ej, "<Button-1>", "<Double-1>"

        """
        # TODO: Creo que esto no hace falta.
        # if self.__ancho[columna] == 0:
        #     # Si el ancho es 0, significa que no se ha añadido la columna,
        #     # por lo que tampoco añadiremos el evento.
        #     return
        try:
            # Para cada evento, guardamos el nombre del evento, y la función
            # asociada a dicho evento.
            self.__eventos[columna] += [(evento, funcion)]
        except KeyError:
            self.__eventos[columna] = [(evento, funcion)]

        # Asociamos el evento a todas las filas que ya estén añadidas. Se puede
        # comprobar que al añadir nuevas filas, a estás también se les añade el
        # evento.
        for fila, controles in self.__controles.items():
            controles['L'][columna].bind(
                evento, partial(funcion, fila))

    def añadir_evento_cabecera(self, evento, columna, funcion):
        """
        Añade un evento sobre el campo correspondiente a la cabecera (para más
        información, ver función añadir_evento).

        """
        self.__cabecera[columna].bind(evento, funcion)

    def definir_color_columna(self, columna, color, funcion=None):
        """
        Definir el color para representar una celda
        Argumentos:
        - columna: índice de la columna. El color se aplica a todas las celdas
          de esta columna.
        - color: código del color de tkinter por defecto para la celda
        - funcion: función que permite calcular el color de la celda en función
          del valor de esta. Debe ser una función que devuelva un código de
          color de tkinter

        La tabla asignará inicialmente el color devuelto por la función. Si
        el valor devuelto es None, o bien no existe la función, le asignará
        el color por defecto. Si la clave para una columna no existe, se le
        asignará el color por defecto de la tabla.

        """
        self.__color_columna[columna] = {
            'C': color,
            'F': funcion}

    @staticmethod
    def formatear_lista_tabla(datos):
        """
        Formatea los datos para que puedan ser cargados en la tabla. El formato
        de los datos de partida son una lista, donde cada elemento es una lista
        de datos, siendo el primer elemento un número entero que indica el
        orden (posición de la fila) donde mostrar el resto de datos.
        El resto de datos son los datos a mostrar.

        La función chequea que la longitud de todos los elementos de datos sea
        la misma. 

        """
        filas = {}
        if len(datos) == 0:
            return filas
        longitud = len(datos[0])
        for dato in datos:
            # Comprobamos que la longitud sea la misma.
            if len(dato) != longitud:
                raise ValueError(
                    "Tabla de datos incorrecta. Longitudes distintas")
            orden = dato[0]
            # Comprobamos que el índice no exista ya en la lista que llevamos
            # hasta ahora.
            if orden in filas:
                raise ValueError("Tabla de datos incorrecta. Índice repetido.")
            # Añadimos la nueva fila a la lista formateada.
            filas[orden] = dato[1:]
        return filas


################################################################################
################################################################################
    def __actualizar_tamaño(self, event=None):

        # Capturamos la altura actual del marco que contiene los datos,
        # para determinar la porción de tabla que se ve sobre la ventana.
        r = self.__canvas.bbox("frame")
        # NOTA: Comenzamos la región en 1, para evitar que salga una línea
        # blanca en la parte superior de la tabla.
        self.__canvas.configure(scrollregion=(2, 2, r[2], r[3]))

        # Si la tabla se queda sin datos, el tamaño del marco no se
        # actualiza, con lo que no se genera el evento de redimensionamiento
        # y por tanto no se queda con su altura igual a 0
        if len(self.__controles) == 0:
            # Fijamos su tamaño a 1 píxel, para que se siga representando
            # el borde.
            altura = 1
        else:
            # Fijamos su tamaño al ancho que requiere (si no hacemos esto,
            # una vez se ejecute la instrucción del if, siempre se queda
            # en tamaño igual a 1.
            altura = self.__marco_tabla.winfo_reqheight()

        self.__set_desp_vertical()

        self.__canvas.itemconfig('frame', height=altura)
        # Hacemos que el ancho del frame donde se crea la tabla se ajuste
        # al ancho del canvas donde lo hemos añadido.
        self.__canvas.itemconfig('frame', width=self.__canvas.winfo_width())

################################################################################
################################################################################

    def __color_celda(self, fila, columna, etiqueta):
        """
        Asigna el color para la celda correspondiente

        """
        # Comprobamos si el color para esta columna ha sido asignado.
        try:
            color_defecto = self.__color_columna[columna]['C']
            funcion = self.__color_columna[columna]['F']
        except KeyError:
            # En caso de que no exista, asignamos el color por defecto de la
            # tabla
            color = self.__color_filas
        else:
            # Comprobamos si tenemos una función para calcular el color de
            # la celda
            try:
                color = funcion(fila, columna, etiqueta["text"])
            except ValueError:
                color = color_defecto
            # TODO: fila_completa indica que hay que pintar de ese color toda la
            # fila, no solo la celda.
        etiqueta.config(bg=color)

    def __get_ancho_tabla(self):
        return self.__ancho_tabla

    def __set_desp_vertical(self, habilitar=None):
        self.__vertical.desp_vertical = habilitar

    ancho_tabla = property(__get_ancho_tabla, None, None, None)
    desp_vertical = property(None, __set_desp_vertical, None, None)
