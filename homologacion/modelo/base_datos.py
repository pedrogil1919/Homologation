'''
Created on 4 feb 2025

@author: pedrogil
'''

from enum import IntEnum

import mariadb

# Valores del filtro de la tabla de equipos.


class estado(IntEnum):
    TODOS = 1
    INSCRITO = 2
    REGISTRADO = 3
    HOMOLOGADO = 4


# Códigos necesarios para realizar el filtro de la tabla de equipos.
ESTADO = {
    1: ((0, 1), (0, 1)),
    2: ((0,), (1, 0)),
    3: ((1,), (0,)),
    4: ((1,), (1,))}


class orden_tabla(IntEnum):
    DORSAL = 1
    NOMBRE = 2
    COMPETICION = 3


# Nombre del campo por el que vamos a ordenar la tabla de equipos.
ORDEN_TABLA = {
    1: "FK_EQUIPO",
    2: "equipo",
    3: "competicion"}


class Conexion():

    def __init__(self, user, password, host, database, timeout):
        """
        Conectar a la base de datos

        """
        # Comprobamos que podemos realizar la conexión a la base de datos.
        try:
            self.__conexion = mariadb.connect(
                user=user,
                password=password,
                host=host,
                database=database,
                autocommit=True,
                connect_timeout=timeout)
        except mariadb.OperationalError as error:
            raise ValueError("No es posible la conexión con %s(%s). %s",
                             (database, host, error))

        cursor_bloqueo = self.__conexion.cursor()
        cursor_bloqueo.execute(
            "SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")

        cursor_bloqueo.execute("SET SESSION innodb_lock_wait_timeout = 5")

        # Comprobamos que la tabla Homologacion_EstadoEquipo tenga todos los
        # equipos que están incluidos en la tabla Equipo de la bd de
        # administración.
        cursor_equipos = self.__conexion.cursor(prepared=True)
        cursor_equipos.execute(
            "INSERT INTO Homologacion_EstadoEquipo(FK_EQUIPO) "
            "SELECT ID_EQUIPO FROM VistaEquipo "
            "WHERE NOT EXISTS "
            "(SELECT FK_EQUIPO FROM Homologacion_EstadoEquipo)")

        # Guardamos los datos en el objeto.
        self.__user = user
        self.__host = host
        self.__database = database

        # Obtenemos la lista de categorías existentes en la base de datos.
        cursor_categorias = self.__conexion.cursor(
            dictionary=True, prepared=True)
        cursor_categorias.execute("SELECT * FROM GeneralCompeticion")
        categorias = cursor_categorias.fetchall()
        self.__categorias = tuple(c["ID_COMPETICION"] for c in categorias)

    def __str__(self):
        """
        Devuelve los datos informativos de la conexión.

        """
        return "%s (%s)" % (self.__database, self.__host)

################################################################################
################################################################################
################################################################################
    def lista_equipos(self, estado, orden, dorsal=None):
        """
        Obtiene la lista de equipos filtrados por el valor de estado (ver
        definición del tipo enumerado "estado"). Si equipo se corresponde con el
        ID de un equipo, sólo obtiene los datos de este equipo (que puede ser
        null si el equipo no cumple las condiciones del estado).

        Argumentos:
        - estado: permite filtrar en función del estado del equipo (ver
          variable ESTADO).
        - orden: Criterio de ordenación de los registros (ver variable
          ORDEN_TABLA).
        - dorsal: Identificador del equipo. Si es None, se devuelve la lista
          completa, en función de los criterios de filtrado. Si no es None,
          se devuelve sólo los datos de ese equipo.

        """
        cursor = self.__conexion.cursor(dictionary=False, prepared=True)
        filtro_registrado = ESTADO[estado][0]
        filtro_homologado = ESTADO[estado][1]
        # Obtenemos la lista de equipos a homologar.
        consulta = "SELECT * FROM "
        consulta += self.__vista_ordenada(orden)
        consulta += "WHERE registrado IN %s AND homologado IN %s" % (
            self.cadena_lista(filtro_registrado),
            self.cadena_lista(filtro_homologado))
        if dorsal is None:
            # En el caso de que no nos pasen el dorsal del equipo, nos descargamos
            # todos los equipos.
            cursor.execute(consulta, filtro_registrado + filtro_homologado)
        else:
            # En el caso de que nos pasen el dorsal, sólo nos descargamos ese
            # equipo.
            consulta += " AND FK_EQUIPO = %s"
            cursor.execute(consulta, filtro_registrado +
                           filtro_homologado + (dorsal,))
        equipos = cursor.fetchall()
        return equipos

    def lista_estado_equipos(self, orden, dorsal=None):
        """
        Devuelve el estado de cada uno de los equipos. El estado se determina a partir
        de los campos registrado y homologado. El significado es:

        - registrado=0: equipo no registrado, independientemente del estado del campo
          homologado.
        - registrado=0, homologado=1: registrado pero no homologado todavía.
        - registrado=1, homologado=1: equipo ya homologado.

        """
        cursor = self.__conexion.cursor(dictionary=True, prepared=True)
        consulta = "SELECT ORDEN, registrado, homologado FROM "
        consulta += self.__vista_ordenada(orden)
        if dorsal is None:
            cursor.execute(consulta)
        else:
            consulta += " WHERE FK_EQUIPO = %s"
            cursor.execute(consulta, (dorsal,))
        equipos = cursor.fetchall()
        return equipos

    def __dorsal_equipo(self, fila, orden):
        """
        Obtiene el dorsal del equipo a partir de la fila que ocupa en la tabla

        """
        cursor_dorsal = self.__conexion.cursor(prepared=True)
        consulta = "SELECT FK_EQUIPO FROM "
        consulta += self.__vista_ordenada(orden)
        consulta += "WHERE ORDEN = %s"
        cursor_dorsal.execute(consulta, (fila,))
        if cursor_dorsal.rowcount != 1:
            raise RuntimeError("Error en función de cambio de estado.")
        dorsal = cursor_dorsal.fetchone()[0]
        return dorsal

    def registrar_equipo(self, dorsal):
        """
        Alterna el estado de registro de un equipo

        Argumentos:
        - fila: fila a la que corresponde el equipo. Tener en cuenta que el
          número de fila no se corresponde con el dorsal, por lo que es
          necesario determinar el dorsal a partir de la fila.

        """
        # Determinamos el estado de registro del equipo, y cambiamos su estado.
        estado_nuevo = 1 if (self.estado_equipo(dorsal) == 0) else 0

        # Comprobamos que el equipo no esté bloqueado por otro usuario, y por
        # tano no podemos cambiar su estado.
        cursor_bloqueo = self.__conexion.cursor(prepared=True)
        try:
            cursor_bloqueo.execute(
                "SELECT * FROM Homologacion_EstadoEquipo WHERE FK_EQUIPO = %s "
                "FOR UPDATE NOWAIT", (dorsal,))
        except mariadb.OperationalError as e:
            # Detectamos si el equipo se encuentra bloqueado por otro usuario.
            if e.errno == 1205:
                raise BlockingIOError(
                    "El equipo está bloqueado por otro usuario. "
                    "Espere a que termine para poder continuar.")
            else:
                raise e

        cursor_equipo = self.__conexion.cursor(prepared=True)
        cursor_equipo.execute(
            "UPDATE Homologacion_EstadoEquipo SET registrado=%s WHERE FK_EQUIPO=%s",
            (estado_nuevo, dorsal))
        if cursor_equipo.affected_rows != 1:
            raise RuntimeError("Error en función de cambio de estado.")
        self.__conexion.commit()

    def estado_equipo(self, dorsal):
        """
        Determina el estado de registro de un equipo.

        """
#        cursor_dorsal = self.__conexion.cursor(prepared=True)
        cursor_estado = self.__conexion.cursor(prepared=True)
#        # Determinamos el estado de registro del equipo, para alternarlo.
        cursor_estado.execute(
            "SELECT registrado FROM Homologacion_ListaEquipos "
            "WHERE FK_EQUIPO = %s", (dorsal,))
        if cursor_estado.rowcount != 1:
            raise RuntimeError("Error en función de cambio de estado.")
        estado_actual = cursor_estado.fetchone()[0]
        return estado_actual

    def datos_equipo(self, fila, orden):
        """
        Obtiene los datos del equipo a partir de la fila en la tabla

        """
        dorsal = self.__dorsal_equipo(fila, orden)

        cursor = self.__conexion.cursor(dictionary=False, prepared=True)
        cursor.execute(
            "SELECT FK_EQUIPO, equipo FROM Homologacion_ListaEquipos WHERE FK_EQUIPO = %s",
            (dorsal,))

        nombre = cursor.fetchone()
        return nombre[0], nombre[1]

    def resumen_equipos(self):
        """
        Estadísticas del proceso de homologación.

        """
        cursor = self.__conexion.cursor(dictionary=True, prepared=True)
        cursor.execute("SELECT * FROM Homologacion_ResumenEquipos")
        if cursor.rowcount != 1:
            raise RuntimeError("Error en la vista de resumen")
        lista = cursor.fetchone()
        resumen = "Total: %i - Sin reg: %i - Reg: %i - Homol: %i" % (
            lista["total"], lista["inscrito"],
            lista["registrado"], lista["homologado"])
        return resumen

################################################################################
################################################################################
################################################################################

    def lista_puntos_homologacion(self, equipo, zona):
        """
        Obtiene la lista de puntos de homologación para la zona indicada.

        """
        self.__abrir_transaccion(equipo)
        cursor = self.__conexion.cursor(dictionary=True, prepared=True)
        cursor.execute(
            "SELECT * FROM Homologacion_ListaPuntos WHERE "
            "FK_EQUIPO = %s AND FK_HOMOLOGACION_ZONA = %s", (equipo, zona))

        lista = cursor.fetchall()

        cursor2 = self.__conexion.cursor(prepared=True)
        cursor2.execute(
            "SELECT comentario FROM Homologacion_Comentario WHERE "
            "FK_EQUIPO = %s AND FK_HOMOLOGACION_ZONA = %s", (equipo, zona))
        if cursor2.rowcount != 1:
            raise ValueError(
                "Error en la tabla Comentario. Vuelve a registrar el equipo para proseguir.")
        comentario = cursor2.fetchone()
        return lista, comentario[0]

    def actualizar_comentario(self, equipo, zona, texto):
        """
        Actualiza el texto del campo comentario para el equipo y zona

        """
        cursor = self.__conexion.cursor(dictionary=False, prepared=True)
        cursor.execute(
            "UPDATE Homologacion_Comentario SET comentario = %s "
            "WHERE FK_EQUIPO = %s AND FK_HOMOLOGACION_ZONA = %s",
            (texto, equipo, zona))
        # Comprobamos que sólo se ha actualizado un registro.
        # NOTA: Puede ser que el número sea igual a 0 si el comentario a
        # añadir es el mismo que ya tenía. Por eso, sólo comprobamos que no
        # haya más de un registro afectado.
        if cursor.affected_rows > 1:
            raise RuntimeError("Error al añadir comentario de equipo.")

    def actualizar_punto_homologacion(self, equipo, punto, zona):
        """
        Alterna el valor de un punto de homologación entre True y False

        """
        cursor_get = self.__conexion.cursor(dictionary=False, prepared=True)
        cursor_set = self.__conexion.cursor(dictionary=False, prepared=True)
        cursor_get.execute(
            "SELECT valor FROM Homologacion_ListaPuntos WHERE "
            "FK_EQUIPO = %s AND FK_HOMOLOGACION_PUNTO = %s AND "
            "FK_HOMOLOGACION_ZONA = %s", (equipo, punto, zona))

        if cursor_get.rowcount != 1:
            raise RuntimeError("Error al actualizar punto de homoloación.")
        valor = cursor_get.fetchone()[0]

        valor = 0 if valor == 1 else 1
        cursor_set.execute(
            "UPDATE Homologacion_Equipo SET valor = %s WHERE "
            "FK_EQUIPO = %s AND FK_HOMOLOGACION_PUNTO = %s AND "
            "FK_HOMOLOGACION_ZONA = %s", (valor, equipo, punto, zona))

        if cursor_set.affected_rows != 1:
            raise RuntimeError("Error al actualizar punto de homoloación.")

        return valor


################################################################################
################################################################################
################################################################################
    def __bloquear_equipo(self, equipo):
        """
        Bloquea todos los registros relacionados con este equipo en la bd.

        """
        # Bloqueamos a nivel de base de datos para que no se puedan modificar
        # por otro usuario hasta que no cierre el primer usuario.
        cursor_equipo = self.__conexion.cursor(prepared=True)
        cursor_puntos = self.__conexion.cursor(prepared=True)
        try:
            cursor_equipo.execute(
                "SELECT * FROM Homologacion_EstadoEquipo WHERE FK_EQUIPO = %s "
                "FOR UPDATE NOWAIT", (equipo,))
            cursor_puntos.execute(
                "SELECT * FROM Homologacion_Equipo WHERE FK_EQUIPO = %s "
                "FOR UPDATE NOWAIT", (equipo,))
        except mariadb.OperationalError as e:
            # Detectamos si el equipo se encuentra bloqueado por otro usuario.
            if e.errno == 1205:
                raise BlockingIOError(
                    "El equipo está bloqueado por otro usuario. "
                    "Espere a que termine para poder continar.")
            else:
                raise e

    def __abrir_transaccion(self, equipo):
        self.__conexion.autocommit = False
        self.__conexion.begin()
        self.__bloquear_equipo(equipo)

    def guardar(self):
        self.__conexion.commit()
        self.__conexion.autocommit = True

    def cancelar(self):
        self.__conexion.rollback()
        self.__conexion.autocommit = True

    def columnas(self):
        """
        Devuelve los nombres de todas las columnas de la vista ListaEquipos.

        """
        # Obtenemos los nombres de las columnas que forman la vista.
        cursor = self.__conexion.cursor(dictionary=True, prepared=True)
        cursor.execute("SHOW COLUMNS FROM Homologacion_ListaEquipos")
        columnas = cursor.fetchall()
        return columnas

    def __vista_ordenada(self, orden):
        """
        Devuelve la estructura de una subconsulta ordenada mendiante
        la función ROW_NUMBER de SQL, siendo orden el criterio de ordenación
        para la obtención del ROW NUMBER (ver variable ORDEN_TABLA)

        """
        # NOTA: Esto crea una vista temporal, que deberá ser consultada
        # mediante una vista real, del tipo:
        # SELECT * FROM
        #    (SELECT ...
        consulta = "(SELECT ROW_NUMBER() OVER (ORDER BY %s ASC) AS ORDEN, " \
            "Homologacion_ListaEquipos.* FROM Homologacion_ListaEquipos " \
            "%s ) " \
            "AS subconsulta " % (
                ORDEN_TABLA[orden], self.__filtro_categorias())
        return consulta

    def __filtro_categorias(self):
        #        lista = tuple(
        #            c["ID_COMPETICION"] for c in self.__categorias if c["ID_COMPETICION"] < 3)
        if len(self.__categorias) == 0:
            return ""
        elif len(self.__categorias) == 1:
            return "WHERE FK_COMPETICION = %s" % self.__categorias[0]
        else:
            return "WHERE FK_COMPETICION IN %s" % str(self.__categorias)

    def seleccion_categorias(self, categorias=None):
        """
        Función para seleccionar diferentes categorías en la tabla de equipos.

        """
        cursor = self.__conexion.cursor(prepared=True, dictionary=True)
        if categorias is None:
            # Si el parámetro es None, significa que nos están solicitando la
            # lista de categorías existentes.
            # Obtenemos la lista de categorías en la base de datos.
            cursor.execute("SELECT * FROM GeneralCompeticion")
            categorias = cursor.fetchall()
            for categoria in categorias:
                categoria["titulo"] = categoria["nombre"]
                categoria["valor"] = 1 if categoria["ID_COMPETICION"] in self.__categorias else 0
            return categorias
        # En caso contrario, nos están mandando la lista para actualizarla.
        self.__categorias = tuple(
            c["ID_COMPETICION"] for c in categorias if c["valor"])

    @staticmethod
    def cadena_lista(lista):
        """
        Devuelve la cadena necesaria para realizar la instrucción WHERE IN de
        una consulta.

        """
        cadena = "(%s" + ", %s"*(len(lista)-1) + ")"
        return cadena

################################################################################
################################################################################
################################################################################
    # """
    # def get_cabecera(self, columna):
    #     cursor = self.__conexion.cursor(dictionary=False, prepared=False)
    #     cursor.execute("SELECT %s FROM ConfigVistaListaEquipos" % columna)
    #     lista = cursor.fetchall()
    #     datos = [fila[0] for fila in lista]
    #     return datos
    #
    # def get_cabecera_nombre(self):
    #     return self.get_cabecera("nombre")
    #
    # def get_cabecera_ancho(self):
    #     return self.get_cabecera("ancho")
    #
    # def get_cabecera_alineacion(self):
    #     return self.get_cabecera("alineacion")
    #
    # def get_cabecera_ajuste(self):
    #     return self.get_cabecera("ajuste")
    #
    # def get_cabecera_eventos(self):
    #     return self.get_cabecera("zona")
    #
    # cabecera_nombre = property(get_cabecera_nombre, None, None, None)
    # cabecera_ancho = property(get_cabecera_ancho, None, None, None)
    # cabecera_alineacion = property(get_cabecera_alineacion, None, None, None)
    # cabecera_ajuste = property(get_cabecera_ajuste, None, None, None)
    # cabecera_eventos = property(get_cabecera_eventos, None, None, None)
    # """
    #


###############################################################################
###############################################################################
###############################################################################
###############################################################################
#    def configuracion_tabla(self):
#        """
#        Obtener los datos de configuración de la tabla de visualización
#
#        Ver tabla "ConfigVistaListaEquipos"
#        """
#        cursor = self.__conexion.cursor(dictionary=True, prepared=True)
#        cursor.execute("SELECT * FROM ConfigVistaListaEquipos")
#        lista = cursor.fetchall()
#        cabecera = [fila["nombre"] for fila in lista]
#        ancho = [fila["ancho"] for fila in lista]
#        alineacion = [fila["alineacion"] for fila in lista]
#        ajuste = [fila["ajuste"] for fila in lista]
#
#        return cabecera, ancho, alineacion, ajuste
#
#    def configuracion_eventos(self):
#        """
#        Obtener los datos de configuración de eventos para la tabla
#
#        Ver tabla "ConfigVistaListaEquipos"
#        """
#        cursor = self.__conexion.cursor(dictionary=False, prepared=True)
#        cursor.execute("SELECT zona FROM ConfigVistaListaEquipos")
#        lista = cursor.fetchall()
#        eventos = [fila[0] for fila in lista]
#
#        return eventos
