"""Pensamiento del juego en cada equipo"""
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..'))

from entorno.captureAgents import CaptureAgent
from entorno.game import Directions, Actions
from TeamComut import TeamBus
from AgentCNP import AgentCNP

def createTeam(firstIndex, secondIndex, thirdIndex, isRed, first = 'AgentCNP',
               second = 'AgentCNP', third = 'AgentCNP'):
    """Crear los 3 agentes del equipo y un buzón que comparten"""
    indices = [firstIndex, secondIndex, thirdIndex]
    bus = TeamBus(indices)
    classes = [globals()[name] for name in (first, second, third)] #Convierte los strs a clases reales
    return [cls(index, bus) for cls, index in zip(classes, indices)]

