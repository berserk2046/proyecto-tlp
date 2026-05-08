# -*- coding: utf-8 -*-
# runtime.py (Snake con evento X2 temporal)

import sys
import json
import time
import random
import Tkinter as tk
import tkMessageBox

class Juego:

    def __init__(self, datos_juego):

        self.datos_juego = datos_juego

        self.tipo_juego = self.datos_juego.get('tipo_juego', 'SNAKE')

        config = self.datos_juego.get('config', {})

        self.ancho = config.get('grid_size', [18, 18])[0]
        self.alto = config.get('grid_size', [18, 18])[1]

        self.grid = [[0 for _ in range(self.ancho)] for _ in range(self.alto)]

        self.puntuacion = 0
        self.juego_terminado = False

        # ---------------- GUI ----------------

        self.root = tk.Tk()

        self.root.title("BrickScript - Snake X2")

        self.root.protocol("WM_DELETE_WINDOW", self.cerrar_ventana)

        self.taman_celda = 25

        self.ancho_canvas = self.ancho * self.taman_celda
        self.alto_canvas = self.alto * self.taman_celda

        self.canvas = tk.Canvas(
            self.root,
            width=self.ancho_canvas,
            height=self.alto_canvas,
            bg='#111111'
        )

        self.canvas.pack(side=tk.LEFT, padx=10, pady=10)

        self.marco_score = tk.Frame(
            self.root,
            width=150,
            height=self.alto_canvas,
            bg='#222222'
        )

        self.marco_score.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)

        self.label_score = tk.Label(
            self.marco_score,
            text="PUNTUACION\n0",
            bg='#222222',
            fg='white',
            font=('Consolas', 16, 'bold')
        )

        self.label_score.pack(pady=40, padx=10)

        self.label_controles = tk.Label(
            self.marco_score,
            text="CONTROLES\nFlechas: Mover",
            bg='#222222',
            fg='gray',
            font=('Consolas', 10)
        )

        self.label_controles.pack(pady=20, padx=10)

        self.root.bind('<Key>', self.manejar_input_gui)

        # ---------------- SNAKE ----------------

        self.serpiente_cuerpo = []
        self.serpiente_direccion = (1, 0)

        self.posicion_comida = None

        self.velocidad_normal = 0.15
        self.velocidad_x2 = 0.07

        self.velocidad_gravedad = self.velocidad_normal

        # ---------------- SISTEMA X2 ----------------

        self.modo_x2 = False

        self.color_comida = '#FF0000'

        self.tiempo_x2 = 0

        self.duracion_x2 = 5

        self.timer_gravedad = 0

        self.ejecutar_evento('ON_START')

        self.timer_id = None

    # --------------------------------------------------

    def run(self):

        self.root.after(50, self.game_loop)

        self.root.mainloop()

    # --------------------------------------------------

    def game_loop(self):

        if self.juego_terminado:

            self.mostrar_game_over()

            return

        self.timer_gravedad += 0.05

        if self.timer_gravedad >= self.velocidad_gravedad:

            self.timer_gravedad = 0

            self.ejecutar_evento('ON_TICK')

        # DESACTIVAR X2
        if self.modo_x2:

            if time.time() - self.tiempo_x2 >= self.duracion_x2:

                self.modo_x2 = False

                self.velocidad_gravedad = self.velocidad_normal

                self.color_comida = '#FF0000'

                print "X2 DESACTIVADO"

        self.dibujar()

        self.timer_id = self.root.after(50, self.game_loop)

    # --------------------------------------------------

    def cerrar_ventana(self):

        if self.timer_id:

            self.root.after_cancel(self.timer_id)

        self.root.destroy()

        sys.exit(0)

    # --------------------------------------------------

    def manejar_input_gui(self, event):

        key = event.keysym.upper()

        if key == 'UP':

            self.snake_cambiar_direccion('UP')

        elif key == 'DOWN':

            self.snake_cambiar_direccion('DOWN')

        elif key == 'LEFT':

            self.snake_cambiar_direccion('LEFT')

        elif key == 'RIGHT':

            self.snake_cambiar_direccion('RIGHT')

    # --------------------------------------------------

    def dibujar(self):

        self.canvas.delete("all")

        self.label_score.config(
            text="PUNTUACION\n" + str(self.puntuacion)
        )

        COLOR_SNAKE_CABEZA = '#00FF00'
        COLOR_SNAKE_CUERPO = '#33CC33'

        COLOR_FOOD = self.color_comida

        # COMIDA
        if self.posicion_comida:

            x, y = self.posicion_comida

            self.dibujar_celda(x, y, COLOR_FOOD)

        # SERPIENTE
        for i, segmento in enumerate(self.serpiente_cuerpo):

            x, y = segmento

            color = COLOR_SNAKE_CABEZA if i == 0 else COLOR_SNAKE_CUERPO

            self.dibujar_celda(x, y, color)

    # --------------------------------------------------

    def dibujar_celda(self, x, y, color):

        ts = self.taman_celda

        x1 = x * ts
        y1 = y * ts

        x2 = x1 + ts
        y2 = y1 + ts

        self.canvas.create_rectangle(
            x1,
            y1,
            x2,
            y2,
            fill=color,
            outline='#000000'
        )

    # --------------------------------------------------

    def ejecutar_evento(self, nombre_evento):

        if nombre_evento in self.datos_juego['events']:

            for accion in self.datos_juego['events'][nombre_evento]:

                verbo = accion.get('accion')

                objeto = accion.get('objeto')

                if verbo == 'GAME_OVER':

                    self.juego_terminado = True

                if verbo == 'SPAWN' and objeto == 'PLAYER':

                    self.snake_spawn_jugador(accion)

                if verbo == 'SPAWN' and objeto == 'FOOD':

                    self.snake_spawn_comida()

                if verbo == 'MOVE' and objeto == 'PLAYER':

                    self.snake_mover_jugador()

    # --------------------------------------------------

    def snake_spawn_jugador(self, accion):

        coords = accion['params'][0]

        self.serpiente_cuerpo = [(coords[0], coords[1])]

        self.serpiente_direccion = (1, 0)

    # --------------------------------------------------

    def snake_spawn_comida(self):

        while True:

            x = random.randint(0, self.ancho - 1)

            y = random.randint(0, self.alto - 1)

            if (x, y) not in self.serpiente_cuerpo:

                self.posicion_comida = (x, y)

                break

    # --------------------------------------------------

    def snake_mover_jugador(self):

        if not self.serpiente_cuerpo:

            return

        cabeza_x, cabeza_y = self.serpiente_cuerpo[0]

        dir_x, dir_y = self.serpiente_direccion

        nueva_cabeza = (
            cabeza_x + dir_x,
            cabeza_y + dir_y
        )

        # COLISION PARED
        if not (
            0 <= nueva_cabeza[0] < self.ancho and
            0 <= nueva_cabeza[1] < self.alto
        ):

            self.ejecutar_evento('ON_COLLISION_WALL')

            return

        # COLISION CONSIGO MISMA
        if nueva_cabeza in self.serpiente_cuerpo[:-1]:

            self.ejecutar_evento('ON_COLLISION_SELF')

            return

        self.serpiente_cuerpo.insert(0, nueva_cabeza)

        # COMER COMIDA
        if nueva_cabeza == self.posicion_comida:

            # 25% PROBABILIDAD X2
            if random.randint(1, 100) <= 25:

                self.modo_x2 = True

                self.tiempo_x2 = time.time()

                self.velocidad_gravedad = self.velocidad_x2

                self.color_comida = '#FFFF00'

                print "X2 ACTIVADO"

            # PUNTOS
            if self.modo_x2:

                self.puntuacion += 20

            else:

                self.puntuacion += 10

            self.snake_spawn_comida()

        else:

            self.serpiente_cuerpo.pop()

    # --------------------------------------------------

    def snake_cambiar_direccion(self, direccion):

        if direccion == 'UP' and self.serpiente_direccion[1] != 1:

            self.serpiente_direccion = (0, -1)

        elif direccion == 'DOWN' and self.serpiente_direccion[1] != -1:

            self.serpiente_direccion = (0, 1)

        elif direccion == 'LEFT' and self.serpiente_direccion[0] != 1:

            self.serpiente_direccion = (-1, 0)

        elif direccion == 'RIGHT' and self.serpiente_direccion[0] != -1:

            self.serpiente_direccion = (1, 0)

    # --------------------------------------------------

    def mostrar_game_over(self):

        tkMessageBox.showinfo(
            "Juego Terminado",
            "Puntuacion Final: " + str(self.puntuacion)
        )

        self.root.destroy()

        sys.exit(0)

# ------------------------------------------------------

if __name__ == "__main__":

    if len(sys.argv) != 2:

        print "Uso: python runtime.py <archivo_juego.json>"

        sys.exit(1)

    archivo_juego = sys.argv[1]

    try:

        with open(archivo_juego, 'r') as f:

            datos_juego = json.load(f)

    except IOError:

        print "Error: No se pudo encontrar el archivo " + archivo_juego

        sys.exit(1)

    juego = Juego(datos_juego)

    juego.run()
