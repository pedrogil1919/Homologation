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
    def control():
        try:
            # Llamamos a la función de lectura del xml.
            res = funcion_leer_xml()
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
def leer_conexion():
    raiz = archivo_xml.getroot()
    elemento = raiz.find("conexion")
    datos_conexion = {
        "HOST": elemento.attrib["HOST"],
        "BASE": elemento.attrib["BASE"],
        "USER": elemento.attrib["USER"],
        "PASS": elemento.attrib["PASS"],
        "SAVE": (elemento.attrib["SAVE"] == "TRUE")}
    return datos_conexion


@captura_error
def leer_campos():
    raiz = archivo_xml.getroot()
    elemento = raiz.find("conexion")
    campos = ()
    datos_campos = elemento.findall("campo")
    for campo in datos_campos:
        campos += (int(campo.attrib["id"]),)

    return campos


@captura_error
def leer_arbitros():
    raiz = archivo_xml.getroot()
    elemento = raiz.find("conexion")
    arbitros = ()
    datos_arbitros = elemento.findall("arbitro")
    for arbitro in datos_arbitros:
        arbitros += (int(arbitro.attrib["id"]),)
    return arbitros


@captura_error
def leer_partidos():
    raiz = archivo_xml.getroot()
    elemento = raiz.find("partidos")
    datos_partidos = {
        "TIPO_ACCESO":     elemento.attrib["TIPO_ACCESO"],
        "TIEMPO_CONEXION": elemento.attrib["TIEMPO_CONEXION"]}
    return datos_partidos


@captura_error
def leer_pantalla_resultado():
    raiz = archivo_xml.getroot()
    elemento = raiz.find("resultados")
    tiempo = [int(elemento.attrib["TIEMPO_REFRESCO"]),
              int(elemento.attrib["TIEMPO_APAGADO"])]
    # Comprobamos si debemos subir el resultado al servidor
    if elemento.attrib["PNG_GUARDAR"] == "False":
        return None, tiempo
    datos_servidor_ftp = {
        "PNG_HOST": elemento.attrib["PNG_HOST"],
        "PNG_USER": elemento.attrib["PNG_USER"],
        "PNG_DIR":  elemento.attrib["PNG_DIR"],
        "PNG_PASS": elemento.attrib["PNG_PASS"]}
    return datos_servidor_ftp, tiempo


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
def leer_iconos():
    raiz = archivo_xml.getroot()
    elemento = raiz.find("graficos")
    directorio = elemento.attrib["DIRECTORIO"]
    acciones = directorio + elemento.attrib["ACCIONES"]
    elemento = elemento.find("iconos")
    directorio += elemento.attrib["DIRECTORIO"]
    datos_iconos = {
        "ICONO_CONECTAR":    elemento.attrib["ICONO_CONECTAR"],
        "ICONO_GUARDAR":     elemento.attrib["ICONO_GUARDAR"],
        "ICONO_FINALIZAR":   elemento.attrib["ICONO_FINALIZAR"],
        "ICONO_DESCONECTAR": elemento.attrib["ICONO_DESCONECTAR"],
        "ICONO_RESULTADO":   elemento.attrib["ICONO_RESULTADO"],
        "ICONO_CERRAR":      elemento.attrib["ICONO_CERRAR"],
        "ICONO_MARCAR":      elemento.attrib["ICONO_MARCAR"],
        "ICONO_LUPA_MAS":    elemento.attrib["ICONO_LUPA_MAS"],
        "ICONO_LUPA_MENOS":  elemento.attrib["ICONO_LUPA_MENOS"],
        "ICONO_GIRAR":       elemento.attrib["ICONO_GIRAR"]}
    return directorio, acciones, datos_iconos


@captura_error
def leer_logos():
    raiz = archivo_xml.getroot()
    elemento = raiz.find("graficos")
    directorio = elemento.attrib["DIRECTORIO"]
    elemento = elemento.find("logos")
    directorio += elemento.attrib["DIRECTORIO"]
    datos_logos = {
        "TITULO":           elemento.attrib["TITULO"],
        "ICONO":            elemento.attrib["ICONO"],
        "LOGO_FONDO":       elemento.attrib["LOGO_FONDO"],
        "LOGO_CABECERA":    elemento.attrib["LOGO_CABECERA"],
        "COLOR_LOGO_FONDO": elemento.attrib["COLOR_LOGO_FONDO"],
        "MAPA":             elemento.attrib["MAPA"],
        "COLOR_FONDO":      elemento.attrib["COLOR_FONDO"]}
    return directorio, datos_logos


@captura_error
def leer_equipos():
    raiz = archivo_xml.getroot()
    elemento = raiz.find("graficos")
    directorio = elemento.attrib["DIRECTORIO"]
    elemento = elemento.find("equipos")
    directorio += elemento.attrib["DIRECTORIO"]
    return directorio


@captura_error
def leer_atajos():
    raiz = archivo_xml.getroot()
    elemento = raiz.find("teclado")
    datos_atajos = {}
    for atajo in elemento.findall("atajo"):
        datos_atajos[int(atajo.attrib["ARBITRO"])] = atajo.attrib["ARCHIVO"]
    return datos_atajos


@captura_error
def leer_escalado():
    raiz = archivo_xml.getroot()
    elemento = raiz.find("escalado")
    datos_escalado = {
        "ZOOM":     (elemento.attrib["ZOOM"] == "TRUE"),
        "BORDE":    int(elemento.attrib["BORDE"]),
        "BARRA":    (elemento.attrib["BARRA"] == "TRUE"),
        "VERTICAL": (elemento.attrib["VERTICAL"] == "TRUE"),
        "GIRAR":    (elemento.attrib["GIRAR"] == "TRUE")}
    return datos_escalado


@captura_error
def leer_fuente():
    raiz = archivo_xml.getroot()
    elemento = raiz.find("fuente")
    datos_fuente = (
        elemento.attrib["FAMILIA"],
        int(elemento.attrib["TAMAÑO"]),
        elemento.attrib["ESTILO"])
    return datos_fuente

################################################################################
# FUNCIONES DE ESCRITURA DEL ARCHIVO DE CONFIGURACIÓN
################################################################################


def guardar_arbitros(lista_arbitros):
    raiz = archivo_xml.getroot()
    elemento = raiz.find("conexion")
    datos_arbitros = elemento.findall("arbitro")
    # Eliminar todos los registros de arbitros.
    for arbitro in datos_arbitros:
        elemento.remove(arbitro)
    # Y añadir los nuevos registros.
    for arbitro in lista_arbitros:
        if arbitro["valor"]:
            nuevo_arbitro = ElementTree.Element("arbitro")
            nuevo_arbitro.set("id", str(arbitro["ID_ARBITRO"]))
            elemento.append(nuevo_arbitro)
    archivo_xml.write(nombre_xml)


def guardar_campos(lista_campos):
    raiz = archivo_xml.getroot()
    elemento = raiz.find("conexion")
    datos_campos = elemento.findall("campo")
    for campo in datos_campos:
        elemento.remove(campo)
    # Y añadir los nuevos registros.
    for campo in lista_campos:
        if campo["valor"]:
            nuevo_campo = ElementTree.Element("campo")
            nuevo_campo.set("id", str(campo["ID_CAMPO"]))
            elemento.append(nuevo_campo)
    archivo_xml.write(nombre_xml)
