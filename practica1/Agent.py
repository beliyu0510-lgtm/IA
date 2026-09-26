"""Ejercicio 1. SAT-Solver"""

from GeneracionNormas import id_var, generate_rules
from DPLL import dpll
import random

class Agent:
    def __init__(self, N):
        self.N = N
        self.position = (1,1) #Posicion inicial
        self.visited = [(1,1)] #Casillas visitadas para no considerarlas nuevas exploraciones
        self.path = [(1,1)] # Recorrido que hace el agente, porque podría retroceder
        self.kb = generate_rules(N)
        self.learned = [] #Lista con las cosas que va aprendiendo el agente   

    def perceive(self, state):
        x,y = self.position

        if state['Breeze']:
            self.learned.append(id_var('Breeze', x,y))
        else:
            self.learned.append(-id_var('Breeze', x,y))

        if state['Reek']:
            self.learned.append(id_var('Reek',x,y))
        else:
            self.learned.append(-id_var('Reek',x,y))

        if state['Bright']:
            self.learned.append(id_var('Bright',x,y))
        else:
            self.learned.append(-id_var('Bright',x,y))

    def get_knowledge(self):
        knowledge = self.kb.copy()
        for fact in self.learned:
            knowledge.append([fact])
        return knowledge

    def entails(self, proposition):
        knowledge = self.get_knowledge()
        test = knowledge.copy()
        test.append([-proposition])
        return not dpll(test) # Si DPLL = True -> no hay contradicción (no está demostrado), de lo contrario sí está demostrado y devuelve true

    def is_safe(self, x,y):
        well = id_var('Well',x,y)
        wumpus = id_var('Wumpus',x,y)

        no_well = self.entails(-well)
        no_wumpus = self.entails(-wumpus)

        return no_well and no_wumpus

    def is_dangerous(self, x, y):
        well = id_var("Well", x, y)
        wumpus = id_var("Wumpus", x, y)

        has_well = self.entails(well)
        has_wumpus = self.entails(wumpus)

        return has_well or has_wumpus

    def move(self):
        x,y = self.position
        possible_moves = []
        if x > 1 and (x - 1, y) not in self.visited:
            possible_moves.append((x - 1, y))

        if x < self.N and (x + 1, y) not in self.visited:
            possible_moves.append((x + 1, y))

        if y > 1 and (x, y - 1) not in self.visited:
            possible_moves.append((x, y - 1))

        if y < self.N and (x, y + 1) not in self.visited:
            possible_moves.append((x, y + 1))

        safe_move = []

        for position in possible_moves:
            px, py = position
            if position not in self.visited and self.is_safe(px, py):
                safe_move.append(position)

        if safe_move:
            position = safe_move[0]
            self.position = position
            self.visited.append(position)
            self.path.append(position)
            return True

        # Esto se hace porque hay veces que el agente no está 100% seguro, entonces elige aleatoriamente entre las que tienen peligro
        uncertain_moves = []

        for position in possible_moves:
            px, py = position

            if position not in self.visited and not self.is_dangerous(px, py):
                uncertain_moves.append(position)

        if uncertain_moves:
            self.position = random.choice(uncertain_moves)
            self.visited.append(position)
            self.path.append(position)
            return True

        if len(self.path) > 1:
            previous_position = self.path[-2]
            self.position = previous_position
            self.path.pop()
            return True
        
        return False


            








