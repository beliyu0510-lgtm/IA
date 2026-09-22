"""The aim of this script is to randomly generate the environment for the game. It must be a square matrix"""

import pygame
import sys
import random
from GeneracionNormas import get_neighbors

def generate_path(start, end) -> list: # Esta funcion sirve para que a la hora de generar la tabla siempre exista un camino posible al oro y no sea un juego imposible
    """Generates a random path for the agent to go 

    Args:
        start (tuple): Start coordinates
        end (tuple): End coordinates (in this case, where the gold is)

    Returns:
        list: list with all the coordinates used for the path
    """
    path = [start]
    x1,y1 = start
    x2,y2 = end

    while (x1,y1) != (x2, y2):
        possible_moves = []
        if x1 < x2:
            new_position = (x1+1, y1)
            if new_position not in path:
                possible_moves.append((x1+1,y1))
        elif x1 > x2:
            new_position = (x1-1, y1)
            if new_position not in path:
                possible_moves.append((x1-1, y1))

        if y1 < y2:
            new_position = (x1, y1+1)
            if new_position not in path:
                possible_moves.append((x1, y1+1))
        elif y1 > y2:
            new_position = (x1, y1-1)
            if new_position not in path:
                possible_moves.append((x1, y1-1))

        x1,y1 = random.choice(possible_moves)
        path.append((x1,y1))
    return path

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
    available_spots.remove((1,1)) #Eliminamos el (1,1) porque ahi no puede haber ni un pozo ni un Wumpus ni oro

    # Spot the gold:
    pos_gold = random.choice(available_spots)
    table[pos_gold]['Gold'] = True
    table[pos_gold]['Bright'] = True

    # Get a possible path from the start to the gold
    path = generate_path((1,1),pos_gold)
    for spots in path[1:]: # El elemento (1,1) fue eliminado anteriormente
        available_spots.remove(spots)

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

    agent_position = (1,1)
    return table, agent_position


