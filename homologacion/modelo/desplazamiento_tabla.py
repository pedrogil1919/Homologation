'''
Created on 25 feb 2025

Clase para implementar las funciones de desplazamiento vertical de una ventana
(scroll) dentro de un canvas.

@author: pedrogil
'''

import sys


class Desplazamiento(object):

    def __init__(self, canvas, marco, barra):
        """
        Constructor. Necesita almacenar las referencias al canvas, el marco
        que hay que desplazar, y la barra de desplazamiento vertical. 

        """
        self.__canvas = canvas
        self.__marco = marco
        self.__barra = barra
        self.desp_vertical = True

################################################################################
################################################################################
    #  Definición de eventos relacionados con el desplazamiento vertical
    # de la tabla cuando existen más filas de las que caben.
################################################################################
################################################################################
    def __teclas_cursor(self, event=None):
        """
        Desplazamiento con las teclas de cursor.

        """
        if event.keysym == "Up":
            self.__canvas.yview_scroll(-1, "units")  # Mover hacia arriba
        elif event.keysym == "Down":
            self.__canvas.yview_scroll(1, "units")  # Mover hacia abajo

    def __rueda_raton(self, event=None):
        """
        Desplazamiento con el ratón.

        """
        if sys.platform == "Windows":  # Windows
            self.__canvas.yview_scroll(-int(event.delta / 120), "units")
        elif sys.platform == "Darwin":  # macOS
            self.__canvas.yview_scroll(-int(event.delta), "units")
        elif sys.platform == "linux" or sys.platform == "linux2":  # Linux
            if event.num == 4:
                self.__canvas.yview_scroll(-1, "units")  # Scroll up
            elif event.num == 5:
                self.__canvas.yview_scroll(1, "units")  # Scroll down

    def __get_desp_vertical(self):
        return self.__desp_vertical

    def __set_desp_vertical(self, habilitar):
        """
        Configuración global

        """
        if habilitar is not None:
            # Guardamos la opción seleccionada en la variable global.
            self.__desp_vertical = habilitar
        # Y configuramos todo el sistema de desplazamiento vertical.
        self.__configurar_desp_vertical()

    def __configurar_desp_vertical(self):
        """
        Configuración de todos los sistemas de desplazamiento.

        """
        # Obtenmemos las alturas de ambos cuadros.
        alto_tabla = self.__marco.winfo_reqheight()
        alto_canvas = self.__canvas.winfo_height()
        if not self.__desp_vertical or alto_tabla <= alto_canvas:
            # Si el marco es más pequeño que el Canvas, deshabilitamos todas
            # las funciones de desplazamiento vertical.
            # O si el se ha seleccionado no desplazar, también lo
            # deshabilitamos.
            # NOTA: En ocasiones puede ocurrir que si la tabla tiene muchos
            # elementos y estamos muy abajo en la tabla, y pasamos a tener
            # muy pocos elementos, de tal forma que no es necesario el
            # desplazamiento, la tabla desaparece. Por ese motivo, hacemos el
            # desplazar el canvas al origen, y de esa forma ya funciona (no se
            # sabe la causa de esto).
            # Sin embargo, sólo desplazamos si el cambio viene motivado por una
            # reducción en el tamaño de la tabla, no porque el usuario haya
            # solicitado deshabilitar el desplazamiento.
            if self.__desp_vertical:
                self.__canvas.yview("moveto", 0.0)
            # Deshabilitamos el desplazamiento con la rueda del ratón
            self.__canvas.unbind_all("<MouseWheel>")
            self.__canvas.unbind_all("<Button-4>")
            self.__canvas.unbind_all("<Button-5>")
            # Deshabilitamos el desplazamiento con las teclas de cursor.
            self.__canvas.unbind_all("<Up>")
            self.__canvas.unbind_all("<Down>")
            # Ocultamos la barra de desplazamiento
            self.__barra.grid_forget()
        else:
            # En caso de que el marco sea más grande que el canvas:
            # habilitamos el desplazamiento con la rueda del ratón.
            if sys.platform == "linux" or sys.platform == "linux2":
                self.__canvas.bind_all("<Button-4>", self.__rueda_raton)
                self.__canvas.bind_all("<Button-5>", self.__rueda_raton)
            elif sys.platform == "win32" or "darwin":
                self.__canvas.bind_all("<MouseWheel>", self.__rueda_raton)
            # Habilitamos el desplazamiento con las teclas de cursor.
            self.__canvas.bind_all("<Up>", self.__teclas_cursor)
            self.__canvas.bind_all("<Down>", self.__teclas_cursor)
            # Mostramos la barra de desplazamiento
            self.__barra.grid(row=0, column=1, sticky="ns")

    desp_vertical = property(
        __get_desp_vertical, __set_desp_vertical, None, None)
