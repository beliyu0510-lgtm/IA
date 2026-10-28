"""
demo.py - Partida de demostración con el Contract Net a la vista.

  python3 main.py                    -> tu equipo (rojo) contra baselineTeam, con ventana gráfica
  python3 main.py MyTeam             -> tu equipo (rojo) contra tu equipo (azul), con ventana gráfica

La ventana muestra la partida; esta consola va contando qué se dicen los agentes.
"""
import sys, os

import importlib

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..'))

# Los archivos de Berkeley dentro de "entorno" se importan unos a otros por su nombre suelto
# (from util import *) y otros con prefijo (from entorno.game import ...). Para que no se
# mezclen, cada módulo se registra con AMBOS nombres, apuntando al mismo objeto.
for nombre in ['util', 'game', 'layout', 'distanceCalculator', 'captureAgents', 'graphicsUtils',
               'textDisplay', 'keyboardAgents', 'captureGraphicsDisplay']:
    try:
        sys.modules[nombre] = importlib.import_module('entorno.' + nombre)
    except ImportError:
        pass                          # p. ej. sin tkinter no hay gráficos; se avisará al usarlos
import entorno.capture as capture
import TeamComut                         # el MISMO módulo que importa tu myTeam.py

# ---------------------------------------------------------------------------
# Para "escuchar" el buzón sin tocar tu código: envolvemos send y broadcast.
# ---------------------------------------------------------------------------
def equipo(indice):
    return 'ROJO' if indice % 2 == 0 else 'AZUL'

def tarea(nombre):
    return nombre.replace(' BANDERA', '').replace('PATRULLA CENTRAL', 'PATRULLAR')

def contar(tipo, emisor, destino, c, turno):
    """Una línea legible por mensaje. destino = None si es broadcast."""
    quien = '%s ag.%d' % (equipo(emisor), emisor)
    if tipo == 'ANUNCIO':
        print('[t%3s] %s ANUNCIA  %s  (%d plaza/s, objetivo %s)'
              % (turno, quien, tarea(c['task']), c['plazas'], c['target']))
    elif tipo == 'PUJA':
        print('[t%3s] %s puja %.1f por %s  (a ag.%d)' % (turno, quien, c['bid'], tarea(c['task']), destino))
    elif tipo == 'ADJUDICACION':
        print('[t%3s] %s ADJUDICA %s  ->  agentes %s' % (turno, quien, tarea(c['task']), c['winners']))
    elif tipo == 'LIBERADA':
        print('[t%3s] %s se libera de %s' % (turno, quien, tarea(c['task'])))

_send, _broadcast = TeamComut.TeamBus.send, TeamComut.TeamBus.broadcast

def send(self, *a, **k):                 # a = (emisor, receptor, tipo, contenido, turno)
    contar(a[2], a[0], a[1], a[3], a[4])
    return _send(self, *a, **k)

def broadcast(self, *a, **k):            # a = (emisor, tipo, contenido, turno)
    contar(a[1], a[0], None, a[2], a[3])
    return _broadcast(self, *a, **k)

TeamComut.TeamBus.send = send
TeamComut.TeamBus.broadcast = broadcast

# ---------------------------------------------------------------------------
PAUSA = 0.1                 # segundos por movimiento en la ventana (sube el número para verlo más lento)
MI_EQUIPO = 'myTeam'        # nombre del archivo de tu equipo (sin .py)


def buscar(nombre):
    """Busca el archivo del equipo en las carpetas habituales."""
    aqui = os.path.dirname(os.path.abspath(__file__))
    carpetas = [
        os.getcwd(),
        aqui,
        os.path.join(aqui, 'entorno'),
        os.path.join(aqui, '..', 'entorno'),
        os.path.join(aqui, '..'),
    ]

    for carpeta in carpetas:
        ruta = os.path.abspath(os.path.join(carpeta, nombre + '.py'))
        if os.path.isfile(ruta):
            return ruta

    raise SystemExit(
        f"No encuentro {nombre}.py. "
        f"Carpetas comprobadas: {[os.path.abspath(c) for c in carpetas]}"
    )


def buscarLayout(nombre = 'flagCapture'):
    """layout.py solo busca layouts/ desde donde lanzas; aquí también en entorno/layouts."""
    aqui = os.path.dirname(os.path.abspath(__file__))
    for carpeta in [os.getcwd(), aqui, os.path.join(aqui, 'entorno'), os.path.join(aqui, '..', 'entorno')]:
        ruta = os.path.join(carpeta, 'layouts', nombre + '.lay')
        if os.path.exists(ruta):
            return ruta
    return None                                      # que capture.py dé su propio error

if __name__ == '__main__':
    resto = sys.argv[1:]
    rival = resto.pop(0) if resto and not resto[0].startswith('-') else 'baselineTeam'
    mapa = [] if ('-l' in resto or '--layout' in resto) else ['-l', buscarLayout() or 'flagCapture']
    args = capture.readCommand(['-r', buscar(MI_EQUIPO), '-b', buscar(rival), '-n', '1'] + mapa + resto)
    if hasattr(args['display'], 'frameTime'):        # con -q o -t no hay ventana que ralentizar
        args['display'].frameTime = PAUSA
    capture.runGames(**args)