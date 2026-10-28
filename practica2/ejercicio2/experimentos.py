"""
experimentos.py - Validación del ejercicio 2.

Experimento A: comparación de estrategias de comunicación (misma semilla = mismo mundo).
Experimento B: robustez frente a pérdida de mensajes (0 %, 10 %, 30 %, 50 %).
Experimento C: escasez de energía (velocidad de carga de las estaciones).
Experimento D: escalabilidad (número de agentes) -> coste de comunicación.

Uso (desde practica2/):
  python3 ejercicio2/experimentos.py                  -> 30 semillas, todo
  python3 ejercicio2/experimentos.py --semillas 10    -> más rápido
Resultados: ejercicio2/resultados/*.csv y *.png
"""
import argparse
import csv
import os
import statistics
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

from colonia import crearColonia                 # noqa: E402
from entornoColonia import Mapa, cargarLayout    # noqa: E402

ESTRATEGIAS = ['sin_com', 'broadcast', 'pubsub_sin_reclamos', 'pubsub_sin_reservas', 'pubsub']
METRICAS = ['entregados', 'caducados', 'agotados', 'objetivosFallidos', 'turnosEspera', 'entregasMensajes',
            'transmisiones', 'mensajesPerdidos']


def correr(estrategia, semilla, mapa, **params):
    r = crearColonia(estrategia, semilla, mapa=mapa, **params).jugar()
    fila = {'estrategia': estrategia, 'semilla': semilla}
    fila.update(params)
    fila.update({k: r[k] for k in METRICAS})
    fila['entregadosPor100Msg'] = 100.0 * r['entregados'] / r['entregasMensajes'] if r['entregasMensajes'] else ''
    return fila


def media(filas, clave):
    vals = [f[clave] for f in filas if f[clave] != '']
    if not vals:
        return float('nan'), 0.0
    return statistics.mean(vals), (statistics.stdev(vals) if len(vals) > 1 else 0.0)


def guardarCsv(filas, ruta):
    claves = list(filas[0].keys())
    for f in filas:
        for k in f:
            if k not in claves:
                claves.append(k)
    with open(ruta, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=claves)
        w.writeheader()
        w.writerows(filas)


def tabla(filas, grupo, metricas):
    grupos = []
    for f in filas:
        if f[grupo] not in grupos:
            grupos.append(f[grupo])
    print('%-22s' % grupo + ''.join('%22s' % m for m in metricas))
    for g in grupos:
        sub = [f for f in filas if f[grupo] == g]
        print('%-22s' % g + ''.join('%14.1f ± %5.1f' % media(sub, m) for m in metricas))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--semillas', type=int, default=30)
    ap.add_argument('--turnos', type=int, default=500)
    ap.add_argument('--sin-graficas', action='store_true')
    a = ap.parse_args()
    salida = os.path.join(AQUI, 'resultados')
    os.makedirs(salida, exist_ok=True)
    mapa = Mapa(cargarLayout('colonia'))
    semillas = range(a.semillas)
    t0 = time.time()

    # ---------------- A: estrategias
    filasA = [correr(e, s, mapa, turnos=a.turnos) for e in ESTRATEGIAS for s in semillas]
    guardarCsv(filasA, os.path.join(salida, 'A_estrategias.csv'))
    print('\n[A] Estrategias de comunicación (%d semillas, media ± desv.)' % a.semillas)
    tabla(filasA, 'estrategia', ['entregados', 'caducados', 'agotados', 'turnosEspera', 'entregasMensajes'])
    tabla(filasA, 'estrategia', ['objetivosFallidos', 'entregadosPor100Msg'])
    print('\n  Diferencia emparejada en entregados respecto a sin_com (mismas semillas, IC 95 %):')
    base = {f['semilla']: f['entregados'] for f in filasA if f['estrategia'] == 'sin_com'}
    for e in ESTRATEGIAS[1:]:
        dif = [f['entregados'] - base[f['semilla']] for f in filasA if f['estrategia'] == e]
        m = statistics.mean(dif)
        ic = 1.96 * statistics.stdev(dif) / len(dif) ** 0.5 if len(dif) > 1 else 0
        print('  %-22s %+5.1f  [%+5.1f, %+5.1f]  (%+.0f %%)' % (e, m, m - ic, m + ic, 100 * m / statistics.mean(base.values())))

    # ---------------- B: pérdida de mensajes
    perdidas = [0.0, 0.1, 0.3, 0.5]
    filasB = [correr(e, s, mapa, turnos=a.turnos, perdida=p)
              for e in ['broadcast', 'pubsub'] for p in perdidas for s in semillas]
    guardarCsv(filasB, os.path.join(salida, 'B_perdidas.csv'))
    print('\n[B] Robustez ante pérdida de mensajes')
    for e in ['broadcast', 'pubsub']:
        print(' ', e)
        tabla([f for f in filasB if f['estrategia'] == e], 'perdida', ['entregados', 'agotados', 'turnosEspera'])

    # ---------------- C: escasez de energía
    velocidades = [5.0, 3.5, 2.5]
    filasC = [correr(e, s, mapa, turnos=a.turnos, velocidadCarga=v)
              for e in ESTRATEGIAS for v in velocidades for s in semillas]
    guardarCsv(filasC, os.path.join(salida, 'C_energia.csv'))
    print('\n[C] Escasez de energía (velocidad de carga de las estaciones)')
    for e in ESTRATEGIAS:
        print(' ', e)
        tabla([f for f in filasC if f['estrategia'] == e], 'velocidadCarga', ['entregados', 'agotados', 'turnosEspera'])

    # ---------------- D: escalabilidad
    numeros = [2, 4, 6]
    filasD = [correr(e, s, mapa, turnos=a.turnos, numAgentes=n)
              for e in ['sin_com', 'broadcast', 'pubsub'] for n in numeros for s in semillas]
    guardarCsv(filasD, os.path.join(salida, 'D_escalabilidad.csv'))
    print('\n[D] Escalabilidad (número de agentes)')
    for e in ['sin_com', 'broadcast', 'pubsub']:
        print(' ', e)
        tabla([f for f in filasD if f['estrategia'] == e], 'numAgentes', ['entregados', 'entregasMensajes'])

    print('\nTiempo total: %.1f s' % (time.time() - t0))
    if not a.sin_graficas:
        graficas(filasA, filasB, filasC, filasD, ESTRATEGIAS, perdidas, velocidades, numeros, salida)
        print('Gráficas en', salida)


def graficas(filasA, filasB, filasC, filasD, estrategias, perdidas, velocidades, numeros, salida):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    etiquetas = {'sin_com': 'Sin\ncomunicación', 'broadcast': 'Broadcast\ningenuo',
                 'pubsub_sin_reclamos': 'Pub/sub\nsin reclamos', 'pubsub_sin_reservas': 'Pub/sub\nsin reservas',
                 'pubsub': 'Pub/sub\ncompleto'}
    colores = ['#9e9e9e', '#e07a5f', '#81b29a', '#f2cc8f', '#3d405b']

    # A: entregados y mensajes
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.2))
    for ax, met, tit in zip(axs, ['entregados', 'turnosEspera', 'entregasMensajes'],
                            ['Suministros entregados', 'Turnos de espera en estaciones', 'Mensajes entregados']):
        ms = [media([f for f in filasA if f['estrategia'] == e], met) for e in estrategias]
        ax.bar(range(len(estrategias)), [m for m, _ in ms], yerr=[s for _, s in ms], color=colores, capsize=4)
        ax.set_xticks(range(len(estrategias)))
        ax.set_xticklabels([etiquetas[e] for e in estrategias], fontsize=8)
        ax.set_title(tit)
        ax.spines[['top', 'right']].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(salida, 'A_estrategias.png'), dpi=150)
    plt.close(fig)

    # B: pérdida
    fig, axs = plt.subplots(1, 2, figsize=(10, 4))
    for e, c in [('broadcast', colores[1]), ('pubsub', colores[4])]:
        for ax, met in zip(axs, ['entregados', 'turnosEspera']):
            ms = [media([f for f in filasB if f['estrategia'] == e and f['perdida'] == p], met) for p in perdidas]
            ax.errorbar([100 * p for p in perdidas], [m for m, _ in ms], yerr=[s for _, s in ms],
                        marker='o', capsize=3, color=c, label=etiquetas[e].replace('\n', ' '))
    base = media([f for f in filasA if f['estrategia'] == 'sin_com'], 'entregados')[0]
    axs[0].axhline(base, ls='--', color=colores[0], label='Sin comunicación')
    axs[0].set_title('Entregados vs. pérdida de mensajes')
    axs[1].set_title('Espera en estaciones vs. pérdida')
    for ax in axs:
        ax.set_xlabel('% de mensajes perdidos')
        ax.legend(fontsize=8)
        ax.spines[['top', 'right']].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(salida, 'B_perdidas.png'), dpi=150)
    plt.close(fig)

    # C: escasez de energía
    fig, axs = plt.subplots(1, 2, figsize=(11, 4))
    for e, c in zip(estrategias, colores):
        for ax, met in zip(axs, ['entregados', 'agotados']):
            ms = [media([f for f in filasC if f['estrategia'] == e and f['velocidadCarga'] == v], met)[0]
                  for v in velocidades]
            ax.plot(velocidades, ms, marker='o', color=c, label=etiquetas[e].replace('\n', ' '))
    axs[0].set_title('Entregados según la energía disponible')
    axs[1].set_title('Agentes agotados (de 6)')
    for ax in axs:
        ax.set_xlabel('Velocidad de carga (batería/turno)  →  más energía')
        ax.legend(fontsize=8)
        ax.spines[['top', 'right']].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(salida, 'C_energia.png'), dpi=150)
    plt.close(fig)

    # D: escalabilidad
    fig, axs = plt.subplots(1, 2, figsize=(10, 4))
    for e in ['sin_com', 'broadcast', 'pubsub']:
        c = colores[estrategias.index(e)]
        for ax, met in zip(axs, ['entregados', 'entregasMensajes']):
            ms = [media([f for f in filasD if f['estrategia'] == e and f['numAgentes'] == n], met)[0] for n in numeros]
            ax.plot(numeros, ms, marker='o', color=c, label=etiquetas[e].replace('\n', ' '))
    axs[0].set_title('Entregados según nº de agentes')
    axs[1].set_title('Mensajes entregados según nº de agentes')
    for ax in axs:
        ax.set_xlabel('Número de recolectores')
        ax.set_xticks(numeros)
        ax.legend(fontsize=8)
        ax.spines[['top', 'right']].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(salida, 'D_escalabilidad.png'), dpi=150)
    plt.close(fig)


if __name__ == '__main__':
    main()
