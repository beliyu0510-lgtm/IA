import gymnasium as gym
import RenderizadoTabla
from Agent import Agent


def main():

    # ==========================================
    # CREAR EL ENTORNO
    # ==========================================

    env = gym.make(
        "WumpusWorld-v0",
        N=3,
        prob_well=0.3,
        disable_env_checker=True
    )

    # ==========================================
    # GENERAR EL TABLERO
    # ==========================================

    observation, info = env.reset()

    # observation es directamente el diccionario
    # del tablero generado por GeneracionTablero.py
    table = observation

    # ==========================================
    # CREAR EL AGENTE
    # ==========================================

    agent = Agent(N=4)

    # El agente empieza en la misma posición
    # que ha generado el entorno
    agent.position = env.unwrapped.agent_position

    print("==============================")
    print("INICIO DEL JUEGO")
    print("==============================")
    print(f"El agente empieza en: {agent.position}")

    # ==========================================
    # MOSTRAR TABLERO INICIAL
    # ==========================================

    env.unwrapped.agent_position = agent.position
    env.render()

    # ==========================================
    # BUCLE PRINCIPAL
    # ==========================================

    while True:

        # --------------------------------------
        # 1. ESTADO DE LA CASILLA ACTUAL
        # --------------------------------------

        state = table[agent.position]

        # --------------------------------------
        # 2. EL AGENTE PERCIBE
        # --------------------------------------

        agent.perceive(state)

        print("\n==============================")
        print("ESTADO DEL AGENTE")
        print("==============================")

        print(f"Posición: {agent.position}")

        print("Percepción:")
        print(f"  Breeze: {state['Breeze']}")
        print(f"  Reek:   {state['Reek']}")
        print(f"  Bright: {state['Bright']}")

        print(f"Visitadas: {agent.visited}")

        if hasattr(agent, "path"):
            print(f"Camino:   {agent.path}")

        # --------------------------------------
        # 3. ¿HA ENCONTRADO EL ORO?
        # --------------------------------------

        if state["Bright"]:

            print("\n==============================")
            print("¡ORO ENCONTRADO!")
            print("==============================")

            print(
                f"El agente ha encontrado el oro "
                f"en {agent.position}"
            )

            break

        # --------------------------------------
        # 4. EL AGENTE DECIDE MOVERSE
        # --------------------------------------

        moved = agent.move()

        if not moved:

            print("\n==============================")
            print("EL AGENTE NO PUEDE AVANZAR")
            print("==============================")

            print("No quedan movimientos posibles.")

            break

        # --------------------------------------
        # 5. ACTUALIZAR EL EMOJI DEL AGENTE
        # --------------------------------------

        env.unwrapped.agent_position = agent.position

        print(
            f"\n→ El agente se mueve a "
            f"{agent.position}"
        )

        # --------------------------------------
        # 6. COMPROBAR SI HA MUERTO
        # --------------------------------------

        new_state = table[agent.position]

        if new_state["Wumpus"]:

            print("\n==============================")
            print("💀 EL AGENTE HA MUERTO")
            print("==============================")

            print(
                f"Ha caído sobre el Wumpus "
                f"en {agent.position}"
            )

            # Mostrar al agente en la casilla
            # donde ha muerto
            env.render()

            break

        if new_state["Well"]:

            print("\n==============================")
            print("💀 EL AGENTE HA MUERTO")
            print("==============================")

            print(
                f"Ha caído en un pozo "
                f"en {agent.position}"
            )

            # Mostrar al agente en la casilla
            # donde ha muerto
            env.render()

            break

        # --------------------------------------
        # 7. ACTUALIZAR EL TABLERO
        # --------------------------------------

        env.render()

    # ==========================================
    # CERRAR EL ENTORNO
    # ==========================================

    input("\nPulsa ENTER para cerrar...")

    env.close()


if __name__ == "__main__":
    main()