"""Cambios respecto a la entrega 1:
En la primera entrega, si ambos equipos usan el algoritmo de ContractNet, se quedan bloqueados: los atacantes
de cada equipo esperan en el centro porque el rival vigila el paso, y como la regla prohíbe pisar casillas
junto a un fantasma, ninguno avanza y la partida acaba en empate.

Solución: ahora el atacante cuenta los turnos que lleva esperando en el borde sin poder pasar. Al llegar a su
umbral (entre 4 y 10 turnos, distinto para cada agente) deja de buscar su paso y de evitar a los fantasmas, y va
directo a la bandera, es decir, se arriesga a pasar. El umbral se elige al azar para que no gane siempre el
equipo que mueve primero. El contador se reinicia si el agente deja de atacar, si coge la bandera o si lo comen.

Resultado: entre equipos iguales ya no se empata siempre, y contra el baseline se siguen ganando todas las
partidas."""

from entorno.captureAgents import CaptureAgent
from entorno.game import Directions, Actions
from TeamComut import TeamBus
from ComutAgent import ComutAgent
import heapq
import random

ATACAR = 'ATACAR BANDERA'
DEFENDER = 'DEFENDER BANDERA'
PATRULLAR = 'PATRULLA CENTRAL'
COOLDOWN_ATACAR = 15 # tirnos mínimos entre dos anuncios de la misma tarea
COOLDOWN_DEFENDER = 8
COOLDOWN_LIBERAR = 15 #turnos sin amenaza tras los que un defensor se libera
ESPERA_MIN = 4 #tirnos esperando en el borde antes de arriesgarse
ESPERA_MAX = 10

class AgentCNP(ComutAgent):

    def registerInitialState(self, gameState):
        ComutAgent.registerInitialState(self,gameState)
        self.startPos = gameState.getAgentPosition(self.index)
        self.centerCells = self.getCenterBoundary(gameState) # pasos de la línea central en mi lado
        self.patrolIdx = 0 
        self.currentTask = None 
        self.openCall = None #Subasta abierta por el gerente
        self.mateTask = {} #lo que hacen mis compañeros
        self.lastSeen = {} #tarea que se anunció por última vez
        self.calm = 0 #Turnos seguidos sin amenaza
        self.espera = 0 #Turnos esperando en el borde
        self.umbral = random.randint(ESPERA_MIN, ESPERA_MAX)
        
    def chooseAction(self, gameState):
        self.turn += 1
        # Leer el buzón
        for m in self.readMessages():
            if m.tipo == 'ANUNCIO':
                tarea = m.contenido['task']
                self.lastSeen[tarea] = self.turn
                bid = self.computeBid(gameState,tarea, m.contenido['target']) #Calcula el valor de la puja
                if bid > 0:
                    self.send(m.emisor, 'PUJA', {'task': tarea, 'bid':bid})
            elif m.tipo == 'PUJA':
                if self.openCall and self.openCall['task'] == m.contenido['task']:
                    self.openCall['bids'][m.emisor] = m.contenido['bid']
            elif m.tipo == 'ADJUDICACION':
                for w in m.contenido['winners']:
                    self.mateTask[w] = m.contenido['task']
                if self.index in m.contenido['winners']:
                    self.currentTask = m.contenido['task']
                    self.calm = 0
            elif m.tipo == 'LIBERADA':
                self.mateTask.pop(m.emisor, None)

        # Detectar algo para convertirme en gerente y hacer broadcasting
        self.detectarEventos(gameState)

        # Si la subasta sigue abierta pero asignada, se cierra:
        self.cerrarSubasta(gameState)

        # La tarea deja de ser necesaria
        self.liberarTarea(gameState)

        pos = gameState.getAgentPosition(self.index)
        if (self.currentTask != ATACAR or gameState.getAgentState(self.index).numCarrying > 0 or pos == self.startPos):
            self.espera = 0 
        elif (self.centerCells and not gameState.getAgentState(self.index).isPacman
            and min(self.getMazeDistance(pos, c) for c in self.centerCells) <= 2):
            self.espera += 1 # estoy en el borde sin haber pasado
        target = self.targetFor(gameState)
        action = self.planRoute(gameState, target)
        return action if action else Directions.STOP

    def hayAlguien(self, tarea):
        """Verificar si la tarea ya está cogida"""
        return self.currentTask == tarea or tarea in self.mateTask.values()

    def fresca(self, tarea, cooldown):
        """True si la tarea no se ha anunciado hace poco"""
        return self.turn - self.lastSeen.get(tarea, -999) >= cooldown

    def detectarEventos(self, gameState):
        """Si hay algo y nadie lo hace, se anuncia"""
        if self.openCall is not None: 
            return #hay una subasta en marcha
        if gameState.getAgentState(self.index).numCarrying > 0: #El portador no gestiona nada
            return

        # La bandera está en su sitio y nadie ataca
        if (gameState.isFlagHome(not self.red) and not self.hayAlguien(ATACAR) and self.fresca(ATACAR, COOLDOWN_ATACAR)):
            self.abrirSubasta(ATACAR, gameState.getFlagHome(not self.red), 2)
            return

        # Invasor a la vista o bandera robada, y nadie defiende
        invasor = self.nearestInvader(gameState)
        if ((invasor is not None or not gameState.isFlagHome(self.red)) and not self.hayAlguien(DEFENDER) and self.fresca(DEFENDER, COOLDOWN_DEFENDER)):
            self.abrirSubasta(DEFENDER, invasor if invasor else gameState.getFlagHome(self.red), 1)
    
    def abrirSubasta(self, tarea, target, plazas):
        """Anunciar la tarea para todos"""
        self.lastSeen[tarea] = self.turn
        self.openCall = {'task':tarea, 'target':target, 'plazas':plazas, 'deadline':self.turn+1, 'bids':{}}
        self.broadcast('ANUNCIO', {'task':tarea, 'target':target, 'plazas':plazas})

    def cerrarSubasta(self, gameState):
        """Cuando ha pasado el plazo, se evaluan las pujas y se elige los mejores y se anuncia"""
        c = self.openCall
        if c is None or self.turn < c['deadline']:
            return
        propia = self.computeBid(gameState, c['task'], c['target'])
        if propia > 0:
            c['bids'][self.index] = propia
        ranking = sorted(c['bids'].items(), key = lambda kv: -kv[1])
        ganadores = [agente for agente, _ in ranking[:c['plazas']]]
        if ganadores:
            self.broadcast('ADJUDICACION', {'task':c['task'], 'winners':ganadores})
            for w in ganadores:
                self.mateTask[w] = c['task']
            if self.index in ganadores:
                self.currentTask = c['task']
                self.calm = 0
        self.openCall = None

    def liberarTarea(self, gameState):
        """El defensor se libera si lleva un rato sin amenaza y avisa"""
        if self.currentTask != DEFENDER:
            return
        amenaza = self.nearestInvader(gameState) is not None or not gameState.isFlagHome(self.red)
        self.calm = 0 if amenaza else self.calm + 1
        if self.calm >= COOLDOWN_LIBERAR:
            self.currentTask = None
            self.broadcast('LIBERADA', {'task':DEFENDER})

    def computeBid(self,gameState, tarea, target): #Puja
        """Cuanto más cerca del objetivo, más puja
        Puja = cercanía - riesgo - coste de cambio de tarea. Si es 0 me abstengo"""

        if gameState.getAgentState(self.index).numCarrying > 0:
            return 1000.0 if tarea == ATACAR else 0.0 # El portador no se reasigna
        
        dist = self.getMazeDistance(gameState.getAgentPosition(self.index), target)
        cercania = 100.0 / (dist +1)

        fantasmas = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
        fantasmas = [f for f in fantasmas if not f.isPacman and f.getPosition() is not None]
        riesgo = 0.0
        if fantasmas:
            d = min(self.getMazeDistance(gameState.getAgentPosition(self.index), f.getPosition()) for f in fantasmas) 
            if d < 5:
                riesgo = 10.0 / (d+1)
        costeCambio = 15.0 if (self.currentTask is not None and self.currentTask != tarea) else 0.0
        return max(0.0, cercania - riesgo - costeCambio)
    

    def targetFor(self, gameState):
        """Dónde ir según la tarea"""
        if self.currentTask == ATACAR:
            if gameState.getAgentState(self.index).numCarrying > 0:
                return gameState.getFlagHome(self.red) #Si ya llevo la bandera la entrego a mi base
            # No tengo la bandera, ir a por la enemiga
            if not gameState.isFlagHome(not self.red): # si la bandera del equipo contrario ya no está en su casa
                invasor = self.nearestInvader(gameState)
                if invasor is not None:
                    return invasor
                return self.nextPatrolCell(gameState)
            cruce = self.myCrossing()
            if self.espera >= self.umbral:
                cruce = None
            if (not gameState.getAgentState(self.index).isPacman and cruce is not None and gameState.getAgentPosition(self.index) != cruce):
                return cruce
            return gameState.getFlagHome(not self.red)
        
        if self.currentTask == DEFENDER:
            invasor = self.nearestInvader(gameState)
            if invasor is not None:
                return invasor #Perseguir al invasor
            return gameState.getFlagHome(self.red) #No hay invasor, vigilo mi bandera

        invasor = self.nearestInvader(gameState)
        if invasor is not None:
            return invasor
        return self.nextPatrolCell(gameState) #No hay invasor, no persigo, recorro las casillas del centro
        

    def nearestInvader(self, gameState):
        """Posición del invasor más cercano que veo"""
        myPos = gameState.getAgentPosition(self.index)
        posiciones = [gameState.getAgentPosition(i) for i in self.getOpponents(gameState)
                      if gameState.getAgentState(i).isPacman and gameState.getAgentPosition(i) is not None]
        if not posiciones:
            return None
        return min(posiciones, key= lambda p:self.getMazeDistance(myPos,p))

    def nextPatrolCell(self, gameState):
        """Siguiente paso de la línea central a visitar"""
        if not self.centerCells:
            return self.startPos
        if gameState.getAgentPosition(self.index) == self.centerCells[self.patrolIdx]:
            self.patrolIdx = (self.patrolIdx + 1) % len(self.centerCells)
        return self.centerCells[self.patrolIdx]

    def getCenterBoundary(self, gameState):
        """Busca las celas pegadas a la línea central de 'mi lado' cuyo vecino del otro lado está también libre. Son los pasos
        por donde podría entrar un rival"""
        walls = gameState.getWalls()
        mid = walls.width // 2
        ownX, otherX = (mid - 1, mid) if self.red else (mid, mid-1)
        return [(ownX, y) for y in range(walls.height) if not walls[ownX][y] and not walls[otherX][y]]
    

    def myCrossing(self):
        """Paso de la línea central, cada compañero tendrá uno distinto"""
        if not self.centerCells:
            return None
        return self.centerCells[self.bus.team.index(self.index) % len(self.centerCells)]

    def dangerCost(self, gameState):
        """Coste de entrar en cada celda. En mi lado 1"""
        fantasmas = [gameState.getAgentPosition(i) for i in self.getOpponents(gameState) if not gameState.getAgentState(i).isPacman
                     and gameState.getAgentPosition(i) is not None]
        arriesgo = self.espera >= self.umbral
        cache = {}
        def coste(celda):
            if celda in cache:
                return cache[celda]
            c = 1
            if fantasmas and not arriesgo and gameState.isRed(celda) != self.red:
                d = min(self.getMazeDistance(celda, g) for g in fantasmas)
                if d<=1:
                    c = None
                else:
                    c = 1 + {2:8, 3:3}.get(d,0)
            cache[celda] = c
            return c
        return coste

    def planRoute(self, gameState, target):
        """Aplicamos el algoritmo de Dijsktra: primera acción del camino de menor coste a target, esquivando el peligro"""
        start = gameState.getAgentPosition(self.index)
        if start == target:
            return Directions.STOP
        coste = self.dangerCost(gameState)
        walls = gameState.getWalls()
        mejor = {start:0}
        cola = [(0, 0, start, None)]
        n = 0
        while cola:
            c, _, celda, primera = heapq.heappop(cola)
            if celda == target:
                return primera
            if c > mejor.get(celda, float('inf')):
                continue
            x,y = int(celda[0]), int(celda[1])
            for accion in [Directions.NORTH, Directions.SOUTH, Directions.EAST, Directions.WEST]:
                dx, dy = Actions.directionToVector(accion)
                sig = (int(x + dx), int(y + dy))
                if walls[sig[0]][sig[1]]:
                    continue
                paso = coste(sig)
                if paso is None:
                    continue
                nc = c + paso
                if nc < mejor.get(sig, float('inf')):
                    mejor[sig] = nc
                    n += 1
                    heapq.heappush(cola, (nc, n, sig, primera if primera is not None else accion))
        return self.huir(gameState)

    def huir(self, gameState):
        """No hay camino seguor, huyo porque es la acción que más me aleja de los fantasmas visibles"""
        fantasmas = [gameState.getAgentPosition(i) for i in self.getOpponents(gameState) if not gameState.getAgentState(i).isPacman
                     and gameState.getAgentPosition(i) is not None]
        if not fantasmas:
            return Directions.STOP
        pos = gameState.getAgentPosition(self.index)
        mejorAccion = Directions.STOP
        mejorDist = min(self.getMazeDistance(pos, g) for g in fantasmas)
        for accion in gameState.getLegalActions(self.index):
            dx, dy = Actions.directionToVector(accion)
            sig = (int(pos[0]+dx), int(pos[1]+dy))
            d = min(self.getMazeDistance(sig, g) for g in fantasmas)
            if d > mejorDist:
                mejorAccion, mejorDist = accion, d
        return mejorAccion