# -*- coding: utf-8 -*-
# runtime.py (VERSION CON INTERFAZ GRAFICA USANDO Tkinter y caracteres ASCII unicamente)

import sys
import json
import time
import random
# Tkinter es la libreria GUI estandar de Python, compatible con 2.7
import Tkinter as tk
import tkMessageBox # Necesario para el GAME OVER
# Quitamos os y msvcrt ya que la GUI maneja el dibujo y el input
# import os
# import msvcrt 

class Juego:
    def __init__(self, datos_juego):
        self.datos_juego = datos_juego
        self.tipo_juego = self.datos_juego.get('tipo_juego', 'TETRIS')
        config = self.datos_juego.get('config', {})
        self.ancho = config.get('grid_size', [10, 20])[0]
        self.alto = config.get('grid_size', [10, 20])[1]
        self.grid = [[0 for _ in range(self.ancho)] for _ in range(self.alto)]
        self.power = config.get('power', 0)
        self.duracion_poder = int(config.get('power_time', 0))
        self.level = config.get('levels', 'BABY')
        self.puntuacion = 0
        self.juego_terminado = False

        # -- Checkeo variables dadas por BRICK -- #
        if self.power == 'ON': self.power = 1
        else: self.power = 0
        if self.level not in ['BABY', 'ENTUSIASTA', 'NYAN_CAT']: self.level = 'BABY'
        
        # --- Configuracion de la GUI ---
        self.root = tk.Tk()
        self.root.title("BrickScript - " + self.tipo_juego)
        # Configurar la accion al cerrar la ventana ('X' de la barra de titulo)
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar_ventana)
        
        self.taman_celda = 25 # Pixeles por celda
        self.ancho_canvas = self.ancho * self.taman_celda
        self.alto_canvas = self.alto * self.taman_celda
        
        # Canvas para dibujar el juego
        self.canvas = tk.Canvas(self.root, width=self.ancho_canvas, height=self.alto_canvas, bg='#111111')
        self.canvas.pack(side=tk.LEFT, padx=10, pady=10)

        # Marco lateral para la puntuacion y controles
        self.marco_score = tk.Frame(self.root, width=150, height=self.alto_canvas, bg='#222222')
        self.marco_score.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)
        
        self.label_score = tk.Label(self.marco_score, text="PUNTUACION\n0", bg='#222222', fg='white', font=('Consolas', 16, 'bold'))
        self.label_score.pack(pady=40, padx=10)
        
        # Nota: Se ha eliminado 'Q: Salir' de los controles en pantalla
        self.label_controles = tk.Label(self.marco_score, text="CONTROLES\nFlechas: Mover/Rotar", bg='#222222', fg='gray', font=('Consolas', 10))
        self.label_controles.pack(pady=20, padx=10)
        if self.tipo_juego == 'TETRIS' and self.power:
            self.label_pow = tk.Label(self.marco_score, text="BOOST POWER:\nAleatoriamente se otorgara un boost (10%)\nLas piezas cambiaran a amarillo\nLa XP se multiplicara por cada linea limpiada.", bg='#222222', fg='yellow', font=('Consolas', 10))
            self.label_pow.pack(pady=30, padx=10)

        # Configurar eventos de teclado. Usamos <Key> para capturar cualquier tecla
        self.root.bind('<Key>', self.manejar_input_gui)
        
        if self.tipo_juego == 'TETRIS':
            self.pieza_actual = None
            self.pieza_x, self.pieza_y, self.pieza_rotacion = 0, 0, 0
            self.pieza_config = None
            self.velocidad_gravedad = 0.2
            # BOOST XP
            self.boost_xp = False
            self.tiempo_boost = 0
            self.puntos_normales = 100
            self.puntos_boost = 300
        
        if self.tipo_juego == 'SNAKE':
            self.serpiente_cuerpo = []
            self.serpiente_config = {}
            self.serpiente_direccion = (1, 0)
            self.posicion_comida = None
            self.posicion_bcomida = None
            self.posicion_ycomida = None
            self.velocidad_gravedad = 0.15 if self.level in ['BABY', 'ENTUSIASTA'] else 0.05
            self.invencible = False
            self.tiempo_invencible = 0
            self.obstaculos = []
            self.invulnerable_obstaculo = False
            self.tiempo_obstaculo = 0


        
        self.timer_gravedad = 0
        self.ejecutar_evento('ON_START')
        self.timer_id = None # Para controlar el loop de Tkinter

    def run(self):
        # Inicia el ciclo principal de juego de Tkinter
        self.root.after(50, self.game_loop) 
        self.root.mainloop() 

    def game_loop(self):
        if self.juego_terminado:
            self.mostrar_game_over()
            return

        # Logica de TICK/Gravedad
        # El loop se ejecuta cada 50ms (0.05 segundos)
        self.timer_gravedad += 0.05 
        if self.timer_gravedad >= self.velocidad_gravedad:
            self.timer_gravedad = 0
            self.ejecutar_evento('ON_TICK')
        # DESACTIVAR BOOST XP
        if self.tipo_juego == 'TETRIS' and self.power and self.boost_xp:
            if time.time() - self.tiempo_boost >= self.duracion_poder:
                self.boost_xp = False
                self.velocidad_gravedad = 0.2
        if self.tipo_juego == 'SNAKE' and self.invencible and self.power:
            if time.time() - self.tiempo_invencible >= self.duracion_poder:
                self.invencible = False
        if self.tipo_juego == 'SNAKE' and self.invulnerable_obstaculo:
            if time.time() - self.tiempo_obstaculo >= 2:
                self.invulnerable_obstaculo = False

        self.dibujar()

        # Programa el siguiente ciclo de juego
        self.timer_id = self.root.after(50, self.game_loop)
        
    def cerrar_ventana(self):
        # Detiene el loop de juego de forma segura
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
        self.root.destroy()
        sys.exit(0)


    def manejar_input_gui(self, event):
        key = event.keysym.upper()
        
        # La opcion de salir con 'Q' ha sido eliminada.
        
        # Mapeo de teclas de flecha
        if self.tipo_juego == 'TETRIS':
            if key == 'UP': self.ejecutar_evento('ON_KEY_UP')
            elif key == 'DOWN': self.ejecutar_evento('ON_KEY_DOWN')
            elif key == 'LEFT': self.ejecutar_evento('ON_KEY_LEFT')
            elif key == 'RIGHT': self.ejecutar_evento('ON_KEY_RIGHT')
        elif self.tipo_juego == 'SNAKE':
            # Llamamos a las funciones internas para Snake
            if key == 'UP': self.snake_cambiar_direccion('UP')
            elif key == 'DOWN': self.snake_cambiar_direccion('DOWN')
            elif key == 'LEFT': self.snake_cambiar_direccion('LEFT')
            elif key == 'RIGHT': self.snake_cambiar_direccion('RIGHT')


    def dibujar(self):
        self.canvas.delete("all") # Borrar todo en cada frame
        self.label_score.config(text="PUNTUACION\n" + str(self.puntuacion))
        
        # Colores
        COLOR_GRID_FIJA = '#343434' # Gris oscuro para las celdas fijadas (Tetris)
        COLOR_PIEZA = '#00FFFF'     # Cyan para la pieza activa (Tetris)
        # COLORES BOOST XP
        
        COLOR_SNAKE_CABEZA = '#00FF00' # Verde brillante
        COLOR_SNAKE_CUERPO = '#33CC33' # Verde normal
        COLOR_FOOD = '#FF0000'      # Rojo
        COLOR_BFOOD = '#8A0BD2'
        COLOR_PFOOD = '#FFD700'
        
        # 1. Dibujar la cuadricula estatica (grid base)
        for y in range(self.alto):
            for x in range(self.ancho):
                if self.grid[y][x] == 1:
                     self.dibujar_celda(x, y, COLOR_GRID_FIJA)

        # 2. Dibujar la pieza actual de Tetris
        if self.tipo_juego == 'TETRIS' and self.pieza_actual:
            if self.tipo_juego == 'TETRIS' and self.boost_xp:
                COLOR_PIEZA = '#FFD700'
            elif self.pieza_config['color'] != None:
                COLOR_PIEZA = "#" + self.pieza_config['color']
            matriz_pieza = self.pieza_actual[self.pieza_rotacion]
            for y_offset, fila in enumerate(matriz_pieza):
                for x_offset, celda in enumerate(fila):
                    if celda == 1:
                        self.dibujar_celda(self.pieza_x + x_offset, self.pieza_y + y_offset, COLOR_PIEZA)
        
        # 3. Dibujar Snake y Comida
        if self.tipo_juego == 'SNAKE':
            # Comida
            if self.level == 'NYAN_CAT':
                for x, y in self.obstaculos:
                    self.dibujar_celda(x, y, '#777777')
            if self.posicion_comida:
                x, y = self.posicion_comida
                self.dibujar_celda(x, y, COLOR_FOOD)
            if self.posicion_bcomida:
                x, y = self.posicion_bcomida
                self.dibujar_celda(x, y, COLOR_BFOOD)
            if self.posicion_ycomida:
                x, y = self.posicion_ycomida
                self.dibujar_celda(x, y, COLOR_PFOOD)
            # Cuerpo de la Serpiente
            for i, segmento in enumerate(self.serpiente_cuerpo):
                x, y = segmento
                direction = self.serpiente_dirs[i]
                style = 'CAT' if self.level == 'NYAN_CAT' and i==0 else self.serpiente_config['style']
                if self.level == 'NYAN_CAT':
                    color = COLOR_SNAKE_CABEZA if i == 0 else '#%02x%02x%02x' % (random.randint(0,255), random.randint(0,255), random.randint(0,255))
                else:
                    color = COLOR_SNAKE_CABEZA if i == 0 else COLOR_SNAKE_CUERPO
                if self.invencible:
                    color = '#FFD700'
                self.dibujar_celda(x, y, color, style, direction)

    def dibujar_celda(self, x, y, color, style=None, direction=None):
        ts = self.taman_celda # Alias para taman de celda
        x1, y1 = x * ts, y * ts
        x2, y2 = x1 + ts, y1 + ts
        if style != None:
            if style == 'CIRCLE':
                self.canvas.create_oval(x1-1, y1-1, x2+1, y2+1, fill=color, outline='#000000')
            if style == 'CAT':
                self.canvas.create_oval(x1-ts/8, y1+ts/9, x2+ts/8, y2-0.1, fill="#adadad", outline='#000000')
                self.canvas.create_polygon(x1, y1-ts/3, x1, y1+7, x2-(ts/4)-5, y1+7, fill="#adadad", outline="#adadad")
                self.canvas.create_polygon(x2, y1-ts/3, x1+(ts/4)+5, y1+7, x2, y1+7, fill="#adadad", outline="#adadad")

            elif style == 'TRIANGLE':
                if direction != None: x, y = direction
                else: x, y = self.serpiente_direccion
                if x == 1: self.canvas.create_polygon(x1, y1, x1, y2, x2, (y1+y2)/2, fill=color, outline='#000000')
                elif x == -1: self.canvas.create_polygon(x1, (y1+y2)/2, x2, y1, x2, y2, fill=color, outline='#000000')
                elif y == -1: self.canvas.create_polygon((x1+x2)/2, y1, x1, y2, x2, y2, fill=color, outline='#000000')
                elif y == 1: self.canvas.create_polygon((x1+x2)/2, y2, x1, y1, x2, y1, fill=color, outline='#000000')
        else:
            self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline='#000000')


    def ejecutar_evento(self, nombre_evento):
        if nombre_evento in self.datos_juego['events']:
            for accion in self.datos_juego['events'][nombre_evento]:
                verbo, objeto = accion.get('accion'), accion.get('objeto')
                
                if verbo == 'INCREASE_SCORE': self.puntuacion += int(objeto)
                if verbo == 'DECREASE_SCORE': self.puntuacion -= int(objeto)
                if verbo == 'SET_SCORE': self.puntuacion = int(objeto)
                if verbo == 'GAME_OVER': self.juego_terminado = True

                if self.tipo_juego == 'TETRIS':
                    if verbo == 'SPAWN': self.tetris_spawn_pieza()
                    if verbo == 'MOVE': self.tetris_mover_pieza(accion['params'][0])
                    if verbo == 'ROTATE': self.tetris_rotar_pieza()
                
                if self.tipo_juego == 'SNAKE':
                    if verbo == 'SPAWN' and objeto == 'PLAYER': self.snake_spawn_jugador(accion)
                    if verbo == 'SPAWN' and objeto == 'FOOD': self.snake_spawn_comida()
                    if verbo == 'SPAWN' and objeto == 'BFOOD': self.snake_spawn_bcomida()
                    if verbo == 'SPAWN' and objeto == 'YFOOD': self.snake_spawn_ycomida()
                    if verbo == 'MOVE' and objeto == 'PLAYER': self.snake_mover_jugador()
                    if verbo == 'GROW': self.snake_crecer(objeto)
                    if verbo == 'DECREASE': self.snake_decrease(objeto)


    # METODOS DE LOGICA DE JUEGO (MANTENIDOS DEL ARCHIVO ORIGINAL)
    # ---------------------------------------------------------------------
    #Probabilidad con pesos
    def probabilidad_ponderada(self):
        info = self.datos_juego['shapes']
        names = list(info.keys())
        promedio = (100.0 / len(names)) / 100.0
        lista = {}
        current = 0
        for i in range(len(names)):
            if not 'estados' in info[names[i]] or not info[names[i]]['config']['chance']:
                lista[current] = names[i]
                current += promedio
            elif info[names[i]]['config']['chance'] > 0:
                lista[current] = names[i]
                current += float(info[names[i]]['config']['chance']) / 100

        rand = random.uniform(0, current)
        choice = None
        for key in sorted(lista.keys() + [current]):
            if rand < key:
                return choice
            choice = lista[key]
        return None

    def tetris_spawn_pieza(self):
        nombre_pieza = self.probabilidad_ponderada()

        self.pieza_actual = self.datos_juego['shapes'][nombre_pieza]['estados']
        self.pieza_config = self.datos_juego['shapes'][nombre_pieza]['config']

        self.pieza_x, self.pieza_y, self.pieza_rotacion = self.ancho / 2 - 2, 0, 0
        if self.tetris_verificar_colision(self.pieza_x, self.pieza_y, self.pieza_rotacion):
            self.juego_terminado = True

    def tetris_mover_pieza(self, direccion):
        if not self.pieza_actual: return
        dx, dy = 0, 0
        if direccion == 'LEFT': dx = -1
        elif direccion == 'RIGHT': dx = 1
        elif direccion == 'DOWN': dy = 1
        if not self.tetris_verificar_colision(self.pieza_x + dx, self.pieza_y + dy, self.pieza_rotacion):
            self.pieza_x += dx
            self.pieza_y += dy
        elif dy > 0:
            self.tetris_fijar_pieza()

    def tetris_rotar_pieza(self):
        if not self.pieza_actual: return
        nueva_rotacion = (self.pieza_rotacion + 1) % len(self.pieza_actual)
        if not self.tetris_verificar_colision(self.pieza_x, self.pieza_y, nueva_rotacion):
            self.pieza_rotacion = nueva_rotacion

    def tetris_fijar_pieza(self):
        matriz_pieza = self.pieza_actual[self.pieza_rotacion]
        for y_offset, fila in enumerate(matriz_pieza):
            for x_offset, celda in enumerate(fila):
                if celda == 1:
                    if 0 <= self.pieza_y + y_offset < self.alto and 0 <= self.pieza_x + x_offset < self.ancho:
                        self.grid[self.pieza_y + y_offset][self.pieza_x + x_offset] = 1
        self.pieza_actual = None
        self.tetris_limpiar_lineas()
        self.ejecutar_evento('ON_START')

    def tetris_verificar_colision(self, x, y, rotacion):
        if not self.pieza_actual: return False
        matriz_pieza = self.pieza_actual[rotacion]
        for y_offset, fila in enumerate(matriz_pieza):
            for x_offset, celda in enumerate(fila):
                if celda == 1:
                    nuevo_x, nuevo_y = x + x_offset, y + y_offset
                    if not (0 <= nuevo_x < self.ancho and 0 <= nuevo_y < self.alto and self.grid[nuevo_y][nuevo_x] == 0):
                        return True
        return False

    def tetris_limpiar_lineas(self):

        nuevo_grid = [fila for fila in self.grid if not all(fila)]

        lineas_limpias = self.alto - len(nuevo_grid)

        if lineas_limpias > 0:
            self.grid = ([[0] * self.ancho for _ in range(lineas_limpias)] + nuevo_grid)

        # ACTIVAR BOOST XP RANDOM
        if self.power:
            if random.randint(1, 100) <= 10:
                self.boost_xp = True

                self.tiempo_boost = time.time()
                self.velocidad_gravedad = 0.08

            # DAR PUNTOS
            if self.boost_xp:
                self.puntuacion += (
                    self.puntos_boost * lineas_limpias
                )

            else:
                self.puntuacion += (
                    self.puntos_normales * lineas_limpias
                )

        for _ in range(lineas_limpias):
            self.ejecutar_evento('ON_LINE_CLEAR')
    
    def snake_spawn_jugador(self, accion):
        coords = accion['params'][0] if accion['params'] else [self.ancho / 2, self.alto / 2]
        self.serpiente_cuerpo = [(coords[0], coords[1])]
        self.serpiente_dirs = [(1,0)]
        self.serpiente_config = self.datos_juego['shapes']['PIXEL']['config']
        self.serpiente_direccion = (1, 0)
        if self.level == 'NYAN_CAT':
            self.generar_obstaculos()

    def generar_obstaculos(self):
        self.obstaculos = []
        for i in range(8):
            x = random.randint(2, self.ancho - 3)
            y = random.randint(2, self.alto - 3)

            if (x, y) not in self.serpiente_cuerpo:
                self.obstaculos.append((x, y))    

    def snake_spawn_comida(self):
        while True:
            x, y = random.randint(0, self.ancho - 1), random.randint(0, self.alto - 1)
            if (x, y) not in self.serpiente_cuerpo:
                self.posicion_comida = (x, y)
                break

    def snake_spawn_bcomida(self):
        while True:
            x, y = random.randint(0, self.ancho - 1), random.randint(0, self.alto - 1)
            if (x, y) not in self.serpiente_cuerpo and (x, y) != self.posicion_comida:
                self.posicion_bcomida = (x, y)
                break
    def snake_spawn_ycomida(self):
        while True:
            x, y = random.randint(0, self.ancho - 1), random.randint(0, self.alto - 1)
            if (x, y) not in self.serpiente_cuerpo and (x, y) != self.posicion_comida and (x, y) != self.posicion_bcomida:
                self.posicion_ycomida = (x, y)
                break
                
    def snake_mover_jugador(self):
        if not self.serpiente_cuerpo: return
        cabeza_x, cabeza_y = self.serpiente_cuerpo[0]
        dir_x, dir_y = self.serpiente_direccion
        nueva_cabeza = (cabeza_x + dir_x, cabeza_y + dir_y)

        if self.invencible:
            x, y = nueva_cabeza
            if x < 0:
                x = self.ancho - 1
            elif x >= self.ancho:
                x = 0
            if y < 0:
                y = self.alto - 1
            elif y >= self.alto:
                y = 0
            nueva_cabeza = (x, y)
        else:
            if not (0 <= nueva_cabeza[0] < self.ancho and 0 <= nueva_cabeza[1] < self.alto):
                if self.level == 'NYAN_CAT' and self.puntuacion > 0:
                    self.ejecutar_evento('ON_COLLISION_WALL_NYAN')
                    self.serpiente_direccion = (dir_x*-1, dir_y*-1)
                else:
                    self.ejecutar_evento('ON_COLLISION_WALL')
                    return
        if self.level == 'NYAN_CAT' and nueva_cabeza in self.obstaculos:
            if not self.invulnerable_obstaculo:
                if self.puntuacion > 0:
                    self.puntuacion = 0
                    self.invulnerable_obstaculo = True
                    self.tiempo_obstaculo = time.time()
                else:
                    self.juego_terminado = True
            return
        if not self.invencible and nueva_cabeza in self.serpiente_cuerpo[:-1]:
            self.ejecutar_evento('ON_COLLISION_SELF')
            return

        self.serpiente_cuerpo.insert(0, nueva_cabeza)
        self.serpiente_dirs.insert(0, self.serpiente_direccion)
        self.serpiente_cuerpo.pop()
        self.serpiente_dirs.pop()

        if nueva_cabeza == self.posicion_bcomida:
            self.ejecutar_evento('ON_EAT_BFOOD')
            self.posicion_bcomida = None

        if nueva_cabeza == self.posicion_ycomida:
            self.ejecutar_evento('ON_EAT_YFOOD')
            self.posicion_ycomida = None
            self.invencible = True
            self.tiempo_invencible = time.time()

        if nueva_cabeza == self.posicion_comida:
            self.ejecutar_evento('ON_EAT_FOOD')
            if self.level == 'ENTUSIASTA' and random.randint(0,100) <= 50:
                self.ejecutar_evento('ON_DIFD')
                if random.randint(0,100) <= 100 and self.power: self.ejecutar_evento('ON_POWERUP')

    def snake_cambiar_direccion(self, direccion):
        if direccion == 'UP' and self.serpiente_direccion[1] != 1:
            self.serpiente_direccion = (0, -1)
        elif direccion == 'DOWN' and self.serpiente_direccion[1] != -1:
            self.serpiente_direccion = (0, 1)
        elif direccion == 'LEFT' and self.serpiente_direccion[0] != 1:
            self.serpiente_direccion = (-1, 0)
        elif direccion == 'RIGHT' and self.serpiente_direccion[0] != -1:
            self.serpiente_direccion = (1, 0)

    def snake_crecer(self, objeto):
        for i in range(int(objeto)):
            self.serpiente_cuerpo.append(self.serpiente_cuerpo[-1])
            self.serpiente_dirs.append(self.serpiente_dirs[-1])

    def snake_decrease(self, objeto):
        if objeto == 'ALL':
            del self.serpiente_cuerpo[1:]
            del self.serpiente_dirs[1:]
        else:
            for i in range(int(objeto)):
                if len(self.serpiente_cuerpo) > 1:
                    self.serpiente_cuerpo.pop()
                    self.serpiente_dirs.pop()
                else:
                    self.ejecutar_evento('ON_COLLISION_WALL')
                    break


    # METODOS DE SALIDA (ADAPTADOS A GUI)
    # -----------------------------------

    def mostrar_game_over(self):
        # Muestra una ventana de mensaje de Tkinter
        tkMessageBox.showinfo("Juego Terminado", "Puntuacion Final: " + str(self.puntuacion))
        self.root.destroy()
        sys.exit(0)

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
    
