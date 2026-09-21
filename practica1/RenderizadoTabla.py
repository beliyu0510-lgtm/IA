"""The aim of this script is to get a pretty environment"""
"""This code was made by Gemini"""

## Este codigo no me gusta va muy lento y encima es feo

import pygame
import sys

class VisualizadorWumpus:
    def __init__(self, N, tamaño_celda=120):
        pygame.init()
        self.N = N
        self.tamaño_celda = tamaño_celda
        self.ancho = N * tamaño_celda
        self.alto = N * tamaño_celda
        
        # Crear la ventana con flag de doble buffer para máxima fluidez
        self.pantalla = pygame.display.set_mode((self.ancho, self.alto))
        pygame.display.set_caption("Mundo del Wumpus - Visualizador")
        
        # Cargar las fuentes UNA SOLA VEZ en el init (no en el bucle de render)
        self.fuente_texto = pygame.font.SysFont("arial", 12, bold=True)
        self.fuente_etiquetas = pygame.font.SysFont("arial", 11)

    def renderizar(self, tablero_real, pos_agente=(1, 1), pisadas=None):
        """Dibuja el estado del juego usando figuras geométricas limpias y rápidas."""
        if pisadas is None:
            pisadas = set()

        # Evitar congelamiento procesando eventos
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # Paleta de Colores
        COLOR_FONDO = (245, 245, 245)
        COLOR_GRID = (180, 180, 180)
        COLOR_VISITADO = (220, 235, 252)
        
        COLOR_AGENTE = (41, 128, 185)    # Azul
        COLOR_WUMPUS = (192, 57, 43)    # Rojo
        COLOR_POZO = (44, 62, 80)       # Negro/Gris Oscuro
        COLOR_ORO = (241, 196, 15)      # Dorado
        COLOR_BRISA = (135, 206, 235)   # Cían / Azul Brisa
        COLOR_HEDOR = (142, 68, 173)    # Morado

        self.pantalla.fill(COLOR_FONDO)

        for x in range(1, self.N + 1):
            for y in range(1, self.N + 1):
                pos = (x, y)
                celda = tablero_real[pos]

                # Inversión de eje Y para formato cartesiano
                px = (x - 1) * self.tamaño_celda
                py = (self.N - y) * self.tamaño_celda

                rect = pygame.Rect(px, py, self.tamaño_celda, self.tamaño_celda)

                # 1. Fondo de casillas visitadas
                if pos in pisadas:
                    pygame.draw.rect(self.pantalla, COLOR_VISITADO, rect)

                # 2. Borde de la casilla
                pygame.draw.rect(self.pantalla, COLOR_GRID, rect, 2)

                cx, cy = px + self.tamaño_celda // 2, py + self.tamaño_celda // 2

                # 3. Dibujar Elementos Principales (Si existen)
                if celda["Well"]:
                    # Pozo: Círculo negro grande
                    pygame.draw.circle(self.pantalla, COLOR_POZO, (cx, cy), self.tamaño_celda // 3)
                
                if celda["Wumpus"]:
                    # Wumpus: Triángulo/Monstruo rojo
                    puntos = [(cx, cy - 25), (cx - 20, cy + 20), (cx + 20, cy + 20)]
                    pygame.draw.polygon(self.pantalla, COLOR_WUMPUS, puntos)
                    
                if celda["Gold"]:
                    # Oro: Rombo/Diamante dorado
                    puntos = [(cx, cy - 20), (cx + 20, cy), (cx, cy + 20), (cx - 20, cy)]
                    pygame.draw.polygon(self.pantalla, COLOR_ORO, puntos)

                if pos == pos_agente:
                    # Agente: Círculo azul brillante en el centro
                    pygame.draw.circle(self.pantalla, COLOR_AGENTE, (cx, cy), 18)
                    pygame.draw.circle(self.pantalla, (255, 255, 255), (cx, cy), 18, 3) # Borde blanco

                # 4. Dibujar Percepciones (Indicadores de texto / puntos de color)
                percepciones_txt = []
                if celda["Breeze"]:
                    percepciones_txt.append("Brisa")
                if celda["Reek"]:
                    percepciones_txt.append("Hedor")

                if percepciones_txt:
                    txt = " | ".join(percepciones_txt)
                    col = COLOR_HEDOR if "Hedor" in txt else COLOR_BRISA
                    surf_perc = self.fuente_etiquetas.render(txt, True, col)
                    self.pantalla.blit(surf_perc, (px + 8, py + self.tamaño_celda - 20))

                # 5. Coordenadas (x,y) en la esquina superior izquierda
                surf_coord = self.fuente_etiquetas.render(f"({x},{y})", True, (150, 150, 150))
                self.pantalla.blit(surf_coord, (px + 6, py + 4))

        # Actualizar la pantalla de una vez
        pygame.display.flip()

    # Alias para compatibilidad con main
    def dibujar(self, tablero_real, pos_agente=(1, 1), pisadas=None):
        self.renderizar(tablero_real, pos_agente, pisadas)