"""Este script tiene como objetivo representar cómo crece el tiempo en función del tamaño de N
Esperamos que el tiempo tenga un crecimiento polinómico, ya que aunque el número de variables crezca como O(n^2), DPLL
resuelve cada consulta explorando un arbol de busqueda practicamente sin ramificar, ya que el Wumpus genera cláusulas Horn

El siguiente codigo fue generado por chatgpt"""

import time
import matplotlib.pyplot as plt

from GeneracionNormas import generate_rules, id_var
from DPLL_new import dpll


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def build_knowledge(N, base_facts):
    """
    Construye la base de conocimiento (KB) para un tablero de tamaño N
    combinando las reglas generadas con una lista de hechos observados.
    """
    kb = generate_rules(N)
    for fact in base_facts:
        kb.append([fact])
    return kb


def entails(knowledge, proposition):
    """
    Comprueba si KB |= proposition usando DPLL por refutación.
    Devuelve True si la proposición está implicada.
    """
    test = knowledge.copy()
    test.append([-proposition])
    return not dpll(test)


# ============================================================
# EXPERIMENTO
# ============================================================

def run_benchmark(sizes, repetitions=3):
    """
    Para cada tamaño N mide:
      - Tiempo de generar las reglas
      - Tiempo de una consulta de entailment representativa

    Devuelve dos listas (tiempos de reglas, tiempos de consulta).
    """
    times_rules = []
    times_query = []

    for N in sizes:
        print(f"\n=== Probando N = {N} ===")

        # -------- 1. Medir tiempo de generación de reglas --------
        t0 = time.perf_counter()
        for _ in range(repetitions):
            generate_rules(N)
        t_rules = (time.perf_counter() - t0) / repetitions
        times_rules.append(t_rules)
        print(f"  Tiempo medio generación reglas: {t_rules:.4f} s")

        # -------- 2. Medir tiempo de una consulta de entailment --------
        # Simulamos un agente que está en (1,1) y ha percibido:
        #   - Sin Breeze en (1,1)
        #   - Sin Reek en (1,1)
        #   - Sin Bright en (1,1)
        # y quiere saber si (2,1) y (1,2) son seguras.
        base_facts = [
            -id_var('Breeze', 1, 1),
            -id_var('Reek',   1, 1),
            -id_var('Bright', 1, 1),
        ]

        knowledge = build_knowledge(N, base_facts)

        # Consultamos si en (2,1) NO hay pozo (consulta típica del agente)
        target_x, target_y = 2, 1
        well_var = id_var('Well', target_x, target_y)

        t0 = time.perf_counter()
        for _ in range(repetitions):
            entails(knowledge, -well_var)
        t_query = (time.perf_counter() - t0) / repetitions
        times_query.append(t_query)
        print(f"  Tiempo medio consulta entails(-Well({target_x},{target_y})): {t_query:.4f} s")

    return times_rules, times_query


# ============================================================
# GRÁFICA
# ============================================================

def plot_results(sizes, times_rules, times_query):
    """
    Representa en una gráfica los tiempos medidos frente a N.
    Usa escala logarítmica en Y para apreciar mejor el crecimiento.
    """
    plt.figure(figsize=(10, 6))

    plt.plot(sizes, times_rules, marker='o', label='Generación de reglas')
    plt.plot(sizes, times_query, marker='s', label='Consulta entails (DPLL)')

    plt.xlabel('Tamaño del tablero N')
    plt.ylabel('Tiempo (segundos)')
    plt.title('Crecimiento del tiempo del SAT-Solver con el tamaño N')
    plt.yscale('log')          # escala logarítmica para ver el crecimiento exponencial
    plt.grid(True, which='both', linestyle='--', alpha=0.7)
    plt.legend()
    plt.tight_layout()

    plt.savefig('benchmark_wumpus.png', dpi=150)
    plt.show()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    sizes = [2, 3, 4, 5, 6]

    print("Iniciando benchmark del SAT-Solver...")
    times_rules, times_query = run_benchmark(sizes, repetitions=3)

    print("\n================ RESULTADOS ================")
    print(f"{'N':>4} | {'Reglas (s)':>15} | {'Consulta (s)':>15}")
    print("-" * 40)
    for N, tr, tq in zip(sizes, times_rules, times_query):
        print(f"{N:>4} | {tr:>15.6f} | {tq:>15.6f}")

    plot_results(sizes, times_rules, times_query)