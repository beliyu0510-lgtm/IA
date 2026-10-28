"""
mensajes.py - Capa de comunicación del ejercicio 2.

Implementa los modelos y patrones de comunicación vistos en clase (tema 07):
  * Mensajes con estructura FIPA-ACL: performativa, emisor, receptor, tema,
    contenido, id de conversación y "en respuesta a".
  * Modelos de envío: punto a punto, broadcast y multicast (por grupos).
  * Patrón publicar-suscribir con temas y mensajes retenidos (como en MQTT):
    quien se suscribe recibe el último estado conocido de cada clave del tema.
  * Patrón petición-respuesta (request-reply): lo implementan los agentes con
    'conversacion' y 'enRespuestaA'.
  * Transporte asíncrono con latencia de 1 turno y pérdida de mensajes con
    probabilidad configurable (para estudiar la robustez del protocolo).
  * Estadísticas: transmisiones, entregas, pérdidas, por performativa y por patrón.
"""
from collections import Counter, defaultdict
import itertools


class Performativa:
    """Actos comunicativos de FIPA-ACL que usamos."""
    INFORM = 'INFORM'                    # compartir información
    QUERY_REF = 'QUERY_REF'              # preguntar por un valor
    REQUEST = 'REQUEST'                  # pedir una acción (reservar turno de carga)
    AGREE = 'AGREE'                      # aceptar la petición
    REFUSE = 'REFUSE'                    # rechazar la petición
    PROPOSE = 'PROPOSE'                  # proponerse para un recurso
    REJECT_PROPOSAL = 'REJECT_PROPOSAL'  # rechazar una propuesta
    CANCEL = 'CANCEL'                    # anular una petición anterior

    TODAS = [INFORM, QUERY_REF, REQUEST, AGREE, REFUSE, PROPOSE, REJECT_PROPOSAL, CANCEL]


class Mensaje:
    _ids = itertools.count()

    def __init__(self, performativa, emisor, contenido=None, receptor=None, tema=None,
                 conversacion=None, enRespuestaA=None, turno=None):
        self.id = next(Mensaje._ids)
        self.performativa = performativa
        self.emisor = emisor
        self.receptor = receptor          # se rellena al entregar
        self.tema = tema
        self.contenido = dict(contenido or {})
        self.conversacion = conversacion
        self.enRespuestaA = enRespuestaA
        self.turno = turno

    def copiaPara(self, receptor):
        m = Mensaje(self.performativa, self.emisor, self.contenido, receptor, self.tema,
                    self.conversacion, self.enRespuestaA, self.turno)
        m.id = self.id
        return m

    def __repr__(self):
        destino = self.receptor if self.receptor is not None else '*'
        tema = ' [%s]' % self.tema if self.tema else ''
        return '(%s %s->%s%s %s)' % (self.performativa, self.emisor, destino, tema, self.contenido)


class Canal:
    """Medio de comunicación compartido por todos los agentes de la colonia.

    Los mensajes enviados en el turno t se entregan al final de ese turno y el
    receptor los lee al principio del turno t+1 (latencia = 1 turno).
    Cada entrega individual se pierde con probabilidad 'perdida'.
    """

    def __init__(self, rng, perdida=0.0, oyente=None):
        self.rng = rng
        self.perdida = perdida
        self.oyente = oyente                  # función opcional para registrar cada envío (log)
        self.buzones = {}
        self.pendientes = []                  # (receptor, mensaje) a entregar al final del turno
        self.grupos = defaultdict(set)
        self.suscriptores = defaultdict(set)
        self.retenidos = defaultdict(dict)    # tema -> clave -> mensaje
        self.ultimasEntregas = []             # para dibujar quién habló con quién en el último turno
        self.transmisiones = 0
        self.entregas = 0
        self.perdidos = 0
        self.porPerformativa = Counter()
        self.porPatron = Counter()

    # ------------------------------------------------------------------ alta
    def registrar(self, agente, grupos=()):
        self.buzones[agente] = []
        for g in grupos:
            self.grupos[g].add(agente)

    # --------------------------------------------------------------- envíos
    def _encolar(self, mensaje, receptores, patron):
        receptores = [r for r in receptores if r != mensaje.emisor]
        self.transmisiones += 1
        self.porPerformativa[mensaje.performativa] += 1
        self.porPatron[patron] += 1
        if self.oyente:
            self.oyente(mensaje, receptores, patron)
        for r in receptores:
            self.pendientes.append((r, mensaje.copiaPara(r)))

    def enviar(self, mensaje, receptor):
        """Punto a punto."""
        self._encolar(mensaje, [receptor], 'punto-a-punto')

    def broadcast(self, mensaje):
        """A todos los agentes registrados."""
        self._encolar(mensaje, list(self.buzones), 'broadcast')

    def multicast(self, mensaje, grupo):
        """A un grupo concreto de agentes."""
        self._encolar(mensaje, sorted(self.grupos[grupo], key=str), 'multicast')

    # ------------------------------------------------------ publicar-suscribir
    def suscribir(self, agente, tema):
        if agente in self.suscriptores[tema]:
            return
        self.suscriptores[tema].add(agente)
        # Mensajes retenidos: el nuevo suscriptor recibe el estado actual del tema
        for m in self.retenidos[tema].values():
            self.pendientes.append((agente, m.copiaPara(agente)))

    def desuscribir(self, agente, tema):
        self.suscriptores[tema].discard(agente)

    def publicar(self, mensaje, tema, clave=None, retener=False, borrar=False):
        """Publica en un tema. Con 'retener' el broker guarda el mensaje bajo 'clave';
        con 'borrar' elimina el retenido de esa clave (p. ej. un recurso ya recogido)."""
        mensaje.tema = tema
        if clave is not None:
            if borrar:
                self.retenidos[tema].pop(clave, None)
            elif retener:
                self.retenidos[tema][clave] = mensaje
        self._encolar(mensaje, sorted(self.suscriptores[tema], key=str), 'publicar-suscribir')

    def olvidarRetenido(self, tema, clave):
        """El broker limpia un retenido caducado (no genera tráfico)."""
        self.retenidos[tema].pop(clave, None)

    # --------------------------------------------------------------- entrega
    def entregar(self):
        """Fin de turno: mueve los mensajes pendientes a los buzones (con posibles pérdidas)."""
        self.ultimasEntregas = []
        for receptor, m in self.pendientes:
            if self.perdida > 0 and self.rng.random() < self.perdida:
                self.perdidos += 1
                continue
            self.buzones[receptor].append(m)
            self.entregas += 1
            self.ultimasEntregas.append((m.emisor, receptor, m.performativa))
        self.pendientes = []

    def recibir(self, agente):
        mensajes = self.buzones[agente]
        self.buzones[agente] = []
        return mensajes

    # ---------------------------------------------------------- estadísticas
    def estadisticas(self):
        return {'transmisiones': self.transmisiones, 'entregas': self.entregas,
                'perdidos': self.perdidos,
                'porPerformativa': dict(self.porPerformativa),
                'porPatron': dict(self.porPatron)}
