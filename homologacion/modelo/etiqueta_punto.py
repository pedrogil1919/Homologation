'''
Created on 7 mar 2025

Widget derivado de Label, para incluir la funcionalidad requerida a éstas
cuando el punto o la sección cambian de valor.

@author: pedrogil

'''

import tkinter


class Etiqueta(tkinter.Label):
    # Variable global, que especifica el número de píxeles a indentar en función
    # del nivel de cada uno de los puntos.
    indentacion = 20

    # Función global para determinar el color de una etiqueta en función de
    # su valor.
    @staticmethod
    def funcion_color(v, c): return None

    def __init__(self, marco, punto, fila, nivel, seccion, valor,
                 descendientes, **kwargs):
        """
        Argumentos:
        - marco: marco donde insertar la etiqueta.
        - punto: índide de la base de datos del punto
        - fila: fila que ocupa la etiqueta dentro del marco anterior.
        - nivel: nivel dentro de la jerarquía de puntos y secciones.
        - seccion: Si es 0, indica que se trata de una sección y no de un punto.
        - valor: valor actual, para asignarle el aspecto correspondiente en
          función de su valor.
        - descedientes: lista de Etiquetas que son descendientes de esta
          sección, si lo es.

        """
        super().__init__(marco, **kwargs)
        self.__punto = punto
        self.__fila = fila
        self.__nivel = nivel
        self.__seccion = seccion
        self.__valor = valor
        self.__descendientes = descendientes
        # En el propio constructor añadimos y hacemos visible la etiqueta en el
        # marco anterior.
        self.añadir()

    def añadir(self):
        """
        Añade la etiqueta al marco, mediante grid.

        """
        self.grid(
            row=self.__fila, column=0, sticky="nsew",
            padx=(1 + 2*(self.__nivel-1)*self.indentacion, 1), pady=1)

    def actualizar(self, valor=None):
        """
        Acualiza el aspecto de la etiqueta y de sus descendidentes.

        Si valor no es None, se actualiza el valor de la etiqueta, y su aspecto,
        si es None, sólo actualiza su aspecto.

        """
        # Actualizamos el valor de este punto.
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
                # Si valor es False, tenemos que ocultar todos sus
                # descendientes.
                for d in self.__descendientes:
                    d.grid_forget()
            else:
                # Pero si el valor es True, tenemos que volver a mostrar sus
                # descendientes.
                for d in self.__descendientes:
                    d.añadir()
                    # Pero como es posible que alguno de sus descendientes sea
                    # una sección, y es posible que esté a False, tenemos que
                    # actualizar todos sus descendientes.
                    # NOTA: En relación a esto, cualquier etiqueta que esté a
                    # más de un nivel de profundidad, ejecutará el mensaje de
                    # añadir (grid) más de una vez, pero por suerte, tkinter
                    # no se ve afectado si llamamos a grid más de una vez sobre
                    # la misma etiqueta.
                    d.actualizar()
