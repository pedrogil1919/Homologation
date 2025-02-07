'''
Created on 3 feb 2025

@author: pedrogil
'''


import tkinter


class Tabla(object):

    def __init__(self, marco, cabecera, datos, ancho, ajuste, alto_cabecera,
                 alto_datos, fuente_cabecera, fuente_datos):
        """
        Construye una tabla, y la rellena con los datos aportados.

        parámetros:
        - marco: marco de tkinter donde se construirá la tabla.
        - cabecera: textos para la cabecera. Será una lista con tantos elementos
          como columnas deba tener la tabla.
        - tabla: datos para el resto de la tabla. Será una lista, donde cada
          elemento será una lista con tantos elementos como los que tenía la
          cabecera. 
        - ancho: ancho mínimo para cada una de las columnas.
        - ajuste: indica que, si la tabla se hace más grande que la suma de los
          anchos mínimos, cómo se reparte el espacio sobrante:
          - 0: No se redimensiona.
          - 1: Se redimensiona completamente.
          - valores entre 0 y 1: hace que el reparto sea proporcional entre
            cada una de las columnas que tienen un valor distinto de 0.
        - alto_cabecera
        - alto_filas
        - fuente_cabecera
        - fuente_filas

        NOTA: Antes de construir la tabla, se chequea que todos los parámetros
        anteriores tengan el mismo número de elementos. Si no es así, se
        lanza una excepción de tipo ValueError.

        """

        self.marco = marco
        self.ancho = ancho
        self.alto_datos = alto_datos
        self.fuente_datos = fuente_datos
        # Comprobamos que todos los argumentos tengan el mismo número de
        # elementos.
        total = len(cabecera)
        if len(ancho) != total:
            raise ValueError(
                "Error tabla: lista de anchos de columnas incorrecta")
        if len(ajuste) != total:
            raise ValueError(
                "Error tabla: lista de ajustes de columnas incorrecta")

        # Construimos un marco para la cabecera
        marco_cabecera = tkinter.Frame(self.marco, bg="black")
        marco_cabecera.grid(row=0, column=0, sticky="nsew")
        # Construimos otro marco para el resto de datos:
        marco_canvas = tkinter.Frame(self.marco, bg="yellow")
        marco_canvas.grid(row=1, column=0, sticky="nsew")
        # marco_canvas.pack(fill=tkinter.BOTH, expand=True)

        # Adapto el ancho del grid al tamaño del contenedor.
        marco.columnconfigure(index=0, weight=1)
        # Respecto a la altura, fijamos una altura para la cabecera
        # y el resto lo debe ocupar la parte de los datos.
        marco.rowconfigure(index=0, minsize=alto_cabecera)
        marco.rowconfigure(index=1, minsize=15, weight=1)

        # Creamos un Canvas para añadir la barra de desplazamiento vertical
        canvas = tkinter.Canvas(marco_canvas, bg="blue")
        canvas.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=True)
        # Añadimos la barra de deslizamiento.
        barra = tkinter.Scrollbar(
            marco_canvas, orient=tkinter.VERTICAL, command=canvas.yview)
        barra.pack(side=tkinter.RIGHT, fill=tkinter.Y)

        canvas.config(yscrollcommand=barra.set)

        self.marco_tabla = tkinter.Frame(canvas)
        canvas.create_window((0, 0), window=self.marco_tabla,
                             anchor="nw", tags="frame")

        # Guardamos la lista de etiquetas que representan las celdas, para
        # poder acceder a ellas en todo momento.
        self.controles = {}
        for fila, valores in datos.items():
            self.añadir_fila(fila, valores)

        # Dentro de la cabecera añadimos los datos.
        for n, dato in enumerate(cabecera):
            marco_aux = tkinter.Frame(
                marco_cabecera, width=self.ancho[n], height=alto_cabecera)
            marco_aux.grid(row=0, column=n, sticky="nsew", padx=1, pady=1)
            marco_aux.pack_propagate(False)
            etiqueta_aux = tkinter.Label(
                marco_aux, bg="blue", text=dato, font=fuente_cabecera)
            etiqueta_aux.pack(fill="both", expand=True)

        # Configuramos ambos marcos para que se redimensionen de la misma
        # forma, y por tanto, todas las columntas tengan el mismo tamaño.
        # Ajustamos los anchos de las columnas para la cabecera.
        for i in range(len(ancho)):
            marco_cabecera.columnconfigure(i, weight=ajuste[i])
        # y lo mismo para el resto de celdas.
        for i in range(len(ancho)):
            self.marco_tabla.columnconfigure(i, weight=ajuste[i])

        # Guardamos el ancho actual del marco, que se corresponderá con el
        # ancho mínimo, para que la ventana contenedora se ajuste su valor
        # míimo a esta medida.
        self.marco.update_idletasks()
        self.ancho_tabla = self.marco.winfo_width()

        # Actualizar el tamaño del canvas cuando el contenido cambie
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # canvas.config(width=self.marco_tabla.winfo_width())  # Establecer el ancho del Canvas al ancho del Frame

        self.marco_tabla.bind("<Configure>", on_frame_configure)

        def onCanvasConfigure(e):
            canvas.itemconfig('frame', width=canvas.winfo_width())

        canvas.bind("<Configure>", onCanvasConfigure)

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
        s1 = set(self.controles.keys())
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

        if fila in self.controles:
            raise ValueError("Fila repetida")

        fila_celdas = []
        fila_marcos = []
        for col, dato in enumerate(valores):
            marco_celda = tkinter.Frame(
                self.marco_tabla, width=self.ancho[col], height=self.alto_datos)
            marco_celda.grid(
                row=fila, column=col, sticky="nsew", padx=1, pady=1)
            marco_celda.pack_propagate(False)
            etiqueta_celda = tkinter.Label(
                marco_celda, bg="gray", text=dato, font=self.fuente_datos)
            etiqueta_celda.pack(fill="both", expand=True)

            fila_celdas += [etiqueta_celda]
            fila_marcos += [marco_celda]
        self.controles[fila] = {"L": fila_celdas, "F": fila_marcos}

    def borrar_fila(self, fila):
        try:
            controles = self.controles[fila]
        except KeyError:
            return
        for control in controles['F']:
            control.destroy()
        del self.controles[fila]

    def refrescar_fila(self, fila, valores):
        try:
            controles = self.controles[fila]
        except KeyError:
            raise ValueError("Fila a actualizar no existe.")

        for control, dato in zip(controles['L'], valores):
            control.config(text=dato)

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
