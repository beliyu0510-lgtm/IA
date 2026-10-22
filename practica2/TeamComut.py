"""Buzón de mensajes entre los miembros de un mismo equipo"""
from collections import Counter
import copy

class Message:
    """Mensaje entre dos compañeros"""
    def __init__(self, emisor, receptor, tipo, contenido = None, time = None):
        self.emisor = emisor
        self.receptor = receptor
        self.tipo = tipo
        self.contenido = contenido
        self.time = time

    def __repr__(self):
        return 'Mensaje(%s: %s -> %s, %r)' % (self.tipo, self.emisor, self.receptor, self.contenido)


class TeamBus:
    """Buzón compartido por los agentes de un equipo, los del otro tendrán su propio buzón"""

    def __init__(self, team):
        self.team = list(team) #índices de los agentes del equipo
        self.leader = min(self.team) 
        self.history = [] #partidas ya terminadas
        self.games = 0
        self._clear()

    def _clear(self):
        self.inbox = dict((i,[]) for i in self.team) # buzón de cada agente ({0:[], 2:[], 4:[]})
        self.sent = 0 #Transmisiones (broadcast inicial cuenta como 1)
        self.delivered = 0 #Mensajes entregados (broadcast a 2 compañeros suma 2)
        self.bykind = Counter() #Transmisiones por tipo de mensaje

    def _check(self, index): #Comprobación de que todos los que tienen acceso al buzón son del mismo equipo
        if index not in self.team:
            raise ValueError('El agente %s no es de este equipo %s' % (index, self.team))

    ### Envío y Recepción de Mensajes ###
    def send(self, emisor, receptor, tipo, contenido = None, time = None):
        """Mensaje de un compañero a otro"""
        self._check(emisor)
        self._check(receptor)
        if emisor == receptor:
            raise ValueError('Un agente no puede enviarse mensajes a sí mismo')
        self.inbox[receptor].append(Message(emisor, receptor, tipo, copy.deepcopy(contenido), time))
        self.sent += 1
        self.delivered += 1
        self.bykind[tipo] += 1

    def broadcast(self, emisor, tipo, contenido = None, time = None):
        """Broadcast de un mensaje para todos"""
        self._check(emisor)
        for recep in self.team:
            if recep != emisor:
                self.inbox[recep].append(Message(emisor, recep, tipo, copy.deepcopy(contenido), time))
                self.delivered += 1
        self.sent += 1
        self.bykind[tipo] += 1

    def receive(self, index):
        """Devuelve los mensajes pendientes del agente y vacía su buzón"""
        self._check(index)
        messages = self.inbox[index]
        self.inbox[index] = []
        return messages

### Estadísticas ###
    def stats(self):
        return {'sent':self.sent, 'delivered':self.delivered, 'bykind':dict(self.bykind)}

    def reset(self):
        """Se llama antes de empezar cada partida, archivamos las cifras de la partida anetrior y vaciamos todo"""
        if self.games > 0:
            self.history.append(self.stats())
        self.games += 1
        self._clear()

    def allGames(self):
        """Devuelve todos los datos de todas las partidas"""
        return self.history + [self.stats()]
    
