"""
Created on 9 may 2024

Funciones para leer y guardar datos del archivo xml de configuración.

@author: pedrogil

"""
from tkinter import messagebox
from xml.etree import ElementTree


# Nombre del archivo xml, por si queremos modificar su contenido
nombre_xml = None
# Raíz del contenido del archivo xml
archivo_xml = None

# Definición de una función que emplearemos como decorator, para seguir la
# misma estrategia en todas las funciones de lectura del archivo xml en caso de
# error en el propio archivo xml.


def captura_error(funcion_leer_xml):
    """
    Función decorator

    Esta función realiza la llamada a la función de lectura de algún campo xml,
    capturando el error que genera el propio archivo, y sacando un mensaje por
    pantalla en caso de error en el archivo.

    """
    def control(argumento=None):
        try:
            # Llamamos a la función de lectura del xml.
            if argumento is None:
                # NOTA: Si el argumento es None, se supone que estamos
                # realizando la llamada a una función que no acepta argumentos.
                res = funcion_leer_xml()
            else:
                # Sin embargo, si no es None, es una función que acepta un
                # argumento.
                res = funcion_leer_xml(argumento)
            # Y devolvemos los datos leidos.
            return res
        except (AttributeError, KeyError):
            # Si hay algún error en el archivo xml, como que falta la clave o
            # el parámetro, mostramos un mensaje de error.
            messagebox.showerror(
                "Error configuración",
                "Error en el archivo de configuración %s. "
                "Revisar parámetros de la función '%s'" %
                (nombre_xml, funcion_leer_xml.__name__))
            exit(1)
    return control


def abrir_archivo_xml(archivo):
    """
    Abrir y guardar en el módulo el archivo xml de configuración.

    """
    global archivo_xml
    global nombre_xml
    try:
        archivo_xml = ElementTree.parse(archivo)
        nombre_xml = archivo
    except ElementTree.ParseError as error:
        raise RuntimeError("Error archivo XML %s: %s." % (archivo, error))

################################################################################
# FUNCIONES DE LECTURA DEL ARCHIVO DE CONFIGURACIÓN
################################################################################


@captura_error
def leer_ventana_inicio():
    raiz = archivo_xml.getroot()
    elemento = raiz.find("graficos")
    directorio = elemento.attrib["DIRECTORIO"]
    elemento = elemento.find("inicio")
    directorio += elemento.attrib["DIRECTORIO"]
    imagen = elemento.attrib["IMAGEN"]
    tiempo = float(elemento.attrib["TIEMPO"])
    return directorio, imagen, tiempo


@captura_error
def leer_cabecera():
    raiz = archivo_xml.getroot()
    elemento = raiz.find("cabecera")
    datos_cabecera = {}
    for columna in elemento:
        datos_cabecera[columna.tag] = columna.attrib
    return datos_cabecera


@captura_error
def leer_fuente(zona=""):
    raiz = archivo_xml.getroot()
    if zona == "":
        elemento = raiz.find("fuente")
    else:
        elemento = raiz.find("fuente_%s" % zona)
    datos_fuente = (
        elemento.attrib["FAMILIA"],
        int(elemento.attrib["TAMAÑO"]),
        elemento.attrib["ESTILO"])
    color_fuente = elemento.attrib["COLOR"]
    return datos_fuente, color_fuente


@captura_error
def leer_colores_puntos():
    raiz = archivo_xml.getroot()
    elemento = raiz.find("colores_puntos")
    lista_colores = {
        "COLOR_SI": elemento.attrib["COLOR_SI"],
        "COLOR_NO": elemento.attrib["COLOR_NO"],
        "COLOR_SC": elemento.attrib["COLOR_SC"],
        "COLOR_NP": elemento.attrib["COLOR_NP"]
    }
    return lista_colores


@captura_error
def leer_colores_tabla():
    raiz = archivo_xml.getroot()
    elemento = raiz.find("colores_tabla")

    lista_colores = {
        "BORDE": elemento.attrib["BORDE"],
        "FONDO": elemento.attrib["FONDO"],
        "CABECERA": elemento.attrib["CABECERA"],
        "FILAS": elemento.attrib["FILAS"]}

    return lista_colores


@captura_error
def leer_logos():
    raiz = archivo_xml.getroot()
    elemento = raiz.find("graficos")
    directorio = elemento.attrib["DIRECTORIO"]
    elemento = elemento.find("logos")
    directorio += elemento.attrib["DIRECTORIO"]
    cabecera = directorio + elemento.attrib["CABECERA"]
    logo = directorio + elemento.attrib["FONDO"]
    icono = directorio + elemento.attrib["ICONO"]
    return {
        "CABECERA": cabecera,
        "ICONO": icono,
        "LOGO": logo}


@captura_error
def leer_ancho_pagina():
    raiz = archivo_xml.getroot()
    elemento = raiz.find("pagina")
    return int(elemento.attrib["ANCHO"])


@captura_error
def leer_margen_pagina():
    raiz = archivo_xml.getroot()
    elemento = raiz.find("pagina")
    return int(elemento.attrib["MARGENX"]), int(elemento.attrib["MARGENY"])


##############################################################
