"""
Created on 4 apr 2025

Funciones para leer datos de conexión y contraseñas

@author: pedrogil

"""

from xml.etree import ElementTree

from leer_constantes import captura_error


archivo_xml = None

################################################################################
# FUNCIONES DE LECTURA DEL ARCHIVO DE CONFIGURACIÓN
################################################################################


def abrir_xml_conexion(archivo):
    """
    Abrir y guardar en el módulo el archivo xml de configuración.

    """
    global archivo_xml
    global nombre_xml
    try:
        archivo_xml = ElementTree.parse(archivo)
    except ElementTree.ParseError as error:
        raise RuntimeError("Error archivo XML %s: %s." % (archivo, error))


@captura_error
def leer_conexion():
    raiz = archivo_xml.getroot()
    elemento = raiz.find("homologacion")
    datos_conexion = {
        "HOST": elemento.attrib["HOST"],
        "BASE": elemento.attrib["BASE"],
        "USER": elemento.attrib["USER"],
        "PASS": elemento.attrib["PASS"],
        "TIME": int(elemento.attrib["TIMEOUT"])}
    return datos_conexion
