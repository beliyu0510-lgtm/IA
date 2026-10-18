"""Experimentación del planificador BFS (ejercicio 2).

Mide el tiempo computacional de bfs() sobre tableros aleatorios variando
el tamaño del tablero y la probabilidad de obstáculo.

Genera:
    resultados_bfs.csv   -> una fila por tablero
    resultados_bfs.png   -> gráfica del tiempo medio según el tamaño
y muestra por consola la tabla de tiempos por configuración.
"""

import csv
import random
import statistics

import matplotlib
matplotlib.use("Agg")  #solo guarda el PNG
import matplotlib.pyplot as plt

from GenerarTableroRobot import generate_table
from PlanRobot import RobotWorld, initial_state, bfs

# parametros del experimento
TAMANOS = [4, 6, 8, 10, 12, 14, 16]     # tamaño del tablero (N x N)
PROBABILIDADES_OBSTACULO = [0.0, 0.25, 0.5]
TABLEROS_POR_CONFIGURACION = 50         # tableros distintos por cada (tamaño, probabilidad)
EJECUCIONES_POR_TABLERO = 3             # se ejecuta BFS 3 veces y se toma el tiempo mínimo
SEMILLA_INICIAL = 2026                  # para que el experimento sea reproducible

ARCHIVO_CSV = "resultados_bfs.csv"
ARCHIVO_GRAFICA = "resultados_bfs.png"


def medir_tablero(tamano, probabilidad, semilla):
    """Genera un tablero, lo resuelve con BFS y devuelve el tiempo en milisegundos."""
    random.seed(semilla)
    table, _, _, pos_meta, _ = generate_table(N=tamano, prob_obstacle=probabilidad)

    world = RobotWorld(table, N=tamano, finish_line=pos_meta)
    s0 = initial_state(world)

    #El tiempo de una sola ejecución tiene ruido (sistema operativo, etc.).
    #BFS es determinista, así que repetimos y nos quedamos con el mínimo.
    tiempos = []
    for _ in range(EJECUCIONES_POR_TABLERO):
        plan, stats = bfs(world, s0)
        tiempos.append(stats["tiempo"])

    assert plan is not None, "El generador garantiza que existe solución"
    return min(tiempos) * 1000


def ejecutar_experimento():
    """Devuelve una lista de filas: una por cada tablero medido."""
    resultados = []
    semilla = SEMILLA_INICIAL
    for tamano in TAMANOS:
        for probabilidad in PROBABILIDADES_OBSTACULO:
            for _ in range(TABLEROS_POR_CONFIGURACION):
                resultados.append({
                    "tamano": tamano,
                    "probabilidad_obstaculo": probabilidad,
                    "semilla": semilla,
                    "tiempo_ms": medir_tablero(tamano, probabilidad, semilla),
                })
                semilla += 1
            print(f"  hecho: tamaño {tamano}, probabilidad de obstáculo {probabilidad}")
    return resultados


def guardar_csv(resultados):
    with open(ARCHIVO_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=resultados[0].keys())
        writer.writeheader()
        writer.writerows(resultados)


def calcular_resumen(resultados):
    """Tiempo medio, desviación típica y máximo por configuración."""
    resumen = []
    for tamano in TAMANOS:
        for probabilidad in PROBABILIDADES_OBSTACULO:
            tiempos = [r["tiempo_ms"] for r in resultados
                       if r["tamano"] == tamano
                       and r["probabilidad_obstaculo"] == probabilidad]
            resumen.append({
                "tamano": tamano,
                "probabilidad_obstaculo": probabilidad,
                "tiempo_medio": statistics.mean(tiempos),
                "desviacion_tipica": statistics.stdev(tiempos),
                "tiempo_maximo": max(tiempos),
            })
    return resumen


def imprimir_resumen(resumen):
    cabecera = (f"{'Tamaño':>6}  {'Prob. obstáculo':>15}  {'Tiempo medio (ms)':>17}  "
                f"{'Desviación típica (ms)':>22}  {'Tiempo máximo (ms)':>18}")
    print("\n" + cabecera)
    print("-" * len(cabecera))
    for fila in resumen:
        print(f"{fila['tamano']:>6}  {fila['probabilidad_obstaculo']:>15}  "
              f"{fila['tiempo_medio']:>17.2f}  {fila['desviacion_tipica']:>22.2f}  "
              f"{fila['tiempo_maximo']:>18.2f}")


def guardar_grafica(resumen):
    fig, ax = plt.subplots(figsize=(7, 5))
    for probabilidad in PROBABILIDADES_OBSTACULO:
        filas = [f for f in resumen if f["probabilidad_obstaculo"] == probabilidad]
        ax.plot([f["tamano"] for f in filas], [f["tiempo_medio"] for f in filas],
                marker="o", label=f"Probabilidad de obstáculo = {probabilidad}")
    ax.set_yscale("log")
    ax.set_xlabel("Tamaño del tablero (N)")
    ax.set_ylabel("Tiempo medio (ms, escala logarítmica)")
    ax.set_title("Tiempo de BFS según el tamaño del tablero")
    ax.legend()
    ax.grid(True, which="both", alpha=0.3)
    fig.tight_layout()
    fig.savefig(ARCHIVO_GRAFICA, dpi=150)


def main():
    print("Ejecutando experimentos...")
    resultados = ejecutar_experimento()
    guardar_csv(resultados)
    resumen = calcular_resumen(resultados)
    imprimir_resumen(resumen)
    guardar_grafica(resumen)
    print(f"\nGuardado: {ARCHIVO_CSV}, {ARCHIVO_GRAFICA}")


if __name__ == "__main__":
    main()
