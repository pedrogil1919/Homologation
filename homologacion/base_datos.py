'''
Created on 4 feb 2025

@author: pedrogil
'''

import mariadb


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

    def equipos_registrados(self):
        self.__conexion.rollback()
        cursor = self.__conexion.cursor(dictionary=False, prepared=True)
        cursor.execute("SELECT * FROM ListaEquiposHomologacion")
        equipos = cursor.fetchall()
        return equipos

    def cabecera_vista_equipos(self):
        cursor = self.__conexion.cursor(dictionary=True, prepared=True)
        cursor.execute("SHOW COLUMNS FROM ListaEquiposHomologacion")
        cabecera = cursor.fetchall()
        return cabecera[1:]
