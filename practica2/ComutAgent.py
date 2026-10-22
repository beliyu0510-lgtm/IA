from entorno.captureAgents import CaptureAgent

class ComutAgent(CaptureAgent):
    """Agente con acceso al buzón del equipo"""
    def __init__(self, index, bus, timeForComputing = 0.1):
        CaptureAgent.__init__(self, index, timeForComputing)
        self.bus = bus
        self.turn = 0

    def registerInitialState(self, gameState):
        CaptureAgent.registerInitialState(self, gameState)
        self.turn = 0
        if self.index == self.bus.leader:
            self.bus.reset()

    def send(self, receptor, tipo, contenido = None):
        self.bus.send(self.index, receptor, tipo, contenido, self.turn)

    def broadcast(self, tipo, contenido=None):
        self.bus.broadcast(self.index, tipo, contenido, self.turn)

    def readMessages(self):
        return self.bus.receive(self.index)

    def final(self, gameState):
        CaptureAgent.final(self, gameState)
        if self.index == self.bus.leader:
            print('[%s] mensajes: %s' % ('rojo' if self.red else 'azul', self.bus.stats()))
    
