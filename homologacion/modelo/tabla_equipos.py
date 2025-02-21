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

from magic.compat import NONE
import tkinter.messagebox

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
        pestañas = tkinter.Frame(marco)
        pestañas.grid(row=0, column=0, sticky="nsew")
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
        tkinter.Radiobutton(pestañas, text="Todos",
                            variable=self.variable, value=1,
                            indicatoron=0, width=10, height=1, padx=10, pady=10,
                            command=lambda: self.seleccionar_estado(
                                estado.TODOS)).pack(side=tkinter.LEFT)

        tkinter.Radiobutton(pestañas, text="Inscritos",
                            variable=self.variable, value=2,
                            indicatoron=0, width=10, height=1, padx=10, pady=10,
                            command=lambda: self.seleccionar_estado(
                                estado.INSCRITO)).pack(side=tkinter.LEFT)

        tkinter.Radiobutton(pestañas, text="Registrados",
                            variable=self.variable, value=3,
                            indicatoron=0, width=10, height=1, padx=10, pady=10,
                            command=lambda: self.seleccionar_estado(
                                estado.REGISTRADO)).pack(side=tkinter.LEFT)

        tkinter.Radiobutton(pestañas, text="Homologados",
                            variable=self.variable, value=4,
                            indicatoron=0, width=10, height=1, padx=10, pady=10,
                            command=lambda: self.seleccionar_estado(
                                estado.HOMOLOGADO)).pack(side=tkinter.LEFT)

        # Obtenemos los datos de configuración de la cabecera desde la
        # base de datos.
#        cabecera, ancho, alineacion, ajuste = self.__conexion.configuracion_tabla()
        nombre = self.__conexion.cabecera_nombre
        ancho = self.__conexion.cabecera_ancho
        alineacion = self.__conexion.cabecera_alineacion
        ajuste = self.__conexion.cabecera_ajuste
        # Creamos la tabla, junto con su formato.
        self.__tabla_equipos = Tabla(tabla, nombre, ancho, ajuste, alineacion,
                                     50, 45, FUENTE_CABECERA, FUENTE_DATOS)

        # Inicialmente arrancamos la aplicación mostrando todos los equipos.
        self.__estado_tabla = self.seleccionar_estado(estado.TODOS)

        # Configuración de eventos. La tabla de configuración de la base de
        # datos nos indica sobre qué columnas se deben ejecutar los eventos
        # de edición de puntos, y sobre que columnas los de cambio de registro.
        eventos = self.__conexion.cabecera_eventos
        for columna, evento in enumerate(eventos):
            if evento is None:
                continue
            elif evento == 0:
                # El código 0 se refiere a cambio de registro.
                self.__tabla_equipos.añadir_evento(
                    "<Double-1>", columna, self.registrar)
            else:
                # El resto de códigos se refieren al número de zona que debe
                # editar dicho evento.
                self.__tabla_equipos.añadir_evento(
                    "<Double-1>", columna,
                    self.editar_zona(evento)(self.editar_zona_aux))
                # Asignamos también las funciones para calcular el color de
                # la celda en función del valor de ésta.
                self.__tabla_equipos.definir_color_columna(
                    columna, "white",
                    lambda valor: "green" if int(valor) == 0 else "red")

        # Guardamos en esta variable la referencia a la página que estamos
        # editando. Si es None, significa que estamos no estamos editando nada,
        # es decir, estamos en modo Lectura.
        self.__pagina_edicion = None

    def registrar(self, fila, evento=None):
        """
        Cambia el estado de registro de un equipo.

        """
        if self.__pagina_edicion is not None:
            tkinter.messagebox.showwarning(
                "Edición puntos homologación",
                "Guarde los datos del equipo actual antes de editar otro equipo.")
            return
        # Obtenemos el nombre del equipo para mostrarselo al usuario.
        nombre = self.__conexion.datos_equipo(fila)
        # Antes de cambiar de estado, preguntamos al usuario.
        if tkinter.messagebox.askokcancel(
                "Registrar equipo",
                "Cambiar el estado de registro del equipo %s (%s)" %
                (nombre[1], nombre[0])):
            try:
                self.__conexion.registrar_equipo(fila)
            except BlockingIOError as e:
                tkinter.messagebox.showerror(
                    "Error edición equipo", e)
            self.refrescar_tabla()

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

    def refrescar_tabla(self):
        """
        Refresca los datos de la tabla.

        """
        # Obtenemos los datos para la tabla,
        lista = self.__conexion.lista_equipos(self.__estado_tabla)
        # los formatemaos
        lista = Tabla.formatear_lista_tabla(lista)
        # y los mostramos en la tabla.
        self.__tabla_equipos.refrescar(lista)

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
        self.refrescar_tabla()
        # Y ponemos su estado en modo lectura, hasta que abramos una nueva
        # página.
        self.__pagina_edicion = None

    def get_ancho(self):
        return self.__tabla_equipos.ancho_tabla

    def get_edicion(self):
        return self.__pagina_edicion is not None

    ancho = property(get_ancho, None, None, None)
    edicion = property(get_edicion, None, None, None)
