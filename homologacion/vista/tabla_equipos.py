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

from functools import partial
import tkinter.messagebox

from leer_constantes import leer_cabecera, leer_alturas_tabla, leer_logos
from leer_constantes import leer_colores_tabla, leer_colores_puntos
from leer_constantes import leer_fuente
from modelo.base_datos import estado, orden_tabla
from modelo.pagina_edicion import Pagina
from modelo.tabla import Tabla
from vista.formulario_seleccion import abrir_seleccion


FUENTE_CABECERA = ("LIBERATION SANS", 20, "")
FUENTE_DATOS = ("LIBERATION SANS", 15, "")


class TablaEquipos(object):
    '''

    '''

    def __init__(self, ventana, marco, conexion, puntos, fondo):
        '''
        Constructor

        Argumentos:
        - ventana: ventana principal, para poder mostrar diálogos con
          respecto a esta ventana.
        - marco: marco de tkinter donde se construirá toda la interfaz gráfica
        - conexion.
        - puntos: marco auxiliar donde se mostrarán los puntos de homologacion.
        - fondo: etiqueta con el fondo a mostrar en el area de puntos
          cuando no se está visualizando los puntos de homologación.

        '''
        # Criterio de ordenación. Inicialmente, ordenamos por dorsal.
        self.__orden = orden_tabla.DORSAL

        # Guardamos la referencia a la ventana principal.
        self.__ventana = ventana
        # Guardamos la conexión a la base de datos.
        self.__conexion = conexion
        # Guardamos el marco donde se mostrarán los puntos de homologación.
        self.__puntos = puntos
        # y el fondo, para cuando no se estén mostrando puntos.
        self.__fondo = fondo

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

        # Variable para gestionar los radiobutton
        self.variable = tkinter.IntVar()
        self.variable.set(1)
        # Sobre la cabecera añadimos botones para cambiar entre los distintos
        # estados del equipo.
        tkinter.Radiobutton(self.__pestañas, text="Todos",
                            variable=self.variable, value=1,
                            indicatoron=0, width=10, height=1, padx=10, pady=10,
                            command=lambda: self.__seleccionar_estado(
                                estado.TODOS)).pack(side=tkinter.LEFT)

        tkinter.Radiobutton(self.__pestañas, text="Inscritos",
                            variable=self.variable, value=2,
                            indicatoron=0, width=10, height=1, padx=10, pady=10,
                            command=lambda: self.__seleccionar_estado(
                                estado.INSCRITO)).pack(side=tkinter.LEFT)

        tkinter.Radiobutton(self.__pestañas, text="Registrados",
                            variable=self.variable, value=3,
                            indicatoron=0, width=10, height=1, padx=10, pady=10,
                            command=lambda: self.__seleccionar_estado(
                                estado.REGISTRADO)).pack(side=tkinter.LEFT)

        tkinter.Radiobutton(self.__pestañas, text="Homologados",
                            variable=self.variable, value=4,
                            indicatoron=0, width=10, height=1, padx=10, pady=10,
                            command=lambda: self.__seleccionar_estado(
                                estado.HOMOLOGADO)).pack(side=tkinter.LEFT)

        # Obtenemos los datos de configuración de toda la interfaz.
        colores_tabla = leer_colores_tabla()
        fuente_cabecera, color_fuente_cabecera = leer_fuente("tabla")
        self.__fuente_filas, self.__color_fuente_filas = leer_fuente("filas")
        # Obtenemos los datos de configuración de la tabla desde la
        # base de datos y el archivo xml.
        cabecera = leer_cabecera()
        columnas = self.__conexion.columnas()
        configuracion = self.__configuracion_columnas(columnas, cabecera)
        alturas = leer_alturas_tabla()
        # Creamos la tabla, junto con su formato.
        self.__tabla_equipos = Tabla(
            tabla,
            cabecera=configuracion["nombre"],
            ancho=configuracion["ancho"],
            ajuste=configuracion["ajuste"],
            alineacion=configuracion["alineacion"],
            alto_cabecera=alturas["CABECERA"],
            alto_datos=alturas["DATOS"],
            color_borde=colores_tabla["BORDE"],
            color_fondo=colores_tabla["FONDO"],
            color_cabecera=colores_tabla["CABECERA"],
            color_filas=colores_tabla["FILAS"],
            fuente_cabecera=fuente_cabecera,
            color_fuente_cabecera=color_fuente_cabecera,
            fuente_filas=self.__fuente_filas,
            color_fuente_filas=self.__color_fuente_filas)

        # Añadimos el evento doble click a la cabecera, para permitir ordenar
        # respecto de la columna pulsada.
        self.__tabla_equipos.añadir_evento_cabecera(
            "<Double-1>", 0, partial(self.__ordenar, orden_tabla.DORSAL))
        self.__tabla_equipos.añadir_evento_cabecera(
            "<Double-1>", 1, partial(self.__ordenar, orden_tabla.NOMBRE))
        self.__tabla_equipos.añadir_evento_cabecera(
            "<Double-1>", 3, partial(self.__filtro_categorias, None))

        def color_zona(fila, columna, valor):
            " Función para definir el color de las zonas de hommologación."
            try:
                color = self.__colores["COLOR_SI"] if int(
                    valor) == 0 else self.__colores["COLOR_NO"]
            except ValueError:
                color = self.__colores["COLOR_NP"]
            return color

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
                    self.__editar_zona(evento)(self.__editar_zona_aux))
                # Asignamos también las funciones para calcular el color de
                # la celda en función del valor de ésta.
                self.__tabla_equipos.definir_color_columna(
                    columna, "white", color_zona)

        self.__colores = leer_colores_puntos()
        # Inicialmente arrancamos la aplicación mostrando todos los equipos.
        # La llamada a esta función rellena por primera vez la tabla con datos.
        self.__estado_tabla = self.__seleccionar_estado(estado.TODOS)

        # Guardamos en esta variable la referencia a la página que estamos
        # editando. Si es None, significa que no estamos editando nada, es
        # decir, estamos en modo Lectura.
        self.__pagina_edicion = None
        # Variable temporal empleada por la función que determinar el color
        # de la columna con el nombre del equipo (ver función refrescar_tabla
        # y __color_equipo).
        self.__temp_estado = None
        # Guardamos el fondo que debemos mostrar cuando no hay ningún equipo
        # editando.
        self.__mostrar_area()

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
        dorsal, equipo = self.__conexion.datos_equipo(fila, self.__orden)
        # Antes de cambiar de estado, preguntamos al usuario.
        if tkinter.messagebox.askokcancel(
                "Registrar equipo",
                "¿Cambiar el estado de registro del equipo %s (%s)?" %
                (equipo, dorsal)):
            try:
                self.__conexion.registrar_equipo(dorsal)
            except BlockingIOError as e:
                tkinter.messagebox.showerror(
                    "Error edición equipo", e)
            self.refrescar_tabla(dorsal)

    # Funciones de atención a los eventos de edición de zona de homologación.
    # Se implementa como un decorator, de tal forma que con una única función
    # podems atender a todos los posibles zonas sin necesidad de pasar el
    # número de zona como argumento.
    @staticmethod
    def __editar_zona(zona):
        def decorator(funcion):
            def wrapper(fila, evento=None):
                return funcion(fila, zona, evento)
            return wrapper
        return decorator

    def __editar_zona_aux(self, fila, zona, evento=None):
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
        # En primer lugar, obtenemos el dorsal del equipo a partir de la fila en
        # la que se encuentra.
        dorsal, __ = self.__conexion.datos_equipo(fila, self.__orden)
        if self.__conexion.estado_equipo(dorsal) == 0:
            return
        # Función para definir el color de la etiqueta de la página.

        def color_punto(valor, seccion):
            if not seccion:
                return self.__colores["COLOR_SC"]
            return self.__colores["COLOR_SI"] if valor == 0 else self.__colores["COLOR_NO"]
        # Creamos una nueva página para editar los puntos de la zona.
        try:
            # Fijamos el mismo color del borde de la tabla en la página.
            colores_tabla = leer_colores_tabla()
            self.__pagina_edicion = Pagina(
                self.__puntos, self.__conexion, fila, self.__orden, zona,
                self.__desbloquear, color_punto, colores_tabla["BORDE"])
            self.__mostrar_area()

        except BlockingIOError as e:
            tkinter.messagebox.showerror(
                "Error edición equipo", e)
        except ValueError as e:
            tkinter.messagebox.showerror(
                "Error edición equipo", e)
        else:
            # Deshabilitamos las funciones de desplazamiento vertical de la
            # tabla, que se volverá a habilitar cuando la pagina anterior llame
            # a la función desbloquear al finalizar.
            self.__tabla_equipos.desp_vertical = False
            self.__bloquear_pestañas()

    def refrescar_tabla(self, dorsal=None):
        """
        Refresca los datos de la tabla.

        Si equipo es None, se refresca la tabla entera. Si no es None sólo se
        refresca el equipo indicado.

        """
        # Obtenemos los datos para la tabla,
        lista = self.__conexion.lista_equipos(
            self.__estado_tabla, self.__orden, dorsal)
        # NOTA: Si dorsal no es None, es decir, requerimos la información de
        # un equipo, pero la base de datos no nos devuelve ningún registro,
        # significa que éste ha cambiado de estado y no supera el filtro de la
        # tabla actual. En ese caso, lo que hacemos es refrescar toda la tabla,
        # y ponemos dorsal a None para que entre en el código correcto del if.
        if len(lista) == 0:
            lista = self.__conexion.lista_equipos(
                self.__estado_tabla, self.__orden)
            dorsal = None
        # Formateamos los datos para mostrarlos en la tabla.
        lista = Tabla.formatear_lista_tabla(lista)
        # Obtenemos el estado de cada equipo, para que la función de determinar
        # el color de la celda funcione correctamente.
        lista_estados = self.__conexion.lista_estado_equipos(
            self.__orden, dorsal)
        # Para ello generamos una variable temporal que será accedida por la
        # función de cálculo del color de la celda con el nombre del equipo.
        self.__temp_estado = {}
        for estado in lista_estados:
            self.__temp_estado[estado["ORDEN"]] = estado
        # Determinamos si es necesario refrescar toda la tabla, o sólo la
        # información del equipo actual.
        if dorsal is None:
            # Si hay que refrescar toda la tabla, hacemos la llamada normal.
            self.__tabla_equipos.refrescar(lista)
        else:
            # y si sólo es refrescar los datos del equipo en cuestión, ponemos
            # el indicador a True.
            self.__tabla_equipos.refrescar(lista, True)
        # En este punto ya no es necesario la variable temporal, por lo que
        # podemos eliminarla.
        self.__temp_estado = None

    def __seleccionar_estado(self, es):
        """
        Permite cambiar el estado (filtro) de la tabla de equipos.

        """
        global estado_tabla
        self.__estado_tabla = es
        self.refrescar_tabla()
        return self.__estado_tabla

    def __desbloquear(self, mensaje):
        """
        Evento que debe ser llamado una vez se cierre la página de edición.

        """
        if not tkinter.messagebox.askokcancel("Finalizar edición equipo", mensaje):
            return False
        # Cada vez que cerramos una página, refrescamos la tabla, ya que es
        # posible que el equipo haya cambiado de estado.
        self.refrescar_tabla(self.__pagina_edicion.equipo)
        # Y ponemos su estado en modo lectura, hasta que abramos una nueva
        # página.
        self.__pagina_edicion = None
        self.__mostrar_area()
        # Habilitamos las funciones de desplazamiento vertical de la tabla.
        self.__tabla_equipos.desp_vertical = True
        self.__bloquear_pestañas(False)
        return True

    def __bloquear_pestañas(self, bloquear=True):
        estado = tkinter.DISABLED if bloquear else tkinter.NORMAL
        for boton in self.__pestañas.children.values():
            boton.config(state=estado)

    def __ordenar(self, crierio, event=None):
        """
        Función para ordenar la tabla de equipos en función del criterio

        """
        if self.__pagina_edicion is not None:
            return
        # Solo actualizamos el criterio de ordenación cuando no estamos
        # editando ningún equipo.
        self.__orden = crierio
        self.refrescar_tabla()

    def __filtro_categorias(self, categorias, event=None):
        """
        Seleccionar las categorías a mostrar en la tabla de equipos.

        """
        if self.__pagina_edicion is not None:
            return
        categorias = self.__conexion.seleccion_categorias()

        datos_logos = leer_logos()
        cabecera = datos_logos["LOGO_CABECERA"]

        aceptar = abrir_seleccion(
            self.__ventana, "Categorías", cabecera,
            "Selecciona las categorías a visualizar", categorias)

        if aceptar:
            self.__conexion.seleccion_categorias(categorias)
            self.refrescar_tabla()

    def __color_equipo(self, fila, columna, valor):
        """
        Obtener el color de la etiqueta correspondiente a la columna con el
        nombre del equipo.

        """
        # La función necesita la variable __temp_estado, por lo que es
        # necesario asegurarse que esta variable existe antes de poder
        # utilizarla.
        try:
            datos_equipo = self.__temp_estado[fila]
        except KeyError:
            return
        if not datos_equipo["registrado"]:
            return self.__colores["COLOR_NP"]
        elif not datos_equipo["homologado"]:
            return self.__colores["COLOR_NO"]
        else:
            return self.__colores["COLOR_SI"]

    @staticmethod
    def __configuracion_columnas(columnas, configuracion):
        """
        Devuelve las listas de configuración de columnas.

        Argumentos:
        - columnas: lista de columnas de la vista que queremos configurar,
          obtenida con el comando SQL "SHOW COLUMNS FROM NombreVista"
        - configuracion: dicionario, donde cada

        """
        # Creamos las listas para cada uno de los parámetros de configuración.
        nombre = []
        ancho = []
        alineacion = []
        ajuste = []
        eventos = []
        # Para cada columna de la vista,
        for campo in columnas:
            try:
                # Comprobamos que el nombre de la columna exista en la lista de
                # configuración.
                valor = configuracion[campo["Field"]]
                # Comprobamos que la columna tenga el campo nombre.
                try:
                    nombre += [valor["NOMBRE"]]
                except KeyError:
                    continue
            except KeyError:
                # En caso contrario, significa que esta columna no hay que
                # añadirla.
                # Si no existe en la lista de configuración, significa que esta
                # columna no hay que mostrarla. Eso se indica poniendo a 0 en
                # campo ancho. El resto da igual
                nombre += [""]
                ancho += [0]
                alineacion += ["N"]
                ajuste += [0]
                eventos += [None]
            else:
                # Si el campo existe, copiamos todos los datos de configuración
                # de la columna.
                ancho += [int(valor["ANCHO"])]
                alineacion += [valor["ALINEACION"]]
                ajuste += [int(valor["AJUSTE"])]
                try:
                    zona = int(valor["ZONA"])
                except ValueError:
                    zona = None
                eventos += [zona]

        return {
            "nombre": nombre,
            "ancho": ancho,
            "alineacion": alineacion,
            "ajuste": ajuste,
            "eventos": eventos}

    def __mostrar_area(self):
        if self.edicion:
            self.__fondo.pack_forget()
            self.__puntos.pack(expand=True, fill=tkinter.BOTH)
        else:
            self.__puntos.pack_forget()
            self.__fondo.pack(expand=True, fill=tkinter.BOTH)

    def get_ancho(self):
        return self.__tabla_equipos.ancho_tabla

    def get_edicion(self):
        return self.__pagina_edicion is not None

    ancho = property(get_ancho, None, None, None)
    edicion = property(get_edicion, None, None, None)
