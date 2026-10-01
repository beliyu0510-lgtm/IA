import pygame

from RenderizarTablaRobot import RobotEnv

from PlanRobot import (
    RobotWorld,
    initial_state,
    bfs,
    resultado,
    position,
    objetivo,
    nombre_accion,
    AGENTE,
    CAJA,
)


def main():

    env = RobotEnv(
        N=4,
        prob_obstacle=0.5
    )

    table, _ = env.reset()
    env.render()

    # ------------------------------------------------------------------
    # PLANIFICACIÓN + EJECUCIÓN PASO A PASO
    # ------------------------------------------------------------------

    # Posiciones iniciales extraídas del tablero generado por el env
    pos_agente = env.agent_position
    pos_caja   = next(c for c, st in table.items() if st["Box"])
    pos_meta   = next(c for c, st in table.items() if st["Goal"])

    print("Agente:", pos_agente, "| Caja:", pos_caja, "| Meta:", pos_meta)

    # Mundo y situación inicial
    world = RobotWorld(table, N=env.N, finish_line=pos_meta)
    if not hasattr(world, "caja"):
        world.caja = world.box
    if not hasattr(world, "meta"):
        world.meta = world.finish_line

    s0 = initial_state(world)

    # Planificar con BFS
    plan, stats = bfs(world, s0)
    print("Stats BFS:", stats)

    if plan is None:
        print("No se encontró plan.")
    else:
        print(f"Plan de {len(plan)} acciones:")
        for i, a in enumerate(plan, 1):
            print(f"  {i:2d}. {nombre_accion(a)}")

        # Ejecutar el plan paso a paso, sincronizando el env
        s = s0
        for a in plan:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    env.close()
                    return

            # Aplicar la acción al estado lógico
            s = resultado(world, a, s)

            # Sincronizar el estado visual
            pos_agente = position(AGENTE, s)
            if pos_agente is not None:
                env.agent_position = pos_agente

            pos_caja = position(CAJA, s)
            for c, st in env.table.items():
                st["Box"] = False
            if pos_caja is not None:
                env.table[pos_caja]["Box"] = True

            env.render()

            print(f"{nombre_accion(a)}  ->  "
                  f"Agente: {position(AGENTE, s)}  "
                  f"Caja: {position(CAJA, s) if pos_caja is not None else '(sostenida)'}  "
                  f"Sosteniendo: {('Sosteniendo', CAJA) in s}")

            pygame.time.wait(400)

        print("¿Objetivo cumplido?:", objetivo(world, s))

    # ------------------------------------------------------------------
    # BUCLE DE EVENTOS ORIGINAL
    # ------------------------------------------------------------------

    running = True

    while running:

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False

    env.close()


if __name__ == "__main__":
    main()