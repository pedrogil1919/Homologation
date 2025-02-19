'''
Created on 18 feb 2025

Clase para gestionar los datos a mostrar en la tabla de equipos de la
aplicación.

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

from base_datos import estado
from pagina_edicion import Pagina
from tabla import Tabla


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

        # Sobre la cabecera añadimos botones para cambiar entre los distintos
        # estados del equipo.
        tkinter.Button(pestañas, text="Todos",
                       command=lambda: self.seleccionar_estado(
                           estado.TODOS)).pack(side=tkinter.LEFT)

        tkinter.Button(pestañas, text="Inscritos",
                       command=lambda: self.seleccionar_estado(
                           estado.INSCRITO)).pack(side=tkinter.LEFT)

        tkinter.Button(pestañas, text="Registrados",
                       command=lambda: self.seleccionar_estado(
                           estado.REGISTRADO)).pack(side=tkinter.LEFT)

        tkinter.Button(pestañas, text="Homologados",
                       command=lambda: self.seleccionar_estado(
                           estado.HOMOLOGADO)).pack(side=tkinter.LEFT)

        cabecera, ancho, alineacion, ajuste = self.__conexion.configuracion_tabla()

        self.__tabla_equipos = Tabla(tabla, cabecera, ancho, ajuste, alineacion,
                                     50, 45, FUENTE_CABECERA, FUENTE_DATOS)

        self.__estado_tabla = self.seleccionar_estado(estado.INSCRITO)

        eventos = self.__conexion.configuracion_eventos()
        for n, evento in enumerate(eventos):
            if evento is None:
                continue
            elif evento == 0:
                self.__tabla_equipos.añadir_evento(
                    "<Double-1>", n, self.registrar)
            else:
                self.__tabla_equipos.añadir_evento(
                    "<Double-1>", n, self.editar_zona(evento)(self.editar_zona_aux))

        # Guardamos en esta variable la referencia a la página que estamos
        # editando. Si es None, significa que estamos no estamos editando nada,
        # es decir, estamos en modo Lectura.
        self.__pagina_edicion = None

    def refrescar_tabla(self):
        lista = self.__conexion.lista_equipos(self.__estado_tabla)
        lista = Tabla.formatear_lista_tabla(lista)
        self.__tabla_equipos.refrescar(lista)

    def seleccionar_estado(self, es):
        global estado_tabla
        self.__estado_tabla = es
        self.refrescar_tabla()
        return self.__estado_tabla

    def registrar(self, fila, evento=None):
        if self.__pagina_edicion is not None:
            tkinter.messagebox.showwarning(
                "Edición puntos homologación",
                "Guarde los datos del equipo actual antes de editar otro equipo.")
            return

        self.__conexion.registrar_equipo(fila, self.__estado_tabla)
        self.refrescar_tabla()

    @staticmethod
    def editar_zona(zona):
        def decorator(funcion):
            def wrapper(fila, evento=None):
                return funcion(fila, zona, evento)
            return wrapper
        return decorator

    def editar_zona_aux(self, fila, zona, evento=None):
        if self.__pagina_edicion is not None:
            tkinter.messagebox.showwarning(
                "Edición puntos homologación",
                "Guarde los datos del equipo actual antes de editar otro equipo.")
            return

        if self.__estado_tabla == estado.INSCRITO:
            return
        self.__pagina_edicion = Pagina(
            self.desbloquear,  self.__puntos, self.__conexion, fila, zona)

    def desbloquear(self):
        self.refrescar_tabla()
        self.__pagina_edicion = None

    def get_ancho(self):
        return self.__tabla_equipos.ancho_tabla

    def get_edicion(self):
        return self.__pagina_edicion is not None

    ancho = property(get_ancho, None, None, None)
    edicion = property(get_edicion, None, None, None)
