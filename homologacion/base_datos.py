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


class Conexion():

    def __init__(self, user, password, host, database):
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
                connect_timeout=10)
        except mariadb.OperationalError as error:
            raise ValueError("No es posible la conexión con %s(%s). %s",
                             (database, host, error))

        cursor_bloqueo = self.__conexion.cursor()
        cursor_bloqueo.execute(
            "SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")

        cursor_bloqueo.execute("SET SESSION innodb_lock_wait_timeout = 5")
        # Guardamos los datos en el objeto.
        self.__user = user
        self.__host = host
        self.__database = database

    def __str__(self):
        """
        Devuelve los datos informativos de la conexión.

        """
        return "%s (%s)" % (self.__database, self.__host)

################################################################################
################################################################################
################################################################################
    def lista_equipos(self, estado):
        """
        Obtiene la lista de equipos filtrados por el valor de estado

        Ver definición del tipo enumerado "estado"

        """
        cursor = self.__conexion.cursor(dictionary=False, prepared=False)
        filtro_registrado = ESTADO[estado][0]
        filtro_homologado = ESTADO[estado][1]
        consulta = "SELECT * FROM ListaEquipos WHERE registrado IN (%s) AND homologado IN (%s)" % (
            format(", ".join(map(str, filtro_registrado))), format(", ".join(map(str, filtro_homologado))))
        cursor.execute(consulta)
        equipos = cursor.fetchall()
        return equipos

    def registrar_equipo(self, fila):
        """
        Alterna el estado de registro de un equipo

        Argumentos:
        - fila: fila a la que corresponde el equipo. Tener en cuenta que el
          número de fila no se corresponde con el dorsal, por lo que es
          necesario determinar el dorsal a partir de la fila.

        """
        # Obtenemos el dorsal del equipo a partir de la fila en la tabla.
        cursor_dorsal = self.__conexion.cursor(prepared=True)
        cursor_dorsal.execute(
            "SELECT ID_EQUIPO FROM ListaEquipos WHERE ORDEN = %s", (fila,))
        if cursor_dorsal.rowcount != 1:
            raise RuntimeError("Error en función de cambio de estado.")
        dorsal = cursor_dorsal.fetchone()[0]
        # Determinamos el estado de registro del equipo, y cambiamos su estado.
        estado_nuevo = 1 if (self.estado_equipo(fila) == 0) else 0

        # Comprobamos que el equipo no esté bloqueado por otro usuario, y por
        # tano no podemos cambiar su estado.
        cursor_bloqueo = self.__conexion.cursor(prepared=True)
        try:
            cursor_bloqueo.execute(
                "SELECT * FROM Equipo WHERE ID_EQUIPO = %s FOR UPDATE NOWAIT",
                (dorsal,))
        except mariadb.OperationalError as e:
            # Detectamos si el equipo se encuentra bloqueado por otro usuario.
            if e.errno == 1205:
                raise BlockingIOError(
                    "El equipo está bloqueado por otro usuario. "
                    "Espere a que termine para poder continar.")

        cursor_equipo = self.__conexion.cursor(prepared=True)
        cursor_equipo.execute(
            "UPDATE Equipo SET registrado=%s WHERE ID_EQUIPO=%s",
            (estado_nuevo, dorsal))
        if cursor_equipo.affected_rows != 1:
            raise RuntimeError("Error en función de cambio de estado.")
        self.__conexion.commit()

    def estado_equipo(self, fila):
        """
        Determina el estado de registro de un equipo.

        """
        cursor_dorsal = self.__conexion.cursor(prepared=True)
        cursor_estado = self.__conexion.cursor(prepared=True)
        # Obtenemos el dorsal del equipo.
        cursor_dorsal.execute(
            "SELECT ID_EQUIPO FROM ListaEquipos WHERE ORDEN = %s", (fila,))
        if cursor_dorsal.rowcount != 1:
            raise RuntimeError("Error en función de cambio de estado.")
        dorsal = cursor_dorsal.fetchone()[0]
        # Determinamos el estado de registro del equipo, para alternarlo.
        cursor_estado.execute(
            "SELECT registrado FROM Equipo WHERE ID_EQUIPO = %s", (dorsal,))
        if cursor_estado.rowcount != 1:
            raise RuntimeError("Error en función de cambio de estado.")
        estado_actual = cursor_estado.fetchone()[0]
        return estado_actual

    def datos_equipo(self, fila):
        """
        Obtiene los datos del equipo a partir de la fila en la tabla

        """
        cursor = self.__conexion.cursor(dictionary=False, prepared=True)
        cursor.execute(
            "SELECT ID_EQUIPO, equipo FROM ListaEquipos WHERE ORDEN = %s",
            (fila,))

        nombre = cursor.fetchone()
        return nombre[0], nombre[1]

    def resumen_equipos(self):
        """
        Estadísticas del proceso de homologación.

        """
        cursor = self.__conexion.cursor(dictionary=True, prepared=True)
        cursor.execute("SELECT * FROM ResumenHomologacionEquipos")
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
            "SELECT * FROM ListaPuntosHomologacion WHERE "
            "ID_EQUIPO = %s AND FK_HOMOLOGACION_ZONA = %s", (equipo, zona))

        lista = cursor.fetchall()
        return lista

    def actualizar_punto_homologacion(self, equipo, punto, zona):
        """
        Alterna el valor de un punto de homologación entre True y False

        """
        cursor_get = self.__conexion.cursor(dictionary=False, prepared=True)
        cursor_set = self.__conexion.cursor(dictionary=False, prepared=True)
        cursor_get.execute(
            "SELECT valor FROM ListaPuntosHomologacion WHERE "
            "ID_EQUIPO = %s AND ID_HOMOLOGACION_PUNTO = %s AND "
            "FK_HOMOLOGACION_ZONA = %s", (equipo, punto, zona))

        if cursor_get.rowcount != 1:
            raise RuntimeError("Error al actualizar punto de homoloación.")
        valor = cursor_get.fetchone()[0]

        valor = 0 if valor == 1 else 1
        cursor_set.execute(
            "UPDATE HomologacionEquipo SET valor = %s WHERE "
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
                "SELECT * FROM Equipo WHERE ID_EQUIPO = %s FOR UPDATE NOWAIT",
                (equipo,))
            cursor_puntos.execute(
                "SELECT * FROM HomologacionEquipo WHERE FK_EQUIPO = %s "
                "FOR UPDATE NOWAIT", (equipo,))
        except mariadb.OperationalError as e:
            # Detectamos si el equipo se encuentra bloqueado por otro usuario.
            if e.errno == 1205:
                raise BlockingIOError(
                    "El equipo está bloqueado por otro usuario. "
                    "Espere a que termine para poder continar.")

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

################################################################################
################################################################################
################################################################################

    def get_cabecera(self, columna):
        cursor = self.__conexion.cursor(dictionary=False, prepared=False)
        cursor.execute("SELECT %s FROM ConfigVistaListaEquipos" % columna)
        lista = cursor.fetchall()
        datos = [fila[0] for fila in lista]
        return datos

    def get_cabecera_nombre(self):
        return self.get_cabecera("nombre")

    def get_cabecera_ancho(self):
        return self.get_cabecera("ancho")

    def get_cabecera_alineacion(self):
        return self.get_cabecera("alineacion")

    def get_cabecera_ajuste(self):
        return self.get_cabecera("ajuste")

    def get_cabecera_eventos(self):
        return self.get_cabecera("zona")

    cabecera_nombre = property(get_cabecera_nombre, None, None, None)
    cabecera_ancho = property(get_cabecera_ancho, None, None, None)
    cabecera_alineacion = property(get_cabecera_alineacion, None, None, None)
    cabecera_ajuste = property(get_cabecera_ajuste, None, None, None)
    cabecera_eventos = property(get_cabecera_eventos, None, None, None)


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
