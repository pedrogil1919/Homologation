'''
Created on 7 mar 2025

@author: pedrogil
'''

from magic.compat import NONE
import tkinter


class Etiqueta(tkinter.Label):
    indentacion = 20

    @staticmethod
    def funcion_color(v, c): return None
    '''
    classdocs
    '''

    def __init__(self, marco, punto, fila, nivel, seccion, valor,
                 descendientes, **kwargs):
        super().__init__(marco, **kwargs)
        self.__punto = punto
        self.__fila = fila
        self.__nivel = nivel
        self.__seccion = seccion
        self.__valor = valor
        self.__descendientes = descendientes
        self.añadir()

    def añadir(self):
        self.grid(
            row=self.__fila, column=0, sticky="nsew",
            padx=(2*(self.__nivel-1)*self.indentacion, 1), pady=1)

    def actualizar(self, valor=None):
        if valor is not None:
            self.__valor = valor
        # Y al mismo tiempo determinamos el color con el que representarlo en
        # la página.
        color = self.funcion_color(self.__valor, self.__seccion)
        self.config(bg=color)
        # Si se trata de una sección, tendremos que ocultar o mostrar los
        # puntos que dependen de esta sección.
        if self.__seccion == 0:
            if self.__valor == 0:
                for d in self.__descendientes:
                    d.grid_forget()
            else:
                for d in self.__descendientes:
                    d.añadir()
                    d.actualizar()
