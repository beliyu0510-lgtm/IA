## Generado por Chaty, aunque faltan cambios porque no hay brisa y obviamente no puedo estar atrapada entre pozos, eso es cosa del
## archivo de generacionTablero

import gymnasium as gym
import pygame

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

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        self.table = generate_table(
            N=self.N,
            prob_well=self.prob_well
        )

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

            # Pozo
            if state["Well"]:
                pygame.draw.circle(
                    self.window,
                    (0, 0, 0),
                    rect.center,
                    25
                )

            # Wumpus
            if state["Wumpus"]:
                pygame.draw.circle(
                    self.window,
                    (200, 0, 0),
                    rect.center,
                    25
                )

            # Oro
            if state["Gold"]:
                pygame.draw.circle(
                    self.window,
                    (255, 215, 0),
                    rect.center,
                    20
                )

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