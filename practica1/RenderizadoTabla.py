## Generado por Chaty, aunque faltan cambios porque no hay brisa y obviamente no puedo estar atrapada entre pozos, eso es cosa del
## archivo de generacionTablero

import gymnasium as gym
import pygame
from pygame_emojis import load_emoji #Descargar libreria en caso de no tenerlo

from GeneracionTablero import generate_table


class WumpusEnv(gym.Env):

    def __init__(self, N=5, prob_well=0.3):
        super().__init__()

        self.N = N
        self.prob_well = prob_well

        self.table = None

        self.window = None
        self.cell_size = 100
        self.action_space = gym.spaces.Discrete(4)
        self.emoji_size = (64,64)
        self.agent_position = (1,1)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        self.table, self.agent_position = generate_table(
            N=self.N,
            prob_well=self.prob_well
        )
        self.agent_position = (1,1)

        return self.table, {}

    def render(self):
        if self.window is None:
            pygame.init()

            size = self.N * self.cell_size

            self.window = pygame.display.set_mode(
                (size, size)
            )

            pygame.display.set_caption("Wumpus World")

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
                agent_image = load_emoji("🕵🏻‍♂️", self.emoji_size)
                agent_rect = agent_image.get_rect(center=rect.center)
                self.window.blit(agent_image, agent_rect)

            # Pozo
            if state["Well"]:
                emoji = load_emoji('🕳️', self.emoji_size)
                emoji_rect = emoji.get_rect(center=rect.center)
                self.window.blit(emoji, emoji_rect)

            # Wumpus
            if state["Wumpus"]:
                emoji = load_emoji('👹', self.emoji_size)
                emoji_rect = emoji.get_rect(center=rect.center)
                self.window.blit(emoji, emoji_rect)

            # Oro
            if state["Gold"]:
                emoji = load_emoji('👑', self.emoji_size)
                emoji_rect = emoji.get_rect(center=rect.center)
                self.window.blit(emoji, emoji_rect)
                font = pygame.font.Font(None, 18)
                bright_text = font.render("Bright", True, (255, 170, 0))
                bright_rect = bright_text.get_rect(centerx=rect.centerx,top=emoji_rect.bottom + 2)
                self.window.blit(bright_text, bright_rect)

            # Brisa
            if state["Breeze"]:
                font = pygame.font.Font(None, 18)
                breeze_text = font.render("Breeze",True,(0, 0, 204))
                self.window.blit(breeze_text,(rect.x + 5, rect.y + 5))

            # Hedor
            if state['Reek']:
                font = pygame.font.Font(None, 18)
                reek_text = font.render("Reek",True,(153, 76, 0))
                reek_rect = reek_text.get_rect(topright=(rect.right - 5, rect.top + 5))
                self.window.blit(reek_text, reek_rect)
            
        pygame.display.flip()

    def close(self):
        if self.window is not None:
            pygame.quit()
            self.window = None


# Registrar el entorno
gym.register(
    id="WumpusWorld-v0",
    entry_point="RenderizadoTabla:WumpusEnv"
)