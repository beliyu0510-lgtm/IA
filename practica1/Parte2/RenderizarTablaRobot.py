"""This script contains the render of the table"""

## Código generado por Chatgpt para la renderización del tablero, el único cambio a descatar es el uso de la librería load_emoji
## para usar emojis en vez de círculos o cuadrados de colores que inicialmente genera la IA. 

import gymnasium as gym
import pygame
from pygame_emojis import load_emoji #Descargar libreria en caso de no tenerlo

from GenerarTableroRobot import generate_table


class RobotEnv(gym.Env):

    def __init__(self, N=5, prob_obstacle=0.3):
        super().__init__()

        self.N = N
        self.prob_obstacle = prob_obstacle

        self.table = None

        self.window = None
        self.cell_size = 100
        self.action_space = gym.spaces.Discrete(4)
        self.emoji_size = (64,64)
        self.agent_position = (1,1)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
    
        self.table, self.agent_position, pos_box, pos_goal, obstacle_position = generate_table(
            N=self.N,
            prob_obstacle=self.prob_obstacle
        )
    
        return self.table, {}
    
    def render(self):
        if self.window is None:
            pygame.init()

            size = self.N * self.cell_size

            self.window = pygame.display.set_mode(
                (size, size)
            )

            pygame.display.set_caption("Robot Planning")

        self.window.fill((255, 255, 255))

        for (x, y), state in self.table.items():

            px = (x - 1) * self.cell_size
            py = (y - 1) * self.cell_size

            rect = pygame.Rect(
                px,
                py,
                self.cell_size,
                self.cell_size
            )

            # Casilla
            pygame.draw.rect(
                self.window,
                (220, 220, 220),
                rect
            )

            # Borde
            pygame.draw.rect(
                self.window,
                (0, 0, 0),
                rect,
                2
            )

            # Agente
            if (x, y) == self.agent_position:
                agent_image = load_emoji("🤖", self.emoji_size)
                agent_rect = agent_image.get_rect(center=rect.center)
                self.window.blit(agent_image, agent_rect)

            # Obstáculo
            if state["Obstacle"]:
                emoji = load_emoji('🚫', self.emoji_size)
                emoji_rect = emoji.get_rect(center=rect.center)
                self.window.blit(emoji, emoji_rect)

            # Caja
            if state["Box"]:
                emoji = load_emoji('📦', self.emoji_size)
                emoji_rect = emoji.get_rect(center=rect.center)
                self.window.blit(emoji, emoji_rect)

            # Objetivo
            if state["Goal"]:
                emoji = load_emoji('🏁', self.emoji_size)
                emoji_rect = emoji.get_rect(center=rect.center)
                self.window.blit(emoji, emoji_rect)
            
        pygame.display.flip()

    def close(self):
        if self.window is not None:
            pygame.quit()
            self.window = None


# Registrar el entorno
gym.register(
    id="RobotPlanning-v0",
    entry_point="RenderizarTablaRobot:RobotEnv"
)