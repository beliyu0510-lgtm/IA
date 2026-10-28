"""
entornoColonia.py - Entorno del ejercicio 2: "Colonia en escasez".

Reutiliza el entorno de Berkeley de la práctica (carpeta ../entorno):
  * layout.py              -> lectura del laberinto (muros, cápsulas = estaciones, 1-6 = salidas)
  * distanceCalculator.py  -> distancias reales dentro del laberinto
  * game.py                -> Directions / Actions para los movimientos

Ahora no hay dos equipos enfrentados: todos los agentes forman UNA colonia que
coopera para sobrevivir y recolectar con recursos escasos.

Reglas (por turno):
  * Aparecen suministros en casillas aleatorias (prob. 'probAparicion') y caducan
    pasados unos turnos. Son escasos y efímeros.
  * Cada recolector ve solo lo que está a distancia Manhattan <= 'radioVision'.
  * Un recolector puede llevar 1 suministro; al llegar al almacén (D) lo entrega: +1 a la colonia.
  * Moverse gasta 1 de batería; quedarse quieto gasta 'consumoBasal'.
    Con batería 0 el agente queda AGOTADO para el resto de la partida (y pierde lo que lleve).
  * Solo hay 2 estaciones de carga (o) y cada una carga a UN agente a la vez.
    El resto espera en la estación gastando batería basal.
"""
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
ENTORNO = os.path.join(os.path.dirname(AQUI), 'entorno')
if ENTORNO not in sys.path:
    sys.path.insert(0, ENTORNO)

import layout as berkeleyLayout                      # noqa: E402  (entorno de Berkeley)
from distanceCalculator import Distancer             # noqa: E402
from game import Directions, Actions                 # noqa: E402


class Config:
    """Parámetros del problema. Se pueden cambiar desde la línea de comandos."""
    def __init__(self, **kw):
        self.turnos = 500
        self.numAgentes = 6
        self.radioVision = 5
        self.bateriaMax = 50.0
        self.consumoMover = 1.0
        self.consumoBasal = 0.25
        self.velocidadCarga = 5.0
        self.probAparicion = 0.25
        self.vidaMin = 30
        self.vidaMax = 50
        self.maxRecursos = 8
        self.perdida = 0.0                 # probabilidad de perder cada mensaje
        for k, v in kw.items():
            if not hasattr(self, k):
                raise ValueError('Parámetro desconocido: %s' % k)
            setattr(self, k, v)


def cargarLayout(nombre):
    """Busca el .lay en ejercicio2/layouts y después en entorno/layouts."""
    candidatos = [nombre, os.path.join(AQUI, 'layouts', nombre), os.path.join(AQUI, 'layouts', nombre + '.lay'),
                  os.path.join(ENTORNO, 'layouts', nombre + '.lay')]
    for ruta in candidatos:
        if os.path.isfile(ruta):
            with open(ruta) as f:
                return berkeleyLayout.Layout([l.rstrip('\n') for l in f if l.strip()])
    raise SystemExit('No encuentro el layout %s' % nombre)


class Mapa:
    """Información estática que todos los agentes conocen de antemano."""

    def __init__(self, lay):
        self.layout = lay
        self.ancho, self.alto = lay.width, lay.height
        self.muros = lay.walls
        self.libres = [(x, y) for x in range(self.ancho) for y in range(self.alto) if not self.muros[x][y]]
        self.estaciones = sorted(lay.capsules)
        self.salidas = [pos for _, pos in lay.agentPositions]
        # 'D' (almacén) no existe en Berkeley: lo leemos del texto del layout
        self.almacen = None
        for fila, linea in enumerate(lay.layoutText):
            col = linea.find('D')
            if col >= 0:
                self.almacen = (col, self.alto - 1 - fila)
        if self.almacen is None:
            self.almacen = self.salidas[0]
        if len(self.estaciones) == 0:
            raise SystemExit('El layout necesita al menos una estación de carga (o)')
        self.distancer = Distancer(lay)
        self.distancer.getMazeDistances()

    def dist(self, a, b):
        return self.distancer.getDistance(a, b)

    def vecinos(self, pos):
        """(acción, casilla) alcanzables desde pos con un movimiento."""
        res = []
        for accion in [Directions.NORTH, Directions.SOUTH, Directions.EAST, Directions.WEST]:
            dx, dy = Actions.directionToVector(accion)
            sig = (int(pos[0] + dx), int(pos[1] + dy))
            if not self.muros[sig[0]][sig[1]]:
                res.append((accion, sig))
        return res

    def pasoHacia(self, pos, objetivo):
        """Primera acción del camino más corto (las distancias ya están precalculadas)."""
        if objetivo is None or pos == objetivo:
            return Directions.STOP
        mejor = min(self.vecinos(pos), key=lambda av: (self.dist(av[1], objetivo), av[0]))
        return mejor[0]

    def estacionMasCercana(self, pos):
        return min(self.estaciones, key=lambda e: (self.dist(pos, e), e))


class EstadoRecolector:
    def __init__(self, idx, pos, bateria):
        self.idx = idx
        self.pos = pos
        self.bateria = bateria
        self.lleva = False
        self.agotado = False
        self.llegadaEstacion = None          # turno en que llegó a la estación (para FIFO)


class Percepcion:
    """Lo que ve un recolector en su turno (observabilidad parcial)."""
    def __init__(self, turno, estado, recursosVisibles, companerosVisibles, celdasVisibles):
        self.turno = turno
        self.pos = estado.pos
        self.bateria = estado.bateria
        self.lleva = estado.lleva
        self.recursos = recursosVisibles          # {pos: turno de caducidad}
        self.companeros = companerosVisibles      # {idx: pos}
        self.celdasVisibles = celdasVisibles      # función pos -> bool


class Colonia:
    """Simulación completa: mundo + agentes + canal."""

    def __init__(self, mapa, config, recolectores, estaciones, canal, rng):
        self.mapa = mapa
        self.cfg = config
        self.rng = rng
        self.canal = canal
        self.recolectores = recolectores           # lista de AgenteRecolector
        self.estacionesAg = estaciones             # lista de AgenteEstacion (una por estación)
        self.turno = 0
        self.recursos = {}                         # pos -> turno de caducidad
        self.estados = [EstadoRecolector(i, mapa.salidas[i % len(mapa.salidas)], config.bateriaMax)
                        for i in range(len(recolectores))]
        self.libresRecurso = [c for c in mapa.libres if c not in mapa.estaciones and c != mapa.almacen
                              and c not in mapa.salidas]
        self.stats = {'entregados': 0, 'recogidos': 0, 'caducados': 0, 'aparecidos': 0,
                      'agotados': 0, 'perdidosPorAgotamiento': 0, 'turnosEspera': 0,
                      'turnosCarga': 0, 'objetivosFallidos': 0, 'pasos': 0}
        self.cargando = {}                         # estación -> idx del agente que está cargando
        for ag in recolectores:
            ag.conectar(self)
        for ag in estaciones:
            ag.conectar(self)

    # ------------------------------------------------------------ percepción
    def visible(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1]) <= self.cfg.radioVision

    def percibir(self, idx):
        e = self.estados[idx]
        recs = {p: c for p, c in self.recursos.items() if self.visible(e.pos, p)}
        comp = {o.idx: o.pos for o in self.estados if o.idx != idx and self.visible(e.pos, o.pos)}
        return Percepcion(self.turno, e, recs, comp, lambda p, pos=e.pos: self.visible(pos, p))

    # ------------------------------------------------------------ dinámica
    def generarRecursos(self):
        for p in [p for p, cad in self.recursos.items() if cad <= self.turno]:
            del self.recursos[p]
            self.stats['caducados'] += 1
            self.canal.olvidarRetenido('recursos', p)
        if len(self.recursos) < self.cfg.maxRecursos and self.rng.random() < self.cfg.probAparicion:
            ocupadas = set(self.recursos) | {e.pos for e in self.estados}
            candidatas = [c for c in self.libresRecurso if c not in ocupadas]
            if candidatas:
                p = self.rng.choice(candidatas)
                self.recursos[p] = self.turno + self.rng.randint(self.cfg.vidaMin, self.cfg.vidaMax)
                self.stats['aparecidos'] += 1

    def mover(self, idx, accion):
        e = self.estados[idx]
        if accion != Directions.STOP:
            dx, dy = Actions.directionToVector(accion)
            sig = (int(e.pos[0] + dx), int(e.pos[1] + dy))
            if self.mapa.muros[sig[0]][sig[1]]:
                raise ValueError('Acción ilegal %s del agente %d en %s' % (accion, idx, e.pos))
            e.pos = sig
            e.bateria -= self.cfg.consumoMover
            self.stats['pasos'] += 1
        # recoger
        if not e.lleva and e.pos in self.recursos:
            del self.recursos[e.pos]
            e.lleva = True
            self.stats['recogidos'] += 1
            self.recolectores[idx].alRecoger(e.pos)
        # entregar
        if e.lleva and e.pos == self.mapa.almacen:
            e.lleva = False
            self.stats['entregados'] += 1
            self.recolectores[idx].alEntregar()
        # llegada a estación
        if e.pos in self.mapa.estaciones:
            if e.llegadaEstacion is None:
                e.llegadaEstacion = self.turno
        else:
            e.llegadaEstacion = None

    def cargar(self):
        """Cada estación carga como mucho a un agente por turno; los demás esperan."""
        servidos = set()
        for est, agEst in zip(self.mapa.estaciones, self.estacionesAg):
            presentes = [e.idx for e in self.estados if not e.agotado and e.pos == est
                         and self.recolectores[e.idx].quiereCargar()]
            actual = self.cargando.get(est)
            actual = agEst.elegir(presentes, actual, self.turno, self.estados) if presentes else None
            self.cargando[est] = actual
            if actual is not None:
                e = self.estados[actual]
                e.bateria = min(self.cfg.bateriaMax, e.bateria + self.cfg.velocidadCarga)
                servidos.add(actual)
                self.stats['turnosCarga'] += 1
                for otro in presentes:
                    if otro != actual:
                        self.stats['turnosEspera'] += 1
        return servidos

    def paso(self):
        self.generarRecursos()
        for agEst in self.estacionesAg:
            agEst.actuar(self.turno)
        movidos = {}
        for ag in self.recolectores:
            e = self.estados[ag.idx]
            if e.agotado:
                continue
            accion = ag.actuar(self.percibir(ag.idx))
            if accion not in [a for a, _ in self.mapa.vecinos(e.pos)] + [Directions.STOP]:
                accion = Directions.STOP
            self.mover(ag.idx, accion)
            movidos[ag.idx] = accion
        servidos = self.cargar()
        for idx, accion in movidos.items():
            e = self.estados[idx]
            if accion == Directions.STOP and idx not in servidos:
                e.bateria -= self.cfg.consumoBasal
            if e.bateria <= 0 and not e.agotado:
                e.bateria = 0.0
                e.agotado = True
                self.stats['agotados'] += 1
                if e.lleva:
                    e.lleva = False
                    self.stats['perdidosPorAgotamiento'] += 1
                self.recolectores[idx].alAgotarse()
        self.canal.entregar()
        self.turno += 1

    def jugar(self, alTurno=None):
        while self.turno < self.cfg.turnos:
            self.paso()
            if alTurno:
                alTurno(self)
        return self.resultados()

    def resultados(self):
        r = dict(self.stats)
        r['bateriaMedia'] = sum(e.bateria for e in self.estados) / len(self.estados)
        r['vivos'] = sum(1 for e in self.estados if not e.agotado)
        c = self.canal.estadisticas()
        r['transmisiones'] = c['transmisiones']
        r['entregasMensajes'] = c['entregas']
        r['mensajesPerdidos'] = c['perdidos']
        r['porPerformativa'] = c['porPerformativa']
        r['porPatron'] = c['porPatron']
        return r
