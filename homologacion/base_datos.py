'''
Created on 4 feb 2025

@author: pedrogil
'''

from enum import IntEnum

import mariadb


class estado(IntEnum):
    INSCRITO = 1
    REGISTRADO = 2
    HOMOLOGADO = 3


# Nombre de la vista en la que aparece en función del estado del equipo.
ESTADO = {
    1: "ListaEquiposRegistrados",
    2: "ListaEquiposInscritos",
    3: "ListaEquiposHomologados"}


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
        self.__conexion.rollback()
        cursor = self.__conexion.cursor(dictionary=False, prepared=False)
        # cursor.execute("SELECT * FROM ListaEquiposInscritos")
        cursor.execute("SELECT * FROM %s" % ESTADO[estado])
        equipos = cursor.fetchall()
        return equipos

    def cabecera_vista_equipos(self):
        cursor = self.__conexion.cursor(dictionary=True, prepared=True)
        cursor.execute("SHOW COLUMNS FROM ListaEquiposRegistrados")
        lista_cabecera = cursor.fetchall()
        cabecera = [columna["Field"] for columna in lista_cabecera[1:]]
        return cabecera
