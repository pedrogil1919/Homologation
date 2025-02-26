'''
Created on 18 feb 2025

Clase para gestionar los datos a mostrar en la tabla de equipos de la
aplicación.

También incluye las funciones para mostrar y editar los puntos de homologación
del equipo.

La clase accede a la lista de equipos de la base de datos, y los muestra en la
tabla.

El objeto puede tener dos estados:
- lectura: cuando estamos visualizando la lista de equipos, pero no estamos
  modificando ninguno de ellos. En este estado, se atienden los eventos
  generados por la tabla para entrar a editar los puntos de un equipo.
- escritura: cuando estamos editando los puntos de un equipo. En este estado,
  no es atienden los eventos de la tabla hasta que el usuario guarde o cancele
  la edición, y pasemos al estado lectura. 

@author: pedrogil
'''

import tkinter.messagebox

from leer_constantes import leer_cabecera
from modelo.base_datos import estado
from modelo.pagina_edicion import Pagina
from modelo.tabla import Tabla


FUENTE_CABECERA = ("LIBERATION SANS", 20, "")
FUENTE_DATOS = ("LIBERATION SANS", 15, "")


class TablaEquipos(object):
    '''

    '''

    def __init__(self, marco, conexion, puntos):
        '''
        Constructor

        Argumentos:
        - marco: marco de tkinter donde se construirá toda la interfaz gráfica
        - conexion.
        - puntos: marco auxiliar donde se mostrarán los puntos de homologacion.

        '''
        # Guardamos la conexión a la base de datos.
        self.__conexion = conexion
        # Guardamos el marco donde se mostrarán los puntos de homologación.
        self.__puntos = puntos

        # Creamos una cabecera para incluir los botones de cambio de pestaña.
        self.__pestañas = tkinter.Frame(marco)
        self.__pestañas.grid(row=0, column=0, sticky="nsew")
        # Cremos otro marco donde insertar la tabla.
        tabla = tkinter.Frame(marco)
        tabla.grid(row=1, column=0, sticky="nsew")
        # Configuramos para que toda la altura sobrante la ocupe el marco
        # de la tabla.
        marco.rowconfigure(index=0, weight=0)
        marco.rowconfigure(index=1, weight=1)
        marco.columnconfigure(index=0, weight=1)

        self.variable = tkinter.IntVar()
        self.variable.set(1)
        # Sobre la cabecera añadimos botones para cambiar entre los distintos
        # estados del equipo.
        tkinter.Radiobutton(self.__pestañas, text="Todos",
                            variable=self.variable, value=1,
                            indicatoron=0, width=10, height=1, padx=10, pady=10,
                            command=lambda: self.seleccionar_estado(
                                estado.TODOS)).pack(side=tkinter.LEFT)

        tkinter.Radiobutton(self.__pestañas, text="Inscritos",
                            variable=self.variable, value=2,
                            indicatoron=0, width=10, height=1, padx=10, pady=10,
                            command=lambda: self.seleccionar_estado(
                                estado.INSCRITO)).pack(side=tkinter.LEFT)

        tkinter.Radiobutton(self.__pestañas, text="Registrados",
                            variable=self.variable, value=3,
                            indicatoron=0, width=10, height=1, padx=10, pady=10,
                            command=lambda: self.seleccionar_estado(
                                estado.REGISTRADO)).pack(side=tkinter.LEFT)

        tkinter.Radiobutton(self.__pestañas, text="Homologados",
                            variable=self.variable, value=4,
                            indicatoron=0, width=10, height=1, padx=10, pady=10,
                            command=lambda: self.seleccionar_estado(
                                estado.HOMOLOGADO)).pack(side=tkinter.LEFT)

        # Obtenemos los datos de configuración de la cabecera desde la
        # base de datos.
        cabecera = leer_cabecera()
        columnas = self.__conexion.columnas()
        configuracion = Tabla.configuracion_columnas(columnas, cabecera)
        # Creamos la tabla, junto con su formato.
        self.__tabla_equipos = Tabla(
            tabla,
            configuracion["nombre"],
            configuracion["ancho"],
            configuracion["ajuste"],
            configuracion["alineacion"],
            50, 45, FUENTE_CABECERA, FUENTE_DATOS)

        def color_zona(fila, columna, valor):
            " Función para definir el color de las zonas de hommologación."
            try:
                return "green" if int(valor) == 0 else "red"
            except ValueError:
                return "white"

        # Configuración de eventos. La tabla de configuración de la base de
        # datos nos indica sobre qué columnas se deben ejecutar los eventos
        # de edición de puntos, y sobre que columnas los de cambio de registro.
        for columna, evento in enumerate(configuracion["eventos"]):
            if evento is None:
                continue
            elif evento == 0:
                # El código 0 se refiere a cambio de registro.
                self.__tabla_equipos.añadir_evento(
                    "<Double-1>", columna, self.registrar)
                # Asignamos la funcion que determina el color de la celda
                # del nombre del equipo.
                self.__tabla_equipos.definir_color_columna(
                    columna, "white", self.__color_equipo)
            else:
                # El resto de códigos se refieren al número de zona que debe
                # editar dicho evento.
                self.__tabla_equipos.añadir_evento(
                    "<Double-1>", columna,
                    self.editar_zona(evento)(self.editar_zona_aux))
                # Asignamos también las funciones para calcular el color de
                # la celda en función del valor de ésta.
                self.__tabla_equipos.definir_color_columna(
                    columna, "white", color_zona)

        # Inicialmente arrancamos la aplicación mostrando todos los equipos.
        # La llamada a esta función rellena por primera vez la tabla con datos.
        self.__estado_tabla = self.seleccionar_estado(estado.TODOS)

        # Guardamos en esta variable la referencia a la página que estamos
        # editando. Si es None, significa que estamos no estamos editando nada,
        # es decir, estamos en modo Lectura.
        self.__pagina_edicion = None
        # Variable temporal empleada por la función que determinar el color
        # de la columna con el nombre del equipo (ver función refrescar_tabla
        # y __color_equipo).
        self.__temp_estado = None

    def registrar(self, fila, evento=None):
        """
        Cambia el estado de registro de un equipo.

        """
        if self.__pagina_edicion is not None:
            tkinter.messagebox.showwarning(
                "Edición puntos homologación",
                "Guarde los datos del equipo actual "
                "antes de editar otro equipo.")
            return
        # Obtenemos el nombre del equipo para mostrarselo al usuario.
        equipo, nombre = self.__conexion.datos_equipo(fila)
        # Antes de cambiar de estado, preguntamos al usuario.
        if tkinter.messagebox.askokcancel(
                "Registrar equipo",
                "Cambiar el estado de registro del equipo %s (%s)" %
                (nombre, equipo)):
            try:
                self.__conexion.registrar_equipo(fila)
            except BlockingIOError as e:
                tkinter.messagebox.showerror(
                    "Error edición equipo", e)
            self.refrescar_tabla(equipo)

    # Funciones de atención a los eventos de edición de zona de homologación.
    # Se implementa como un decorator, de tal forma que con una única función
    # podems atender a todos los posibles zonas sin necesidad de pasar el
    # número de zona como argumento.
    @staticmethod
    def editar_zona(zona):
        def decorator(funcion):
            def wrapper(fila, evento=None):
                return funcion(fila, zona, evento)
            return wrapper
        return decorator

    def editar_zona_aux(self, fila, zona, evento=None):
        """
        Función principal de edición de zonas.

        """
        # Comprobamos si nos encontramos editando otra zona.
#        if self.__pagina_edicion is not None:
        if self.edicion:
            tkinter.messagebox.showwarning(
                "Edición puntos homologación",
                "Guarde los datos del equipo actual antes de editar otro equipo.")
            return

        # Si el equipo no está registrado, no podemos homologarlo todavía.
        if self.__conexion.estado_equipo(fila) == 0:
            return
        # Creamos una nueva página para editar los puntos de la zona.
        try:
            self.__pagina_edicion = Pagina(
                self.desbloquear,  self.__puntos, self.__conexion, fila, zona)
        except BlockingIOError as e:
            tkinter.messagebox.showerror(
                "Error edición equipo", e)
        else:
            # Deshabilitamos las funciones de desplazamiento vertical de la
            # tabla, que se volverá a habilitar cuando la pagina anterior llame
            # a la función desbloquear al finalizar.
            self.__tabla_equipos.desp_vertical = False
            self.__bloquear_pestañas()

    def refrescar_tabla(self, equipo=None):
        """
        Refresca los datos de la tabla.

        Si equipo es None, se refresca la tabla entera. Si no es None sólo se
        refresca el equipo indicado.

        """
        # Obtenemos los datos para la tabla,
        lista = self.__conexion.lista_equipos(self.__estado_tabla, equipo)
        # NOTA: Si equipo no es None, es decir, requerimos la información de
        # un equipo, pero la base de datos no nos devuelve ningún registro,
        # significa que éste ha cambiado de estado y no supera el filtro de la
        # tabla actual. En ese caso, lo que hacemos es refrescar toda la tabla,
        # y ponemos equipo a None para que entre en el código correcto del if.
        if len(lista) == 0:
            lista = self.__conexion.lista_equipos(self.__estado_tabla)
            equipo = None
        # Formateamos los datos para mostrarlos en la tabla.
        lista = Tabla.formatear_lista_tabla(lista)
        # Obtenemos el estado de cada equipo, para que la función de determinar
        # el color de la celda funcione correctamente.
        lista_estados = self.__conexion.lista_estado_equipos(equipo)
        # Para ello generamos una variable temporal que será accedida por la
        # función de cálculo del color de la celda con el nombre del equipo.
        self.__temp_estado = {}
        for estado in lista_estados:
            self.__temp_estado[estado["ORDEN"]] = estado
        # Determinamos si es necesario refrescar toda la tabla, o sólo la
        # información del equipo actual.
        if equipo is None:
            # Si hay que refrescar toda la tabla, hacemos la llamada normal.
            self.__tabla_equipos.refrescar(lista)
        else:
            # y si sólo es refrescar los datos del equipo en cuestión, ponemos
            # el indicador a True.
            self.__tabla_equipos.refrescar(lista, True)
        # En este punto ya no es necesario ela variable temporal, por lo que
        # podemos eliminarla.
        self.__temp_estado = None

    def seleccionar_estado(self, es):
        """
        Permite cambiar el estado (filtro) de la tabla de equipos.

        """
        global estado_tabla
        self.__estado_tabla = es
        self.refrescar_tabla()
        return self.__estado_tabla

    def desbloquear(self):
        """
        Evento que debe ser llamado una vez se cierre la página de edición.

        """
        # Cada vez que cerramos una página, refrescamos la tabla, ya que es
        # posible que el equipo haya cambiado de estado.
        self.refrescar_tabla(self.__pagina_edicion.equipo)
        # Y ponemos su estado en modo lectura, hasta que abramos una nueva
        # página.
        self.__pagina_edicion = None
        # Habilitamos las funciones de desplazamiento vertical de la tabla.
        self.__tabla_equipos.desp_vertical = True
        self.__bloquear_pestañas(False)

    def __bloquear_pestañas(self, bloquear=True):
        estado = tkinter.DISABLED if bloquear else tkinter.NORMAL
        for boton in self.__pestañas.children.values():
            boton.config(state=estado)

    def __color_equipo(self, fila, columna, valor):
        """
        Obtener el color de la etiqueta correspondiente a la columna con el
        nombre del equipo.

        """
        # La función necesita la variable __temp_estado, por lo que es
        # necesario asegurarse que esta variable existe antes de poder
        # utilizarla.
        datos_equipo = self.__temp_estado[fila]
        estado_equipo = datos_equipo["estado"]
        if estado_equipo == "I":
            return "white"
        elif estado_equipo == "R":
            return "red"
        elif estado_equipo == "H":
            return "green"
        else:
            raise ValueError("Vista ListaEstadosEquipos incorrecta")

    def get_ancho(self):
        return self.__tabla_equipos.ancho_tabla

    def get_edicion(self):
        return self.__pagina_edicion is not None

    ancho = property(get_ancho, None, None, None)
    edicion = property(get_edicion, None, None, None)
