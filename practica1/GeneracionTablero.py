"""The aim of this script is to randomly generate the environment for the game. It must be a square matrix"""

import pygame
import sys
import random
from GeneracionNormas import get_neighbors

def generate_table(N=2, prob_well = 0.3):
    """Generates the dict with the features of the Real World

    Args:
        N (int, optional): Size of the table. Defaults to 2.
        prob_well (float, optional): Probability of a well in a spot. Defaults to 0.3.
    """
    table = {}
    for x in range(1, N+1):
        for y in range(1, N+1):
            table[(x,y)] = {
                "Well": False, "Breeze": False, "Wumpus": False, "Reek": False, "Bright": False, "Gold":False
            }

    available_spots = [(x,y) for x in range(1, N+1) for y in range(1, N+1)]

    # Spot the gold:
    pos_gold = random.choice(available_spots)
    table[pos_gold]['Gold'] = True
    table[pos_gold]['Bright'] = True
    available_spots.remove(pos_gold) #Evitamos que el oro y el Wumpus estén en la misma casilla

    # Spot the Wumpus:
    pos_wumpus = random.choice(available_spots)
    table[pos_wumpus]['Wumpus'] = True
    available_spots.remove(pos_wumpus)

    # Spot the Wells:
    for pos in available_spots:
        if random.random() < prob_well:
            table[pos]['Well'] = True

    for (x,y), state in table.items():
        if state['Well']:
            for vx,vy in get_neighbors(x,y,N):
                table[(vx,vy)]['Breeze'] = True
        if state['Wumpus']:
            for vx, vy in get_neighbors(x,y,N):
                table[(vx,vy)]['Reek'] = True
    return table


