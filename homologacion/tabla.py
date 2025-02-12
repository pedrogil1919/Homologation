'''
Created on 3 feb 2025

Definición de la estructura de tabla para mostrar resultados de vistas de la
base de datos.

@author: pedrogil
'''


from functools import partial
import sys
import tkinter


COLOR_BORDE = "black"


class Tabla(object):

    def __init__(self, marco, cabecera, ancho, ajuste, alineacion, alto_cabecera,
                 alto_datos, fuente_cabecera=None, fuente_datos=None):
        """
        Construcción de la tabla, y configuración.

        parámetros:
        - marco: marco de tkinter donde se construirá la tabla. La tabla se
          ajustará al tamaño de dicho marco.
        - cabecera: textos para la cabecera. Será una lista con tantos elementos
          como columnas deba tener la tabla.
        - anchos: ancho mínimo en píxeles para cada una de las columnas.
        - ajuste: indica, si la tabla se hace más grande que la suma de los
          anchos mínimos, cómo se reparte el espacio sobrante:
          - 0: No se redimensiona.
          - 1: Se redimensiona completamente.
          - valores entre 0 y 1: hace que el reparto sea proporcional entre
            cada una de las columnas que tienen un valor distinto de 0.
        - alineacion: alineación del texto para cada columna (izquierda,
          derecha, centrado).
        - alto_cabecera, en pixeles
        - alto_filas, en píxeles
        - fuente_cabecera (familia, tamaño, atributos)
        - fuente_datos (familia, tamaño, atributos)

        NOTA: Antes de construir la tabla, se chequea que todos los parámetros
        anteriores tengan el mismo número de elementos. Si no es así, se
        lanza una excepción de tipo ValueError.

        """

        # Guardamos los datos de configuración de la tabla.
        # Ancho de las columnas.
        self.ancho = ancho
        # Guardamos la altura de las filas.
        self.alto_datos = alto_datos
        self.alto_cabecera = alto_cabecera
        # Y las fuentes para los textos.
        self.fuente_datos = fuente_datos
        self.fuente_cabecera = fuente_cabecera
        # Guardamos la forma de alinear el texto de las etiquetas.
        self.alineacion = alineacion
        # Comprobamos que todos los argumentos tengan el mismo número de
        # elementos.
        self.columnas = len(ancho)
        if len(ajuste) != self.columnas:
            raise ValueError(
                "Error tabla: lista de ajustes de columnas incorrecta")
        if len(alineacion) != self.columnas:
            raise ValueError(
                "Error tabla: lista de alineación de columnas incorrecta")

        # Construimos un marco para la cabecera
        marco_cabecera = tkinter.Frame(marco, bg=COLOR_BORDE)
        marco_cabecera.grid(row=0, column=0, sticky="nsew")
        # Construimos otro marco para las filas de datos:
        marco_canvas = tkinter.Frame(marco, bg=COLOR_BORDE)
        marco_canvas.grid(row=1, column=0, sticky="nsew")

        # Adaptamos el ancho del grid al tamaño del contenedor.
        marco.columnconfigure(index=0, weight=1)
        # Respecto a la altura, fijamos una altura para la cabecera
        # y el resto lo debe ocupar la parte de los datos.
        marco.rowconfigure(index=0, minsize=alto_cabecera)
        marco.rowconfigure(index=1, minsize=self.alto_datos, weight=1)

        # Creamos un Canvas para añadir la barra de desplazamiento vertical
        canvas = tkinter.Canvas(marco_canvas, bg=COLOR_BORDE)
        # Añadimos la barra de deslizamiento.
        barra = tkinter.Scrollbar(
            marco_canvas, orient=tkinter.VERTICAL, command=canvas.yview)

        # Ponemos el canvas a la izquierda del marco anterior.
        canvas.grid(row=0, column=0, sticky="nsew")
        # Y ponemos la barra de desplazamiento a la izquierda.
        barra.grid(row=0, column=1, sticky="ns")
        marco_canvas.columnconfigure(0, weight=1)
        marco_canvas.columnconfigure(1, minsize=barra.winfo_reqwidth())
        marco_canvas.rowconfigure(0, weight=1)
        #  Esta instrucción permite que el elemento central del scroll (thumb)
        # se desplace de acuerdo a la parte visible de la tabla.
        canvas.config(yscrollcommand=barra.set)

        # Finalmente, construimos el marco donde crearemos la tabla con las
        # filas de datos.
        self.marco_tabla = tkinter.Frame(canvas, bg=COLOR_BORDE)
        canvas.create_window(
            (0, 0), window=self.marco_tabla, anchor="nw", tags="frame")

        # Dentro de la cabecera añadimos los datos.
        for col, dato in enumerate(cabecera):
            # NOTA: En todos los casos, cada celda está formada por un marco
            # de tamaño inicial indicado. Esto es necesario, porque es la única
            # forma que tenemos de especificar el tamaño en píxeles. Si
            # fijásemos el tamaño de las etiquetas, estas vienen en función del
            # tamaño de la fuente, y por lo tanto puede variar entre la
            # cabecera y el reseto de filas.
            marco_aux = tkinter.Frame(
                marco_cabecera, width=self.ancho[col], height=alto_cabecera)
            marco_aux.grid(row=0, column=col, sticky="nsew", padx=1, pady=1)
            # Esta instrucción hace que el marco no se expanda si se expande
            # su contenido, en este caso, en función del texto de la celda.
            marco_aux.pack_propagate(False)
            # Y añadimos la etiqueta a la cabecera.
            etiqueta_aux = tkinter.Label(
                marco_aux, bg="blue", text=dato, font=fuente_cabecera)
            etiqueta_aux.pack(fill="both", expand=True)

            # Ajustamos los anchos de las columnas para las filas.
            self.marco_tabla.columnconfigure(col, weight=ajuste[col])
            # Ajustamos los anchos de las columnas para la cabecera.
            marco_cabecera.columnconfigure(col, weight=ajuste[col])
        # Añadimos una última columna, del tamaño de la barra de desplazamiento,
        # para que conserven el mismo tamaño la cabecera y el resto de filas.
        marco_cabecera.columnconfigure(
            self.columnas, minsize=barra.winfo_reqwidth(), weight=0)

        # Guardamos el ancho actual del marco, que se corresponderá con el
        # ancho mínimo, para que la ventana contenedora se ajuste su valor
        # mínimo a esta medida.
        marco.update_idletasks()
        self.__ancho_tabla = marco_cabecera.winfo_reqwidth()

        def teclas_cursor(event):
            if event.keysym == "Up":
                canvas.yview_scroll(-1, "units")  # Mover hacia arriba
            elif event.keysym == "Down":
                canvas.yview_scroll(1, "units")  # Mover hacia abajo

        def rueda_raton(event):
            if sys.platform == "Windows":  # Windows
                canvas.yview_scroll(-int(event.delta / 120), "units")
            elif sys.platform == "Darwin":  # macOS
                canvas.yview_scroll(-int(event.delta), "units")
            elif sys.platform == "linux" or sys.platform == "linux2":  # Linux
                if event.num == 4:
                    canvas.yview_scroll(-1, "units")  # Scroll up
                elif event.num == 5:
                    canvas.yview_scroll(1, "units")  # Scroll down
        # # Actualizar el tamaño del canvas cuando el contenido cambie

        def actualizar_tamaño(__):
            r = canvas.bbox("frame")
            # NOTA: Comenzamos la región en 1, para evitar que salga una línea
            # blanca en la parte superior de la tabla.
            canvas.configure(scrollregion=(0, 1, r[2], r[3]))
            canvas.itemconfig('frame', width=canvas.winfo_width())

            # Si el Frame es más pequeño que el Canvas, deshabilita el scroll
            if self.marco_tabla.winfo_height() <= canvas.winfo_height():
                # Deshabilita el scroll con la rueda del ratón
                canvas.unbind_all("<MouseWheel>")
                canvas.unbind_all("<Button-4>")
                canvas.unbind_all("<Button-5>")
                canvas.unbind_all("<Up>")  # Flecha arriba
                canvas.unbind_all("<Down>")  # Flecha arriba
                # Desconecta la barra de desplazamiento
                canvas.config(yscrollcommand="")
                barra.grid_forget()  # Oculta la barra de desplazamiento
            else:
                if sys.platform == "linux" or sys.platform == "linux2":
                    canvas.bind_all("<Button-4>", rueda_raton)
                    canvas.bind_all("<Button-5>", rueda_raton)
                elif sys.platform == "win32" or "darwin":
                    canvas.bind_all("<MouseWheel>", rueda_raton)
                canvas.bind_all("<Up>", teclas_cursor)  # Flecha arriba
                canvas.bind_all("<Down>", teclas_cursor)  # Flecha arriba
                # Conecta la barra de desplazamiento
                canvas.config(yscrollcommand=barra.set)
                barra.grid(row=0, column=1, sticky="ns")

        self.marco_tabla.bind("<Configure>", actualizar_tamaño)
        canvas.bind("<Configure>", actualizar_tamaño)

        # Guardamos la lista de etiquetas que representan las celdas, para
        # poder acceder a ellas cuando queramos actualizar o borrar filas.
        self.__controles = {}
        # Creamos una lista de todos los eventos que tenemos que añaidr e las
        # celdas de las tablas.
        self.__eventos = {}

    def refrescar(self, datos):
        """
        Actualizar los datos de la tabla. La función debe recibir los datos
        en un formato similar al descrito en la función formatear_lista_tabla.
        La función determina que filas han desaparecido y que filas aparecen
        para eliminarlas / añadirlas. Para el resto de filas, actualiza los
        valores de las etiquetas.

        """
        # Determinamos las filas que existn en datos y no en controles, es
        # decir, las nuevas filas añadidas. Para ello, convertimos los
        # diccionarios en sets.
        s1 = set(self.__controles.keys())
        s2 = set(datos.keys())
        añadir = s2 - s1
        borrar = s1 - s2
        actualizar = s1 & s2
        # Borramos las filas que desaparecen:
        for f in borrar:
            self.borrar_fila(f)

        # Añadimos las nuevas filas:
        for f in añadir:
            self.añadir_fila(f, datos[f])

        # Actualizamos el resto de filas.
        for f in actualizar:
            self.refrescar_fila(f, datos[f])

    def añadir_fila(self, fila, valores):

        if fila in self.__controles:
            raise ValueError("Fila repetida")

        if len(valores) != self.columnas:
            raise ValueError(
                "Error añadir fila: número de datos incorrecto")

        fila_celdas = []
        fila_marcos = []
        for col, dato in enumerate(valores):
            marco_celda = tkinter.Frame(
                self.marco_tabla, width=self.ancho[col], height=self.alto_datos)
            marco_celda.grid(
                row=fila, column=col, sticky="nsew", padx=1, pady=1)
            marco_celda.pack_propagate(False)
            etiqueta_celda = tkinter.Label(
                marco_celda, bg="gray", text=dato, font=self.fuente_datos,
                anchor=self.alineacion[col], padx=10)
            # self.alineacion[col])
            etiqueta_celda.pack(fill=tkinter.BOTH, expand=True)
            for ev in self.__eventos.get(col, []):
                evento = ev[0]
                funcion = ev[1]
                etiqueta_celda.bind(evento, partial(funcion, fila, col))

            fila_celdas += [etiqueta_celda]
            fila_marcos += [marco_celda]
        self.__controles[fila] = {"L": fila_celdas, "F": fila_marcos}

    def borrar_fila(self, fila):
        try:
            controles = self.__controles[fila]
        except KeyError:
            return
        for control in controles['F']:
            control.destroy()
        del self.__controles[fila]

    def refrescar_fila(self, fila, valores):
        try:
            controles = self.__controles[fila]
        except KeyError:
            raise ValueError("Fila a actualizar no existe.")

        for control, dato in zip(controles['L'], valores):
            control.config(text=dato)

    def añadir_evento(self, evento, columna, funcion):
        """
        Añade un evento en una columna determinada para todas las filas
        existentes y las nuevas a añadir.

        """
        try:
            self.__eventos[columna] += [(evento, funcion)]
        except KeyError:
            self.__eventos[columna] = [(evento, funcion)]

        for fila, controles in self.__controles.items():
            controles['L'][columna].bind(
                evento, partial(funcion, fila, columna))

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

    def get_ancho_tabla(self):
        return self.__ancho_tabla

    ancho_tabla = property(get_ancho_tabla, None, None, None)
