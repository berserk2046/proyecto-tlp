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
        self.wall_collision = config.get('wall_collision')
        self.power = config.get('power')
        self.target_score = config.get('target_score')
        self.duracion_poder = config.get('power_time')
        self.level = config.get('levels')
        self.puntuacion = 0
        self.juego_terminado = False
        self.juego_ganado = False
        self.final_boss = False

        # -- Checkeo variables dadas por BRICK -- #
        if self.power == 'ON': self.power = 1
        if self.wall_collision == 'OFF': self.wall_collision = 0
        if self.level not in ['BABY', 'ENTUSIASTA', 'NYAN_CAT']: self.level = 'BABY'
        if self.duracion_poder != None: self.duracion_poder = int(self.duracion_poder)
        if self.target_score != None:
            self.target_score = int(self.target_score)
        
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

        self.entities = {'PLAYER': {}, 'ENEMY': {}, 'ITEM': {}, 'COMIDA': {}, 'BOSS': {}}
        self.entities_counter = {'PLAYER': 0, 'ENEMY': 0, 'ITEM': 0, 'COMIDA': 0, 'BOSS': 0}
        self.items = {}
        self.directions = {'UP': [0,-1], 'DOWN': [0,1], 'RIGHT': [1,0], 'LEFT': [-1,0]}

        if self.tipo_juego == 'TANK':
            self.label_hp = tk.Label(self.marco_score, text="HP:\n", bg='#222222', fg='yellow', font=('Consolas', 10))
            self.label_hp.pack(pady=30, padx=10)

        
        if self.tipo_juego == 'TETRIS':
            self.velocidad_gravedad = 0.2
            self.boost_xp = False
            self.tiempo_boost = 0
            self.puntos_normales = 100
            self.puntos_boost = 300
        
        if self.tipo_juego == 'SNAKE':
            self.velocidad_gravedad = 0.15 if self.level in ['BABY', 'ENTUSIASTA'] else 0.005
            self.obstaculos = 0
            self.invencible = False
            self.tiempo_invencible = 0
            self.obstaculos = []
            self.invulnerable_obstaculo = False
            self.tiempo_obstaculo = 0

        if self.tipo_juego == 'TANK':
            self.player_tank = []
            self.enemy_tank = {}
            self.posd = {}
            self.bullets = {}
            self.velocidad_gravedad = 0.15


        self.tick_counter = 0
        # Basura global para eliminar elementos de entities sin inconvenientes
        self.to_remove = []

        # TABLE WITH ALL SHAPES INSIDE THEIR TYPES
        self.shapes = {'PLAYER': {}, 'ENEMY': {}, 'ITEM': {}, 'BOSS': {}}
        for i in self.datos_juego['shapes'].keys():
            e = self.datos_juego['shapes'][i]
            self.shapes[e['config']['type']][i] = e

        self.timer_gravedad = 0
        self.timer_slow_gravedad = 0
        self.timer_random_events = 0
        self.ejecutar_evento('ON_START')
        if self.tipo_juego == 'SNAKE' and self.level == 'NYAN_CAT': self.generar_obstaculos()

        self.timer_id = None # Para controlar el loop de Tkinter

    def run(self):
        # Inicia el ciclo principal de juego de Tkinter
        self.root.after(50, self.game_loop) 
        self.root.mainloop() 

    def game_loop(self):
        if self.juego_terminado:
            self.mostrar_game_over()
            return

        if self.juego_ganado:
            self.mostrar_game_over('WIN')
            return

        if self.puntuacion == self.target_score:
            self.ejecutar_evento('ON_TARGET_SCORE')
            self.target_score = 10000000

        # Logica de TICK/Gravedad
        # El loop se ejecuta cada 50ms (0.05 segundos)
        self.timer_gravedad += 0.05 
        if self.timer_gravedad >= self.velocidad_gravedad:
            self.timer_gravedad = 0
            self.ejecutar_evento('ON_TICK')
            self.tick_counter += 1

        self.timer_slow_gravedad += 0.0075
        if self.timer_slow_gravedad >= self.velocidad_gravedad:
            self.timer_slow_gravedad = 0
            self.ejecutar_evento('ON_STICK')

            # if self.tipo_juego == 'TANK': self.enemy_movement()

        if self.tipo_juego == 'TANK':
            self.timer_random_events += 0.02
            if self.timer_random_events >= self.velocidad_gravedad:
                if random.randint(0,100) <= 2: self.ejecutar_evento('ON_RANDOM')

        # DESACTIVAR BOOST XP
        if self.tipo_juego == 'TETRIS' and self.power and self.boost_xp:
            if time.time() - self.tiempo_boost >= self.duracion_poder:
                self.boost_xp = False
                self.velocidad_gravedad = 0.2
        if self.tipo_juego == 'SNAKE' and self.invencible and self.power:
            if time.time() - self.tiempo_invencible >= self.duracion_poder:
                self.invencible = False
        if self.tipo_juego == 'SNAKE' and self.invulnerable_obstaculo:
            if time.time() - self.tiempo_obstaculo >= 4:
                self.invulnerable_obstaculo = False

        if self.tipo_juego == 'SNAKE':
            if 0 < self.puntuacion < 60: self.level = 'BABY'
            if 60 <= self.puntuacion < 200: self.level = 'ENTUSIASTA'
            if 200 <= self.puntuacion:
                self.generar_obstaculos()
                self.level = 'NYAN_CAT'
                self.velocidad_gravedad = 0.005

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
        if key == 'UP': self.ejecutar_evento('ON_KEY_UP')
        elif key == 'DOWN': self.ejecutar_evento('ON_KEY_DOWN')
        elif key == 'LEFT': self.ejecutar_evento('ON_KEY_LEFT')
        elif key == 'RIGHT': self.ejecutar_evento('ON_KEY_RIGHT')
        elif key == "Z" or key == 'RETURN': self.ejecutar_evento('ON_KEY_RETURN')

    def dibujar(self):
        self.canvas.delete("all") # Borrar todo en cada frame
        self.label_score.config(text="PUNTUACION\n" + str(self.puntuacion))
        if self.tipo_juego == 'TANK':
            self.label_hp.config(text="HP: " + str(self.entities['PLAYER'][(self.entities['PLAYER'].keys())[0]]['config']['hp']))
        
        # Colores
        COLOR_GRID_FIJA = '#343434' # Gris oscuro para las celdas fijadas (Tetris)
        COLOR_PIEZA = '#00FFFF'     # Cyan para la pieza activa (Tetris)
        # COLORES BOOST XP
        
        COLOR_SNAKE_CABEZA = '#00FF00' # Verde brillante
        COLOR_SNAKE_CUERPO = '#33CC33' # Verde normal
        power_color = '#FFD700'     # DOrado
        
        # 1. Dibujar la cuadricula estatica (grid base)
        for y in range(self.alto):
            for x in range(self.ancho):
                if self.grid[y][x] == 1:
                     self.dibujar_celda(x, y, COLOR_GRID_FIJA)

        # 2. Dibujar la pieza actual de Tetris
        for i in self.entities.keys():
            if i in ['ITEM', 'COMIDA']:
                for j in self.entities[i].keys():
                    e = self.entities[i][j]
                    self.dibujar_celda(e['pos'][0], e['pos'][1], '#'+e['config']['color'], e['config']['style'])
                continue

            for j in self.entities[i].keys():
                e = self.entities[i][j]
                if e['config']['color'] != None: COLOR_PIEZA = "#" + e['config']['color']
                if self.tipo_juego == 'TETRIS' and self.boost_xp: COLOR_PIEZA = '#FFD700'
                if self.tipo_juego == 'SNAKE' and self.invencible: COLOR_PIEZA = power_color

                if self.level == 'NYAN_CAT' and j == self.shapes[i].keys()[0] + '0': e['config']['style'] = 'CAT'
                elif self.level == 'NYAN_CAT' and j != self.shapes[i].keys()[0] + '0': COLOR_PIEZA = '#%02x%02x%02x' % (random.randint(0,255), random.randint(0,255), random.randint(0,255))
                matriz_pieza = e['estados'][e['config']['state_rotation']]
                for y_offset, fila in enumerate(matriz_pieza):
                    for x_offset, celda in enumerate(fila):
                        if celda == 1:
                            self.dibujar_celda(e['pos'][0] + x_offset, e['pos'][1] + y_offset, COLOR_PIEZA, e['config']['style'], e['dir'])


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


    def ejecutar_evento(self, nombre_evento, obj=None):
        if nombre_evento in self.datos_juego['events']:
            for accion in self.datos_juego['events'][nombre_evento]:
                verbo, objeto, param = accion.get('accion'), accion.get('objeto'), accion.get('params')
                if not param: param = [None]
                
                if verbo == 'INCREASE_SCORE': self.puntuacion += int(objeto)
                if verbo == 'DECREASE_SCORE': self.puntuacion -= int(objeto)
                if verbo == 'SET_SCORE': self.puntuacion = int(objeto)
                if verbo == 'GAME_OVER': self.juego_terminado = True
                if verbo == 'GAME_WIN': self.juego_ganado= True
                if verbo == 'CALL': self.ejecutar_evento('ON_'+objeto)

                if self.tipo_juego == 'TETRIS':
                    if verbo == 'SPAWN': self.spawn_shape(objeto, param[0])
                    if verbo == 'MOVE': self.mover_pieza('PLAYER', param[0])
                    if verbo == 'ROTATE': self.mover_pieza('PLAYER', verbo)

                if self.tipo_juego == 'TANK':
                    if verbo == 'SPAWN': self.spawn_shape(objeto, param[0])
                    if verbo == 'MOVE': self.mover_pieza(objeto,param[0])
                    if verbo == 'REMOVE': self.to_remove.append([objeto, obj])
                    if verbo == 'CHECK_OBJ_COLLISION': self.obj_collision(objeto)
                    if verbo == 'TRASLADE': self.traslade(objeto, param[0])
                    if verbo == 'STAGE' and objeto == 'FINAL': self.final_level()
                
                if self.tipo_juego == 'SNAKE':
                    if verbo == 'SPAWN' and objeto == 'PLAYER': self.spawn_shape(objeto, param[0])
                    if verbo == 'SPAWN' and objeto in ['FOOD', 'BFOOD', 'YFOOD']: self.snake_spawn_comida(objeto, param[0])
                    if verbo == 'MOVE': self.mover_pieza(objeto,param[0])
                    if verbo == 'SET_DIRECTION': self.mover_pieza(objeto)
                    if verbo == 'GROW': self.snake_crecer(param[0])
                    if verbo == 'DECREASE': self.snake_decrease(param[0])


    # METODOS DE LOGICA DE JUEGO (MANTENIDOS DEL ARCHIVO ORIGINAL)
    # ---------------------------------------------------------------------
    #Probabilidad con pesos
    def probabilidad_ponderada(self, obj):
        info = dict(self.shapes[obj])
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

    def traslade(self, obj, param):
        if obj != 'PLAYER': return
        e = self.entities['PLAYER'][self.entities['PLAYER'].keys()[0]]
        e['pos'] = param

    def final_level(self):
        for j in ['COMIDA', 'ENEMY']:
            for i in self.entities[j].keys():
                self.entities[j].pop(i)
        self.final_boss = 1

    def spawn_shape(self, obj, param):
        if self.final_boss and (obj not in ['BOSS', 'ITEM']):
            return

        if param == 'BOSS' and not self.final_boss: return
        if obj == 'RANDOM_SHAPE': obj = 'PLAYER'

        entity = None
        shape_name = None
        used_positions = []

        if obj != 'COMIDA':
            i = self.probabilidad_ponderada(obj)
            if self.tipo_juego == 'SNAKE': i = self.shapes[obj].keys()[0]
            shape_name = i+str(self.entities_counter[obj])
            entity = self.entities[obj][shape_name] = dict(self.shapes[obj][i])
            entity['config'] = dict(self.shapes[obj][i]['config'])
            if obj != 'ITEM':
                entity['config']['hp'] = int(entity['config']['hp'])
            entity['config']['dmg'] = int(entity['config']['dmg'])
        else:
            shape_name = obj+str(self.entities_counter[obj])
            entity = self.entities[obj][shape_name] = {'pos': [], 'regen': 50, 'config': {'type': 'COMIDA', 'color': "FFD700", 'style': 'CIRCLE'}}

        self.entities_counter[obj] += 1
        if param == 'RANDOM':
            while True:
                x, y = random.randint(0, self.ancho - 1), random.randint(0, self.alto - 1)
                for i in self.entities.keys():
                    for j in self.entities[i].keys():
                        if j == shape_name: continue
                        used_positions.append(self.entities[i][j]['pos'])
                if [x,y] not in used_positions: 
                    entity['pos'] = [x,y]
                    if obj != 'COMIDA': entity['dir'] = [0,1]
                    break
        elif param == 'PLAYER':
            p = self.entities['PLAYER'][(self.entities['PLAYER'].keys())[0]]
            entity['pos'] = list([p['pos'][0] + p['dir'][0], p['pos'][1] + p['dir'][1]])
            entity['dir'] = list(p['dir'])
        elif param == 'BOSS':
            p = self.entities['BOSS'][self.entities['BOSS'].keys()[0]]
            entity['pos'] = list([p['pos'][0] + p['dir'][0], p['pos'][1] + p['dir'][1]])
            entity['dir'] = list(p['dir'])
        elif param == 'ENEMY':
            if not self.entities[param]:
                self.entities[obj].pop(shape_name)
                return
            i = random.choice(self.entities[param].keys())
            p = self.entities[param][i]
            entity['config'] = dict(entity['config'])
            entity['config']['color'] = 'FF0022'
            entity['pos'] = list([p['pos'][0] + p['dir'][0], p['pos'][1] + p['dir'][1]])
            entity['dir'] = list(p['dir'])

        elif param == None:
            if self.tipo_juego == 'TETRIS':
                entity['pos'] = [self.ancho/2 - 2, 0]
                entity['dir'] = [0, 1]
            else: entity['pos'] = [self.ancho/2, self.alto/2]
        else:
            entity['pos'] = param
            entity['dir'] = [0,1]

        if self.tipo_juego == 'TETRIS' and self.tetris_verificar_colision(entity['pos'][0], entity['pos'][1], entity['config']['state_rotation']):
            self.juego_terminado = True

    def enemy_movement(self, player, enemy):
        x, y = player['pos'][0] - enemy['pos'][0], player['pos'][1] - enemy['pos'][1]
        x = 0 if x == 0 else x/abs(x)
        y = 0 if y == 0 else y/abs(y)
        enemy['dir'] = [x,y]

        if x != 0 or y != 0:
            enemy['pos'][0] += x
            enemy['pos'][1] += y

    def obj_collision(self, obj):
        if not self.entities[obj]: return

        # Calcula colisiones con la pared de las entidades primero (caso basico)
        for i in self.entities[obj].keys():
            e = self.entities[obj][i]
            x, y = e['pos']
            if not ((0 < x < self.ancho) or (0 < y < self.alto)):
                if not self.wall_collision:
                    if x < 0: e['pos'][0] = 0
                    if x > self.ancho-1: e['pos'][0] = self.ancho-1
                    if y < 0: e['pos'][1] = 0
                    if y > self.alto-2: e['pos'][1] = self.alto-2
                else: self.to_remove.append([obj,i])

        #Esto calcula todas las posiciones de las demas entidades para confirmar si hay colisiones con estas
        used_positions = []
        for i in self.entities.keys():
            for j in self.entities[i].keys():
                used_positions.append({'key': j, 'entity': self.entities[i][j]})

        #Revizar Colision
        for i in self.entities[obj].keys():
            e = self.entities[obj][i]
            indexs = [val for val in used_positions if val['entity']['pos'] == e['pos'] and val['key']!=i or val['entity']['config']['type']=='BOSS']
            if e['config']['type'] == 'ENEMY':
                for j in indexs:
                    if j['entity']['config']['type'] == 'PLAYER':
                        j['entity']['config']['hp'] -= e['config']['dmg']
                        e['config']['hp'] -= j['entity']['config']['dmg']
                        if j['entity']['config']['hp'] <= 0: self.ejecutar_evento('ON_COLLISION')
                        if e['config']['hp'] <= 0:
                            self.ejecutar_evento('ON_ENEMY_DIED', i)
                    if j['entity']['config']['type'] == 'ITEM':
                        e['config']['hp'] -= j['entity']['config']['dmg']
                        if e['config']['hp'] <= 0:
                            self.ejecutar_evento('ON_ENEMY_DIED', i)

                        self.to_remove.append(['ITEM', j['key']])

            if e['config']['type'] == 'PLAYER':
                for j in indexs:
                    if j['entity']['config']['type'] == 'BOSS':
                        # block range of boss
                        px, py = e['pos']
                        x, y= j['entity']['pos']
                        x1, y1= x + len(j['entity']['estados'][0][0]), y + len(j['entity']['estados'][0])
                        if (x <= px < x1) and (y <= py < y1):
                            e['config']['hp'] -= j['entity']['config']['dmg']
                            j['entity']['config']['hp'] -= e['config']['dmg']
                            if e['config']['hp'] <= 0: self.ejecutar_evento('ON_COLLISION')
                            if j['entity']['config']['hp'] <= 0: self.ejecutar_evento('ON_WIN')

                    if j['entity']['config']['type'] == 'COMIDA':
                        if self.tipo_juego == 'SNAKE':
                            if j['entity']['ftype'] == 'food': 
                                self.ejecutar_evento('ON_EAT_FOOD')
                                if self.level == 'ENTUSIASTA' and random.randint(0,100) <= 100:
                                    self.ejecutar_evento('ON_DIFD')
                                    if random.randint(0,100) <= 100 and self.power: self.ejecutar_evento('ON_POWERUP')
                            if j['entity']['ftype'] == 'bfood': self.ejecutar_evento('ON_EAT_BFOOD')
                            if j['entity']['ftype'] == 'yfood':
                                self.ejecutar_evento('ON_EAT_YFOOD')
                                self.invencible = True
                                self.tiempo_invencible = time.time()

                        if e['config']['hp'] <= 50: e['config']['hp'] += j['entity']['regen']
                        if e['config']['hp'] > 50: e['config']['hp'] = 100 
                        self.to_remove.append(['COMIDA', j['key']])

                    if j['entity']['config']['type'] == 'ENEMY':
                        e['config']['hp'] -= j['entity']['config']['dmg']
                        j['entity']['config']['hp'] -= e['config']['dmg']
                        if e['config']['hp'] <= 0: self.ejecutar_evento('ON_COLLISION')
                        if j['entity']['config']['hp'] <= 0:
                            self.ejecutar_evento('ON_ENEMY_DIED', j['key'])
                    if j['entity']['config']['type'] == 'ITEM':
                        e['config']['hp'] -= j['entity']['config']['dmg']
                        if e['config']['hp'] <= 0: self.ejecutar_evento('ON_COLLISION')
                        self.to_remove.append(['ITEM', j['key']])

            if e['config']['type'] == 'ITEM':
                hit = 0
                for j in indexs:
                    if j['entity']['config']['type'] == 'BOSS':
                        # block range of boss
                        px, py = e['pos']
                        x, y= j['entity']['pos']
                        x1, y1= x + len(j['entity']['estados'][0][0]), y + len(j['entity']['estados'][0])
                        if (x <= px < x1) and (y <= py < y1):
                            j['entity']['config']['hp'] -= e['config']['dmg']
                            if j['entity']['config']['hp'] <= 0: self.ejecutar_evento('ON_WIN')
                            hit = 1

                    if j['entity']['config']['type'] == 'ENEMY':
                        j['entity']['config']['hp'] -= e['config']['dmg']
                        if j['entity']['config']['hp'] <= 0: self.ejecutar_evento('ON_ENEMY_DIED',j['key'])
                        hit = 1
                    if j['entity']['config']['type'] == 'PLAYER':
                        j['entity']['config']['hp'] -= e['config']['dmg']
                        if j['entity']['config']['hp'] <= 0: self.ejecutar_evento('ON_COLLISION')
                        hit = 1
                    if j['entity']['config']['type'] == 'ITEM':
                        self.to_remove.append(['ITEM', j['key']])
                        hit = 1
                if hit: self.to_remove.append([obj, i])

        if self.to_remove:
            seen = set()
            for i in self.to_remove:
                p = (i[0], i[1])
                if p not in seen and p[1] in self.entities[p[0]]:
                    self.entities[i[0]].pop(i[1])
                    seen.add(p)
            self.to_remove = []

    def mover_pieza(self, obj, direccion=None):
        if self.final_boss and obj not in ['PLAYER', 'ITEM', 'BOSS']: return
        if not self.final_boss and obj == 'BOSS': return

        dire = None
        forward = 0

        if direccion == None: #This if only works for SET_DIRECTION command that is only used in snake.
            direccion = obj
            obj = 'PLAYER' #In set_direction command just set default to player object
            shape_name = self.shapes[obj].keys()[0]
            self.entities[obj][shape_name+'0']['dir'] = self.directions[direccion]
            return
        if direccion == 'ROTATE':
            for i in self.entities[obj].keys():
                e = self.entities[obj][i]
                if len(e['estados']) > 1:
                    e['config']['state_rotation'] = (e['config']['state_rotation'] + 1) % len(e['estados'])
            return
        if direccion not in self.directions or direccion == 'FORWARD': forward = 1
        else: dire = self.directions[direccion]

        if self.tipo_juego == 'TETRIS':
            e = self.entities[obj][self.entities[obj].keys()[0]]
            if not self.tetris_verificar_colision(e['pos'][0]+dire[0], e['pos'][1]+dire[1], e['config']['state_rotation']):
                e['pos'][0] += dire[0]
                e['pos'][1] += dire[1]
            elif self.tipo_juego == 'TETRIS' and dire[1] > 0:
                self.tetris_fijar_pieza()       

        if self.tipo_juego == 'TANK' and obj == 'ENEMY' or obj == 'BOSS':
            player = self.entities['PLAYER'][(self.entities['PLAYER'].keys())[0]]
            for i in self.entities[obj].keys():
                e = self.entities[obj][i]
                speed = int(e['config']['velocity'])
                if self.tick_counter % speed == 0:
                    self.enemy_movement(player, e)
                else: continue
            return

        if self.tipo_juego == 'TANK':
            for i in self.entities[obj].keys():
                if forward: dire = self.entities[obj][i]['dir']
                self.entities[obj][i]['pos'][0] += dire[0]
                self.entities[obj][i]['pos'][1] += dire[1]
                self.entities[obj][i]['dir'] = dire

        if self.tipo_juego == 'SNAKE':
            shape_name = self.shapes['PLAYER'].keys()[0]
            head = self.entities['PLAYER'][shape_name+'0']

            new_x = head['pos'][0] + head['dir'][0]
            new_y = head['pos'][1] + head['dir'][1]
            
            if not (0 <= new_x < self.ancho and 0 <= new_y < self.alto):
                if not self.wall_collision or self.invencible:
                    new_x = new_x % self.ancho
                    new_y = new_y % self.alto
                elif self.level == 'NYAN_CAT' and self.puntuacion > 0:
                    self.ejecutar_evento('ON_COLLISION_WALL_NYAN')
                    head['dir'] = [head['dir'][0]*-1, head['dir'][1]*-1]
                    new_x = head['pos'][0] + head['dir'][0]
                    new_y = head['pos'][1] + head['dir'][1]
                else:
                    self.ejecutar_evento('ON_COLLISION_WALL')
                    return

            if self.grid[new_y][new_x] == 1:
                if not self.invulnerable_obstaculo and self.puntuacion > 0:
                    self.ejecutar_evento('ON_COLLISION_WALL_NYAN')
                    head['dir'] = [head['dir'][0] * -1, head['dir'][1] * -1]
                    new_x = head['pos'][0] + head['dir'][0]
                    new_y = head['pos'][1] + head['dir'][1]
                else:
                    self.ejecutar_evento('ON_COLLISION_WALL')
                    return

            keys = self.entities['PLAYER'].keys()
            old_positions = []

            for i in range(self.entities_counter['PLAYER']):
                old_positions.append(list(self.entities['PLAYER'][shape_name+str(i)]['pos']))
            
            head['pos'] = [new_x, new_y]
            
            for i in range(1, self.entities_counter['PLAYER']):
                self.entities['PLAYER'][shape_name+str(i)]['pos'] = old_positions[i-1]
            
            for k in keys:
                if k == shape_name+'0': continue
                if self.entities['PLAYER'][k]['pos'] == head['pos']:
                    self.ejecutar_evento('ON_COLLISION_SELF')
                    return
            
        self.obj_collision('PLAYER')
        return

    def tetris_fijar_pieza(self):
        if not self.entities['PLAYER']: return
        key = self.entities['PLAYER'].keys()[0]
        e = self.entities['PLAYER'][key]

        matriz_pieza = e['estados'][e['config']['state_rotation']]
        for y_offset, fila in enumerate(matriz_pieza):
            for x_offset, celda in enumerate(fila):
                if celda == 1:
                    x = e['pos'][0] + x_offset
                    y = e['pos'][1] + y_offset
                    if 0 <= x < self.ancho and 0 <= y < self.alto:
                        self.grid[y][x] = 1
        # eliminar la pieza activa
        self.entities['PLAYER'].pop(key)
        self.tetris_limpiar_lineas()
        self.ejecutar_evento('ON_START')

    def tetris_verificar_colision(self, x, y, rotacion):
        e = self.entities['PLAYER'][self.entities['PLAYER'].keys()[0]]
        matriz_pieza = e['estados'][e['config']['state_rotation']]
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
            if random.randint(1, 100) <= 12:
                self.boost_xp = True
                self.tiempo_boost = time.time()
                self.velocidad_gravedad = 0.08
            # DAR PUNTOS
            if self.boost_xp:
                self.puntuacion += self.puntos_boost * lineas_limpias
            else:
                self.puntuacion += self.puntos_normales * lineas_limpias

        for _ in range(lineas_limpias):
            self.ejecutar_evento('ON_LINE_CLEAR')

    def generar_obstaculos(self):
        if self.obstaculos: return
        shape_name = self.shapes['PLAYER'].keys()[0]
        used_positions = []
        for i in self.entities['COMIDA'].keys():
            used_positions.append(list(self.entities['COMIDA'][i]['pos']))
        for i in range(8):
            x = random.randint(2, self.ancho - 3)
            y = random.randint(2, self.alto - 3)
            if [x,y] != self.entities['PLAYER'][shape_name+'0']['pos'] and [x,y] not in used_positions:
                self.grid[y][x] = 1
        self.obstaculos = 1

    def snake_crecer(self, objeto):
        for i in range(int(objeto)):
            shape_name = self.shapes['PLAYER'].keys()[0]
            # This if block works because first entity at spawn is always player
            key = shape_name + str(self.entities_counter['PLAYER']-1)
            tail_pos = list(self.entities['PLAYER'][key]['pos'])
            tail_dir = list(self.entities['PLAYER'][key]['dir'])
            self.spawn_shape('PLAYER', tail_pos)
            key = shape_name + str(self.entities_counter['PLAYER']-1)
            self.entities['PLAYER'][key]['dir'] = tail_dir

    def snake_decrease(self, objeto):
        shape_name = self.shapes['PLAYER'].keys()[0]
        keys = self.entities['PLAYER'].keys()
        if objeto == 'ALL':
            for k in keys:
                if k == shape_name+'0':continue
                self.to_remove.append(['PLAYER', k])
            self.entities_counter['PLAYER'] = 1
        else:
            for i in range(int(objeto)):
                if len(keys) > 1:
                    self.to_remove.append(['PLAYER', shape_name+str(self.entities_counter['PLAYER']-1)])
                    self.entities_counter['PLAYER'] -= 1
                else:
                    self.ejecutar_evento('ON_COLLISION_WALL')
                    break

        if self.to_remove:
            seen = set()
            for i in self.to_remove:
                p = (i[0], i[1])
                if p not in seen and p[1] in self.entities[p[0]]:
                    self.entities[i[0]].pop(i[1])
                    seen.add(p)
            self.to_remove = []

    def snake_spawn_comida(self, tipo, param):
        self.spawn_shape('COMIDA', param)
        food = self.entities['COMIDA']['COMIDA'+str(self.entities_counter['COMIDA']-1)]
        if tipo == 'FOOD':
            food['config']['color'] = "FF0000"
            food['ftype'] = tipo.lower()
        elif tipo == 'BFOOD':
            food['config']['color'] = "8A0BD2"
            food['ftype'] = tipo.lower()
        elif tipo == 'YFOOD':
            food['config']['color'] = "FFD700"
            food['ftype'] = tipo.lower()
               
    # METODOS DE SALIDA (ADAPTADOS A GUI)
    # -----------------------------------

    def mostrar_game_over(self, option=None):
        # Muestra una ventana de mensaje de Tkinter
        if option == 'WIN':
            tkMessageBox.showinfo("Juego Ganado!!!!!", "Puntuacion Final: " + str(self.puntuacion))
            self.root.destroy()
            sys.exit(0)
            return

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
    
