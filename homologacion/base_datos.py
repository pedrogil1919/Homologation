'''
Created on 4 feb 2025

@author: pedrogil
'''

from enum import IntEnum

import mariadb


class estado(IntEnum):
    TODOS = 1
    INSCRITO = 2
    REGISTRADO = 3
    HOMOLOGADO = 4


# Nombre de la vista en la que aparece en función del estado del equipo.
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

        # Guardamos los datos en el objeto.
        self.__user = user
        self.__host = host
        self.__database = database

    def __str__(self):
        """
        Devuelve los datos informativos de la conexión.

        """
        return "%s (%s) - Usuario: %s" % (self.__database, self.__host, self.__user)

    def abrir_transaccion(self):
        self.__conexion.autocommit = False

    def cerrar_transaccion(self):
        self.__conexion.commit()
        self.__conexion.autocommit = True

    def cancelar_transaccion(self):
        self.__conexion.rollback()
        self.__conexion.autocommit = True

    def registrar_equipo(self, fila, estado_actual):
        """
        Alterna el estado de registro de un equipo

        Argumentos:
        - fila: fila a la que corresponde el equipo. Tener en cuenta que el
          número de fila no se corresponde con el dorsal, por lo que es
          necesario determinar el dorsal a partir de la fila.

        """
        cursor_dorsal = self.__conexion.cursor(
            dictionary=False, prepared=False)
        cursor_equipo = self.__conexion.cursor(prepared=True)
        cursor_dorsal.execute(
            "SELECT ID_EQUIPO FROM ListaEquipos WHERE ORDEN = %s", (fila,))
        if cursor_dorsal.rowcount != 1:
            raise RuntimeError("Error en función de cambio de estado.")
        dorsal = cursor_dorsal.fetchone()[0]
        estado_nuevo = 1 if (estado_actual == estado.INSCRITO) else 0
        cursor_equipo.execute(
            "UPDATE Equipo SET registrado=%s WHERE ID_EQUIPO=%s", (estado_nuevo, dorsal))
        if cursor_equipo.affected_rows != 1:
            raise RuntimeError("Error en función de cambio de estado.")
        self.__conexion.commit()

    def lista_equipos(self, estado):
        # self.__conexion.rollback()
        cursor = self.__conexion.cursor(dictionary=False, prepared=False)
        # cursor.execute("SELECT * FROM ListaEquiposInscritos")
        filtro_registrado = ESTADO[estado][0]
        filtro_homologado = ESTADO[estado][1]
        consulta = "SELECT * FROM ListaEquipos WHERE registrado IN (%s) AND homologado IN (%s)" % (
            format(", ".join(map(str, filtro_registrado))), format(", ".join(map(str, filtro_homologado))))
        cursor.execute(consulta)
        equipos = cursor.fetchall()
        return equipos

    def configuracion_tabla(self):
        cursor = self.__conexion.cursor(dictionary=True, prepared=True)
        cursor.execute("SELECT * FROM ConfigVistaListaEquipos")
        lista = cursor.fetchall()
        cabecera = [fila["nombre"] for fila in lista]
        ancho = [fila["ancho"] for fila in lista]
        alineacion = [fila["alineacion"] for fila in lista]
        ajuste = [fila["ajuste"] for fila in lista]

        return cabecera, ancho, alineacion, ajuste

    def configuracion_eventos(self):
        cursor = self.__conexion.cursor(dictionary=False, prepared=True)
        cursor.execute("SELECT zona FROM ConfigVistaListaEquipos")
        lista = cursor.fetchall()
        eventos = [fila[0] for fila in lista]

        return eventos

    def datos_equipo(self, equipo):
        """
        Obtiene los datos del equipo a partir de su ID

        """
        cursor = self.__conexion.cursor(dictionary=False, prepared=True)
        cursor.execute(
            "SELECT ID_EQUIPO, equipo FROM ListaEquipos WHERE ORDEN = %s", (equipo,))

        nombre = cursor.fetchone()
        return nombre[0], nombre[1]

    def lista_puntos_homologacion(self, equipo, zona):
        cursor = self.__conexion.cursor(dictionary=True, prepared=True)
        cursor.execute(
            "SELECT * FROM ListaPuntosHomologacion WHERE "
            "ID_EQUIPO = %s AND FK_HOMOLOGACION_ZONA = %s", (equipo, zona))

        lista = cursor.fetchall()
        return lista

    def actualizar_putno_homologacion(self, equipo, punto, zona):
        cursor1 = self.__conexion.cursor(dictionary=False, prepared=True)
        cursor2 = self.__conexion.cursor(dictionary=False, prepared=True)
        cursor1.execute(
            "SELECT valor FROM ListaPuntosHomologacion WHERE "
            "ID_EQUIPO = %s AND ID_HOMOLOGACION_PUNTO = %s AND "
            "FK_HOMOLOGACION_ZONA = %s", (equipo, punto, zona))

        if cursor1.rowcount != 1:
            raise RuntimeError("Error al actualizar punto de homoloación.")
        valor = cursor1.fetchone()[0]

        valor = 0 if valor == 1 else 1
        cursor2.execute(
            "UPDATE HomologacionEquipo SET valor = %s WHERE "
            "FK_EQUIPO = %s AND FK_HOMOLOGACION_PUNTO = %s AND "
            "FK_HOMOLOGACION_ZONA = %s", (valor, equipo, punto, zona))

        if cursor2.affected_rows != 1:
            raise RuntimeError("Error al actualizar punto de homoloación.")

        return valor
