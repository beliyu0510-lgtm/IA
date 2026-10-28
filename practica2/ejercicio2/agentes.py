"""
agentes.py - Agentes del ejercicio 2 (sin LLMs).

Dos tipos de agente (especialización funcional):
  * AgenteRecolector (móvil, N unidades): explora, recoge suministros, los lleva al
    almacén y recarga batería.
  * AgenteEstacion (fijo, uno por estación de carga): gestiona su cola de reservas y
    responde a consultas y peticiones (patrón petición-respuesta).

Protocolos de comunicación (estrategia 'pubsub', la propuesta):
  P1  Difusión de avistamientos (publicar-suscribir, tema 'recursos', con retenidos)
        INFORM {pos, caducidad}       al ver un suministro nuevo
        INFORM {pos, recogido}        al recogerlo (borra el retenido)
      Solo están suscritos los recolectores libres: quien carga o lleva algo se da de baja
      y, al volver, el broker le entrega el estado actual (mensajes retenidos).
  P2  Reparto de suministros (propuesta/rechazo, tema 'recursos')
        PROPOSE {pos, eta}            "voy a por éste, llego en eta turnos"
        REJECT_PROPOSAL {pos, eta}    "yo llego antes" (punto a punto)
        CANCEL {pos}                  "lo dejo" (p. ej. me voy a recargar)
  P3  Reserva de estaciones (petición-respuesta con los agentes estación)
        QUERY_REF {eta, dur}          multicast al grupo 'estaciones': ¿cuánto esperaría?
        INFORM {inicio, espera}       respuesta de cada estación
        REQUEST {eta, dur}            reserva en la estación elegida
        AGREE {inicio} / REFUSE       respuesta; si no llega, se reintenta (tolerancia a pérdidas)
        CANCEL                        anulación si el agente cambia de estación
  P4  Coordinación de la exploración (tema 'exploracion')
        INFORM {visitado, voy}        zona recién vista y zona a la que me dirijo
"""
import math

from mensajes import Mensaje, Performativa as P
from entornoColonia import Directions

MARGEN = 4.0                  # batería extra que se guarda siempre para llegar a una estación
MAX_ESPERA_OPORTUNISTA = 5    # una estación rechaza recargas no urgentes si se esperaría más
ANTIGUEDAD_MIN = 30           # no se explora una zona vista hace menos turnos que esto
ENFRIAMIENTO = 20             # turnos sin volver a intentar una recarga no urgente rechazada
TIMEOUT = 3                   # turnos que se espera una respuesta antes de reintentar
MAX_INTENTOS = 2

ESTRATEGIAS = {
    # nombre: (cómo se comparten avistamientos, reclamos, reservas, exploración coordinada)
    'sin_com':             dict(compartir=None,        reclamos=False, reservas=False, explorar=False),
    'broadcast':           dict(compartir='broadcast', reclamos=False, reservas=False, explorar=False),
    'pubsub_sin_reclamos': dict(compartir='pubsub',    reclamos=False, reservas=True,  explorar=True),
    'pubsub_sin_reservas': dict(compartir='pubsub',    reclamos=True,  reservas=False, explorar=True),
    'pubsub':              dict(compartir='pubsub',    reclamos=True,  reservas=True,  explorar=True),
}


def puntosExploracion(mapa, pasoX=5, pasoY=4):
    """Rejilla gruesa de casillas libres que sirven como zonas a explorar."""
    puntos = []
    for gx in range(2, mapa.ancho, pasoX):
        for gy in range(2, mapa.alto, pasoY):
            p = min(mapa.libres, key=lambda c: (abs(c[0] - gx) + abs(c[1] - gy), c))
            if p not in puntos:
                puntos.append(p)
    return puntos


# =====================================================================================
class AgenteEstacion:
    """Agente fijo que gestiona una estación de carga (recurso escaso, capacidad 1).

    La batería de cada recolector es información PRIVADA: la estación solo mide la del
    agente que está cargando. De los que esperan solo sabe lo que le hayan comunicado.
      * Sin reservas (sin comunicación): atiende por orden de llegada, sin interrupciones.
      * Con reservas: arbitraje por urgencia (menor batería estimada primero) y puede
        interrumpir una carga avanzada si llega alguien en estado crítico.
    """

    def __init__(self, nombre, pos, conReservas):
        self.nombre = nombre
        self.pos = pos
        self.conReservas = conReservas
        self.reservas = {}        # agente -> dict(eta, dur, turno, bateriaLlegada)
        self.servidos = set()     # agentes con reserva que ya han empezado a cargar
        self.cargado = {}         # energía que la estación ha dado a cada agente (lo mide ella)

    def conectar(self, colonia):
        self.colonia = colonia
        self.canal = colonia.canal
        self.cfg = colonia.cfg
        self.canal.registrar(self.nombre, grupos=['estaciones'])

    # -------------------------------------------------------------- agenda
    def _finActual(self, t):
        """Turno en que quedará libre por el agente que está cargando ahora (lo mide la estación)."""
        actual = self.colonia.cargando.get(self.pos)
        if actual is None:
            return t
        e = self.colonia.estados[actual]
        return t + math.ceil((self.cfg.bateriaMax - e.bateria) / self.cfg.velocidadCarga)

    def estimarInicio(self, t, agente, eta, dur):
        """Simula la cola de reservas y devuelve cuándo podría empezar a cargar 'agente'."""
        libre = self._finActual(t)
        actual = self.colonia.cargando.get(self.pos)
        cola = sorted((r['turno'] + r['eta'], a, r['dur']) for a, r in self.reservas.items()
                      if a != agente and a != actual)
        for llegada, _, d in cola:
            libre = max(libre, llegada) + d
        return max(libre, t + eta)

    def _limpiar(self, t):
        estados = self.colonia.estados
        cargando = self.colonia.cargando.get(self.pos)
        for a in list(self.reservas):
            r = self.reservas[a]
            if a == cargando:
                self.servidos.add(a)
            presente = estados[a].pos == self.pos and not estados[a].agotado
            terminado = a in self.servidos and not presente
            caducada = t > r['turno'] + r['eta'] + r['dur'] + 10 and not presente
            if terminado or caducada or estados[a].agotado:
                del self.reservas[a]
                self.servidos.discard(a)
                self.cargado.pop(a, None)

    # ------------------------------------------------------------- actuar
    def actuar(self, t):
        if self.conReservas:
            self._limpiar(t)
        for m in self.canal.recibir(self.nombre):
            c = m.contenido
            if m.performativa == P.QUERY_REF:
                eta = c['eta'][self.nombre]
                inicio = self.estimarInicio(t, m.emisor, eta, c['dur'])
                self._responder(m, P.INFORM, {'inicio': inicio, 'espera': inicio - (t + eta)}, t)
            elif m.performativa == P.REQUEST:
                eta, dur = c['eta'], c['dur']
                inicio = self.estimarInicio(t, m.emisor, eta, dur)
                espera = inicio - (t + eta)
                if c.get('oportunista') and espera > MAX_ESPERA_OPORTUNISTA:
                    # no es urgente y hay cola: mejor que siga trabajando
                    self._responder(m, P.REFUSE, {'espera': espera}, t)
                else:
                    self.reservas[m.emisor] = dict(eta=eta, dur=dur, turno=t, bateriaLlegada=c['bateria'])
                    self.cargado.pop(m.emisor, None)
                    self._responder(m, P.AGREE, {'inicio': inicio}, t)
            elif m.performativa == P.CANCEL:
                self.reservas.pop(m.emisor, None)
                self.servidos.discard(m.emisor)

    def _responder(self, m, performativa, contenido, t):
        r = Mensaje(performativa, self.nombre, contenido, conversacion=m.conversacion,
                    enRespuestaA=m.id, turno=t)
        self.canal.enviar(r, m.emisor)

    # ----------------------------------------------------------- arbitraje
    def bateriaEstimada(self, a, t, estados):
        """Lo que la estación cree que le queda a un agente que espera (None si no lo sabe)."""
        r = self.reservas.get(a)
        if r is None:
            return None
        espera = t - (estados[a].llegadaEstacion if estados[a].llegadaEstacion is not None else t)
        cargado = self.cargado.get(a, 0.0)
        return min(self.cfg.bateriaMax, r['bateriaLlegada'] + cargado) - self.cfg.consumoBasal * (espera - cargado / self.cfg.velocidadCarga)

    def elegir(self, presentes, actual, t, estados):
        """A quién carga la estación en este turno."""
        llegada = lambda a: (estados[a].llegadaEstacion, a)
        if not self.conReservas:                                   # FIFO sin interrupciones
            return actual if actual in presentes else min(presentes, key=llegada)

        def prioridad(a):
            b = self.bateriaEstimada(a, t, estados)
            if b is None:                                          # no sé nada de él
                return (1 if t - estados[a].llegadaEstacion <= 8 else 0, 0, a)
            return (0, b, a)

        elegido = actual if actual in presentes else min(presentes, key=prioridad)
        if actual in presentes:
            # Solo interrumpo si alguien que espera se agotaría antes de que termine el actual
            restante = math.ceil((self.cfg.bateriaMax - estados[actual].bateria) / self.cfg.velocidadCarga)
            criticos = [a for a in presentes if a != actual and self.bateriaEstimada(a, t, estados) is not None
                        and self.bateriaEstimada(a, t, estados) - self.cfg.consumoBasal * restante <= 1]
            if criticos and estados[actual].bateria >= 0.5 * self.cfg.bateriaMax:
                elegido = min(criticos, key=prioridad)
        self.cargado[elegido] = self.cargado.get(elegido, 0.0) + self.cfg.velocidadCarga
        return elegido


# =====================================================================================
class AgenteRecolector:

    def __init__(self, idx, estrategia, rng):
        self.idx = idx
        self.nombreEstrategia = estrategia
        self.e = ESTRATEGIAS[estrategia]
        self.rng = rng
        self.creencias = {}         # pos -> caducidad de los suministros que creo que existen
        self.reclamos = {}          # pos -> (agente, eta, turno) propuestas de otros
        self.objetivo = None        # suministro al que voy
        self.wp = None              # zona de exploración a la que voy
        self.visitas = {}           # zona -> último turno en que se vio (propio o comunicado)
        self.intenciones = {}       # agente -> (zona, turno)
        self.modo = None            # None | 'RECARGAR'
        self.recarga = None
        self.conv = 0
        self.enfriamiento = 0

    def conectar(self, colonia):
        self.colonia = colonia
        self.mapa = colonia.mapa
        self.cfg = colonia.cfg
        self.canal = colonia.canal
        self.canal.registrar(self.idx, grupos=['recolectores'])
        self.zonas = puntosExploracion(self.mapa)
        if self.e['compartir'] == 'pubsub':
            self.canal.suscribir(self.idx, 'recursos')
        if self.e['explorar']:
            self.canal.suscribir(self.idx, 'exploracion')

    # ------------------------------------------------------------ utilidades
    def d(self, a, b):
        return self.mapa.dist(a, b)

    def reservaEn(self, pos):
        """Batería mínima que debo tener al estar en pos para llegar a una estación."""
        return self.d(pos, self.mapa.estacionMasCercana(pos)) * self.cfg.consumoMover + MARGEN

    def puedoIr(self, *ruta):
        """¿Puedo recorrer pos -> ruta[0] -> ... y aun así llegar a una estación?"""
        gasto, actual = 0, self.per.pos
        for p in ruta:
            gasto += self.d(actual, p) * self.cfg.consumoMover
            actual = p
        return self.per.bateria - gasto >= self.reservaEn(actual)

    def _msg(self, performativa, contenido, **kw):
        return Mensaje(performativa, self.idx, contenido, turno=self.per.turno, **kw)

    def publicar(self, performativa, contenido, tema, **kw):
        self.canal.publicar(self._msg(performativa, contenido), tema, **kw)

    # -------------------------------------------------------- callbacks entorno
    def quiereCargar(self):
        return self.modo == 'RECARGAR' and self.colonia.estados[self.idx].bateria < self.cfg.bateriaMax

    def alRecoger(self, pos):
        self.creencias.pop(pos, None)
        self.objetivo = None
        if self.e['compartir'] == 'pubsub':
            self.publicar(P.INFORM, {'pos': pos, 'recogido': True}, 'recursos', clave=pos, borrar=True)
            self.canal.desuscribir(self.idx, 'recursos')     # ocupado: no me interesan avistamientos
        elif self.e['compartir'] == 'broadcast':
            self.canal.broadcast(self._msg(P.INFORM, {'pos': pos, 'recogido': True}))

    def alEntregar(self):
        if self.e['compartir'] == 'pubsub' and self.modo != 'RECARGAR':
            self.resuscribir()                                    # vuelvo a estar libre

    def resuscribir(self):
        """Mientras estaba de baja no me enteré de lo que se recogió: descarto mis creencias
        y el broker me reenvía el estado vigente (mensajes retenidos)."""
        self.creencias = {}
        self.canal.suscribir(self.idx, 'recursos')

    def alAgotarse(self):
        for tema in ('recursos', 'exploracion'):
            self.canal.desuscribir(self.idx, tema)

    # ---------------------------------------------------------------- turno
    def actuar(self, per):
        self.per = per
        t = per.turno
        for m in self.canal.recibir(self.idx):
            self.procesar(m, t)
        self.observar(per, t)

        if self.modo == 'RECARGAR':
            if per.pos in self.mapa.estaciones and per.bateria >= self.cfg.bateriaMax:
                self.terminarRecarga()
            else:
                accion = self.accionRecarga(t)
                if accion is not None:
                    return accion                              # (None = recarga no urgente abortada)

        if per.lleva:
            if self.puedoIr(self.mapa.almacen):
                return self.mapa.pasoHacia(per.pos, self.mapa.almacen)
            return self.iniciarRecarga(t)

        if per.bateria - self.reservaEn(per.pos) <= 1:
            return self.iniciarRecarga(t)

        r = self.elegirRecurso(t)
        if r is not None:
            return self.mapa.pasoHacia(per.pos, r)
        if per.bateria < 0.5 * self.cfg.bateriaMax and t >= self.enfriamiento:
            return self.iniciarRecarga(t, oportunista=True)   # sin nada que hacer: recarga no urgente
        wp = self.elegirZona(t)
        if wp is None:
            return self.iniciarRecarga(t)
        if wp == 'DESCANSAR':
            return Directions.STOP                          # todo está vigilado: ahorro batería
        return self.mapa.pasoHacia(per.pos, wp)

    # ------------------------------------------------------------ percepción
    def observar(self, per, t):
        nuevos = []
        for p, cad in per.recursos.items():
            if p not in self.creencias:
                nuevos.append(p)
            self.creencias[p] = cad
        # revisión de creencias: lo que debería ver y no veo ya no existe
        for p in list(self.creencias):
            if self.creencias[p] <= t or (per.celdasVisibles(p) and p not in per.recursos):
                del self.creencias[p]
                if p == self.objetivo:
                    self.colonia.stats['objetivosFallidos'] += 1
                    self.objetivo = None
        for p in list(self.reclamos):
            ag, eta, tr = self.reclamos[p]
            if p not in self.creencias or t - tr > eta + 5:
                del self.reclamos[p]
        for z in self.zonas:
            if per.celdasVisibles(z):
                self.visitas[z] = t
        # difusión de lo visto
        if self.e['compartir'] == 'pubsub':
            for p in nuevos:
                self.publicar(P.INFORM, {'pos': p, 'caducidad': per.recursos[p]}, 'recursos', clave=p, retener=True)
        elif self.e['compartir'] == 'broadcast' and per.recursos:
            # estrategia ingenua: cada turno se repite a todos lo que se ve
            self.canal.broadcast(self._msg(P.INFORM, {'recursos': dict(per.recursos)}))

    # --------------------------------------------------------------- mensajes
    def procesar(self, m, t):
        c = m.contenido
        if m.performativa == P.INFORM and isinstance(m.emisor, int):
            if 'recursos' in c:                                   # broadcast ingenuo
                for p, cad in c['recursos'].items():
                    if cad > t:
                        self.creencias[p] = cad
            elif c.get('recogido'):
                self.creencias.pop(c['pos'], None)
                self.reclamos.pop(c['pos'], None)
                if self.objetivo == c['pos']:
                    self.objetivo = None                          # me ahorro el viaje
            elif 'caducidad' in c:
                if c['caducidad'] > t:
                    self.creencias[c['pos']] = c['caducidad']
            elif 'visitado' in c:
                z = c['visitado']
                if z is not None:
                    self.visitas[z] = max(self.visitas.get(z, -999), c['turno'])
                self.intenciones[m.emisor] = (c['voy'], t)
        elif m.performativa == P.PROPOSE:
            p, eta = c['pos'], c['eta']
            if self.objetivo == p:
                mia = self.d(self.per.pos, p)
                if (mia, self.idx) < (eta, m.emisor):
                    self.canal.enviar(self._msg(P.REJECT_PROPOSAL, {'pos': p, 'eta': mia},
                                                enRespuestaA=m.id), m.emisor)
                    return
                self.objetivo = None                              # el otro llega antes: cedo
            previo = self.reclamos.get(p)
            if previo is None or eta < previo[1] - (t - previo[2]):
                self.reclamos[p] = (m.emisor, eta, t)
        elif m.performativa == P.REJECT_PROPOSAL:
            self.reclamos[c['pos']] = (m.emisor, c['eta'], t)
            if self.objetivo == c['pos']:
                self.objetivo = None
        elif m.performativa == P.CANCEL and m.tema == 'recursos':
            if self.reclamos.get(c['pos'], (None,))[0] == m.emisor:
                del self.reclamos[c['pos']]
        elif m.performativa in (P.INFORM, P.AGREE, P.REFUSE) and isinstance(m.emisor, str):
            self.respuestaEstacion(m, t)

    # ---------------------------------------------------------- suministros
    def elegirRecurso(self, t):
        pos = self.per.pos
        candidatos = []
        for p, cad in self.creencias.items():
            dist = self.d(pos, p)
            if t + dist >= cad or not self.puedoIr(p, self.mapa.almacen):
                continue
            if self.e['reclamos'] and p in self.reclamos:
                ag, eta, tr = self.reclamos[p]
                if ag != self.idx and eta - (t - tr) <= dist:
                    continue                                      # otro llega antes
            candidatos.append((dist, p))
        if not candidatos:
            self.soltarObjetivo()
            return None
        dist, p = min(candidatos)
        if self.objetivo is not None and self.objetivo != p and any(q == self.objetivo for _, q in candidatos):
            # mantengo mi objetivo salvo que el nuevo esté bastante más cerca (evita oscilar)
            if self.d(pos, self.objetivo) <= dist + 2:
                return self.objetivo
        if p != self.objetivo:
            self.soltarObjetivo()
            self.objetivo = p
            self.wp = None
            if self.e['reclamos']:
                self.publicar(P.PROPOSE, {'pos': p, 'eta': dist}, 'recursos')
        return p

    def soltarObjetivo(self):
        if self.objetivo is not None and self.e['reclamos'] and self.objetivo in self.creencias:
            self.publicar(P.CANCEL, {'pos': self.objetivo}, 'recursos')
        self.objetivo = None

    # ----------------------------------------------------------- exploración
    def elegirZona(self, t):
        pos = self.per.pos
        if self.wp is not None and pos != self.wp and not self.per.celdasVisibles(self.wp) \
                and self.puedoIr(self.wp) and not self._ocupada(self.wp, t):
            return self.wp
        anterior = self.wp
        mejor, mejorValor, alcanzable = None, -1e9, False
        for z in self.zonas:
            if self.e['explorar'] and self._ocupada(z, t):
                continue
            if not self.puedoIr(z):
                continue
            alcanzable = True
            antiguedad = t - self.visitas.get(z, -60)
            if antiguedad < ANTIGUEDAD_MIN:
                continue                                    # alguien la ha visto hace poco: no merece la pena
            valor = antiguedad - 0.8 * self.d(pos, z)
            if not self.e['explorar']:
                valor += 3 * self.rng.random()          # sin coordinación: desempate al azar
            if valor > mejorValor:
                mejor, mejorValor = z, valor
        self.wp = mejor
        if self.e['explorar'] and mejor != anterior:
            visto = anterior if anterior is not None and self.per.celdasVisibles(anterior) else None
            self.publicar(P.INFORM, {'visitado': visto, 'turno': t, 'voy': mejor}, 'exploracion')
        if mejor is None:
            return 'DESCANSAR' if alcanzable else None
        return mejor

    def _ocupada(self, z, t):
        return any(zona == z and t - tt <= 25 for ag, (zona, tt) in self.intenciones.items() if ag != self.idx)

    # --------------------------------------------------------------- recarga
    def iniciarRecarga(self, t, oportunista=False):
        self.soltarObjetivo()
        self.wp = None
        self.modo = 'RECARGAR'
        if self.e['compartir'] == 'pubsub':
            self.canal.desuscribir(self.idx, 'recursos')
        self.conv += 1
        self.recarga = {'estacion': self.mapa.estacionMasCercana(self.per.pos), 'fase': 'sinReserva',
                        'intentos': 0, 'respuestas': {}, 'rechazos': set(), 'nombre': None,
                        'oportunista': oportunista, 'conv': (self.idx, self.conv), 'limite': t}
        if self.e['reservas']:
            self._consultar(t)
        return self.accionRecarga(t)

    def abortarRecarga(self, t):
        """Recarga no urgente rechazada: sigo trabajando y no lo vuelvo a intentar en un rato."""
        self.modo = None
        self.recarga = None
        self.enfriamiento = t + ENFRIAMIENTO
        if self.e['compartir'] == 'pubsub' and not self.per.lleva:
            self.resuscribir()

    def _dur(self, eta):
        llegada = self.per.bateria - eta * self.cfg.consumoMover
        return math.ceil((self.cfg.bateriaMax - llegada) / self.cfg.velocidadCarga)

    def _nombreEstacion(self, pos):
        return 'E%d' % self.mapa.estaciones.index(pos)

    def _consultar(self, t):
        """QUERY_REF en multicast a todas las estaciones: ¿cuándo podría cargar?"""
        r = self.recarga
        r.update(fase='consultando', limite=t + TIMEOUT, respuestas={})
        r['intentos'] += 1
        etas = {self._nombreEstacion(e): self.d(self.per.pos, e) for e in self.mapa.estaciones}
        contenido = {'eta': etas, 'dur': self._dur(min(etas.values())), 'bateria': self.per.bateria,
                     'oportunista': r['oportunista']}
        self.canal.multicast(self._msg(P.QUERY_REF, contenido, conversacion=r['conv']), 'estaciones')

    def _pedir(self, t, pos):
        """REQUEST punto a punto a la estación elegida (reserva)."""
        r = self.recarga
        eta = self.d(self.per.pos, pos)
        r.update(fase='reservando', estacion=pos, nombre=self._nombreEstacion(pos), limite=t + TIMEOUT)
        r['intentos'] += 1
        contenido = {'eta': eta, 'dur': self._dur(eta), 'bateria': self.per.bateria - eta * self.cfg.consumoMover,
                     'oportunista': r['oportunista']}
        self.canal.enviar(self._msg(P.REQUEST, contenido, conversacion=r['conv']), r['nombre'])

    def respuestaEstacion(self, m, t):
        r = self.recarga
        if self.modo != 'RECARGAR' or r is None or m.conversacion != r.get('conv'):
            return                                              # respuesta de una conversación vieja
        if r['fase'] == 'consultando' and m.performativa == P.INFORM:
            r['respuestas'][m.emisor] = (m.contenido['inicio'], m.contenido['espera'])
        elif r['fase'] == 'reservando' and m.emisor == r['nombre']:
            if m.performativa == P.AGREE:
                r['fase'] = 'reservado'
            elif m.performativa == P.REFUSE:
                r['rechazos'].add(m.emisor)
                r['fase'] = 'rechazado'

    def accionRecarga(self, t):
        """Máquina de estados del protocolo de reserva. Devuelve None si se aborta."""
        r = self.recarga
        if r['fase'] == 'consultando':
            if len(r['respuestas']) == len(self.mapa.estaciones) or t >= r['limite']:
                alcanzables = {n: ini for n, (ini, espera) in r['respuestas'].items()
                               if self.puedoLlegar(self.mapa.estaciones[int(n[1:])])
                               and (not r['oportunista'] or espera <= MAX_ESPERA_OPORTUNISTA)}
                if r['oportunista'] and r['respuestas'] and not alcanzables:
                    self.abortarRecarga(t)                       # todas tienen cola: no merece la pena ir
                    return None
                if alcanzables:
                    nombre = min(alcanzables, key=lambda n: (alcanzables[n], n))
                    r['intentos'] = 0
                    self._pedir(t, self.mapa.estaciones[int(nombre[1:])])
                elif r['intentos'] <= MAX_INTENTOS and not r['respuestas']:
                    self._consultar(t)                           # reintento: se perdieron los mensajes
                else:
                    r['fase'] = 'sinReserva'
        elif r['fase'] == 'reservando' and t >= r['limite']:
            if r['intentos'] <= MAX_INTENTOS:
                self._pedir(t, r['estacion'])                    # reintento
            else:
                r['fase'] = 'sinReserva'
        elif r['fase'] == 'rechazado':
            if r['oportunista']:
                self.abortarRecarga(t)
                return None
            r['fase'] = 'sinReserva'
        elif r['fase'] == 'sinReserva' and self.e['reservas'] and self.per.pos == r['estacion'] \
                and t >= r['limite']:
            r['intentos'] = 0
            self._pedir(t, r['estacion'])                        # ya estoy aquí: pido turno en persona
        if not self.puedoLlegar(r['estacion']):
            # por seguridad: si la elegida queda fuera de alcance, a la más cercana
            if r.get('nombre') and r['fase'] in ('reservando', 'reservado'):
                self.canal.enviar(self._msg(P.CANCEL, {}, conversacion=r['conv']), r['nombre'])
            r['estacion'] = self.mapa.estacionMasCercana(self.per.pos)
            r['fase'] = 'sinReserva'
        return self.mapa.pasoHacia(self.per.pos, r['estacion'])

    def puedoLlegar(self, est):
        return self.per.bateria - self.d(self.per.pos, est) * self.cfg.consumoMover > 0

    def terminarRecarga(self):
        self.modo = None
        self.recarga = None
        if self.e['compartir'] == 'pubsub' and not self.per.lleva:
            self.resuscribir()
