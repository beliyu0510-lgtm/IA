# myTeam.py
# ---------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).

"""AQUí VA LA IMPLEMENTACIÓN DEL ALGORTMO COMPLETO, OSEA LO DE LOS CONFLICTOS Y TODO ESO, ENTONCES, DIRIA QUE TODO
LO QUE HAY EN ESTE ARCHIVO SE PUEDE ELIMINAR Y HACER DE CERO"""

from captureAgents import CaptureAgent
import random, time, util
from game import Directions
import game

#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, thirdIndex, isRed,
               first = 'MyAgent', second = 'MyAgent', third='MyAgent'):

  # The following line is an example only; feel free to change it.
  return [eval(first)(firstIndex), eval(second)(secondIndex), eval(third)(thirdIndex)]

##########
# Agents #
##########

class MyAgent(CaptureAgent):
    """
    Tu agente base donde irás construyendo la lógica paso a paso.
    """
    def registerInitialState(self, gameState):
        CaptureAgent.registerInitialState(self, gameState)
        # Aquí inicializarás variables de tu equipo/agente más adelante

    def chooseAction(self, gameState):
        """
        Método obligatorio: decide qué movimiento hacer en cada turno.
        De momento devuelve STOP o un movimiento legal aleatorio para probar el entorno.
        """
        actions = gameState.getLegalActions(self.index)
        return Directions.STOP


