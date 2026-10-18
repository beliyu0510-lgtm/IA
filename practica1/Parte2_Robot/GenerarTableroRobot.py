"""The aim of this script is to randomly generate the environment for the game. It must be a square matrix"""

import pygame
import sys
import random
#from GeneracionNormas import get_neighbors

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

def generate_table(N=2, prob_obstacle = 0.5):
    """Generates the environment for the robot planning problem. 
    The robot must pick up the box and take it to the goal.

    Args:
        N (int, optional): Size of the table. Defaults to 2.
        prob_obstacle (float, optional): Probability of an obstacle. Defaults to 0.3.
    """
    table = {}
    for x in range(1, N+1):
        for y in range(1, N+1):
            table[(x,y)] = {
                "Obstacle": False, "Robot": False, "Box": False, "Goal": False
            }

    available_spots = [(x,y) for x in range(1, N+1) for y in range(1, N+1)]
    # Spot of the robot, it always starts in (1,1)
    agent_position = (1,1)
    available_spots.remove(agent_position) #Eliminamos el (1,1), ahi no hay nada solo el agente

    # Spot the box:
    pos_box = random.choice(available_spots)
    available_spots.remove(pos_box) 

    pos_goal = random.choice(available_spots)
    available_spots.remove(pos_goal)

    # Generate the possible paths for Agent -> Box, and Box -> Goal
    path_robot_box = generate_path(agent_position, pos_box)
    path_box_goal = generate_path(pos_box, pos_goal)

    protected_path= set(path_robot_box + path_box_goal) #En estos caminos no puede haber obstáculos

    obstacle_position = []
    for pos in available_spots:
        if pos not in protected_path:
            if random.random() < prob_obstacle:
                table[pos]['Obstacle'] = True
                obstacle_position.append(pos)

    table[agent_position]['Robot'] = True
    table[pos_box]['Box'] = True
    table[pos_goal]['Goal'] = True

    return table, agent_position, pos_box, pos_goal, obstacle_position


