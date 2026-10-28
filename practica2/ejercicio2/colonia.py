"""
colonia.py - Ejecuta una partida del ejercicio 2 ("Colonia en escasez").

Ejemplos (desde la carpeta practica2/):
  python3 ejercicio2/colonia.py                              -> estrategia pubsub, resumen final
  python3 ejercicio2/colonia.py -e sin_com                   -> sin comunicación
  python3 ejercicio2/colonia.py -v --pausa 0.1               -> mapa en la consola turno a turno
  python3 ejercicio2/colonia.py --log --turnos 60            -> imprime cada mensaje (performativa, patrón...)
  python3 ejercicio2/colonia.py --gif partida.gif --turnos 150   -> animación para las diapositivas
  python3 ejercicio2/colonia.py --perdida 0.3                -> 30 % de mensajes perdidos

Estrategias: sin_com, broadcast, pubsub_sin_reclamos, pubsub_sin_reservas, pubsub
"""
import argparse
import os
import random
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
if AQUI not in sys.path:
    sys.path.insert(0, AQUI)

from entornoColonia import Config, Colonia, Mapa, cargarLayout   # noqa: E402
from agentes import AgenteRecolector, AgenteEstacion, ESTRATEGIAS  # noqa: E402
from mensajes import Canal                                        # noqa: E402


def crearColonia(estrategia='pubsub', semilla=0, layout='colonia', oyente=None, mapa=None, **params):
    cfg = Config(**params)
    mapa = mapa or Mapa(cargarLayout(layout))
    if cfg.numAgentes > len(mapa.salidas):
        raise SystemExit('El layout solo tiene %d posiciones de salida' % len(mapa.salidas))
    rng = random.Random(semilla)
    canal = Canal(random.Random(semilla + 7919), cfg.perdida, oyente)
    recolectores = [AgenteRecolector(i, estrategia, random.Random(semilla * 100 + i)) for i in range(cfg.numAgentes)]
    conReservas = ESTRATEGIAS[estrategia]['reservas']
    estaciones = [AgenteEstacion('E%d' % k, pos, conReservas) for k, pos in enumerate(mapa.estaciones)]
    return Colonia(mapa, cfg, recolectores, estaciones, canal, rng)


# ------------------------------------------------------------------ consola
def dibujar(col):
    m = col.mapa
    filas = []
    agentes = {}
    for e in col.estados:
        agentes.setdefault(e.pos, []).append(e)
    for y in range(m.alto - 1, -1, -1):
        fila = ''
        for x in range(m.ancho):
            p = (x, y)
            if m.muros[x][y]:
                fila += '%'
            elif p in agentes:
                e = agentes[p][0]
                fila += 'x' if e.agotado else (chr(ord('A') + e.idx) if e.lleva else str(e.idx))
            elif p == m.almacen:
                fila += 'D'
            elif p in m.estaciones:
                fila += 'o'
            elif p in col.recursos:
                fila += '*'
            else:
                fila += ' '
        filas.append(fila)
    s = col.stats
    bat = '  '.join('%d:%4.1f%s' % (e.idx, e.bateria, '+' if e.lleva else ' ') for e in col.estados)
    filas.append('turno %d  entregados %d  caducados %d  agotados %d  mensajes %d' %
                 (col.turno, s['entregados'], s['caducados'], s['agotados'], col.canal.entregas))
    filas.append('batería  ' + bat)
    return '\n'.join(filas)


def oyenteLog(col_ref):
    """Devuelve una función que imprime cada mensaje enviado de forma legible."""
    def oyente(m, receptores, patron):
        t = col_ref[0].turno if col_ref[0] else 0
        dest = ','.join(str(r) for r in receptores) or '(nadie)'
        tema = ' [%s]' % m.tema if m.tema else ''
        print('[t%3d] %-4s %-15s %-17s%s -> %s  %s' % (t, m.emisor, m.performativa, patron, tema, dest, m.contenido))
    return oyente


def imprimirResumen(estrategia, r):
    print('\n=== Estrategia: %s ===' % estrategia)
    print('Suministros entregados : %d  (de %d aparecidos, %d caducados)' % (r['entregados'], r['aparecidos'], r['caducados']))
    print('Agentes agotados       : %d   (vivos al final: %d)' % (r['agotados'], r['vivos']))
    print('Viajes en vano         : %d   (el suministro ya no estaba)' % r['objetivosFallidos'])
    print('Turnos de espera en estaciones: %d   turnos de carga: %d' % (r['turnosEspera'], r['turnosCarga']))
    print('Mensajes: %d transmisiones, %d entregas, %d perdidos' % (r['transmisiones'], r['entregasMensajes'], r['mensajesPerdidos']))
    if r['porPerformativa']:
        print('  por performativa:', r['porPerformativa'])
        print('  por patrón      :', r['porPatron'])


def main(argv=None):
    ap = argparse.ArgumentParser(description='Ejercicio 2: colonia cooperativa con recursos escasos')
    ap.add_argument('-e', '--estrategia', default='pubsub', choices=list(ESTRATEGIAS))
    ap.add_argument('-s', '--semilla', type=int, default=1)
    ap.add_argument('-l', '--layout', default='colonia')
    ap.add_argument('-n', '--agentes', type=int, default=6)
    ap.add_argument('-t', '--turnos', type=int, default=500)
    ap.add_argument('--perdida', type=float, default=0.0, help='probabilidad de perder cada mensaje')
    ap.add_argument('--aparicion', type=float, default=0.25, help='probabilidad de que aparezca un suministro por turno')
    ap.add_argument('-v', '--ver', action='store_true', help='dibuja el mapa en la consola cada turno')
    ap.add_argument('--pausa', type=float, default=0.05)
    ap.add_argument('--log', action='store_true', help='imprime todos los mensajes')
    ap.add_argument('--gif', default=None, help='guarda una animación de la partida')
    a = ap.parse_args(argv)

    ref = [None]
    col = crearColonia(a.estrategia, a.semilla, a.layout, oyente=oyenteLog(ref) if a.log else None,
                       turnos=a.turnos, numAgentes=a.agentes, perdida=a.perdida, probAparicion=a.aparicion)
    ref[0] = col
    fotos = []

    def alTurno(c):
        if a.ver:
            print('\033[2J\033[H' + dibujar(c))
            time.sleep(a.pausa)
        if a.gif:
            fotos.append(capturar(c))

    from visual import capturar, guardarGif   # noqa: E402  (solo necesita matplotlib si se usa --gif)
    if a.gif:
        fotos.append(capturar(col))
    r = col.jugar(alTurno)
    if a.ver:
        print(dibujar(col))
    imprimirResumen(a.estrategia, r)
    if a.gif:
        guardarGif(col, fotos, a.gif)
        print('Animación guardada en', a.gif)
    return r


if __name__ == '__main__':
    main()
