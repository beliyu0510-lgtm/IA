import gymnasium as gym
import RenderizadoTabla


def main():

    env = gym.make(
        "WumpusWorld-v0",
        N=5,
        prob_well=0.3,
        disable_env_checker=True
    )

    observation, info = env.reset()

    print("Mapa generado:")
    print(observation)

    env.render()

    input("Pulsa ENTER para cerrar...")

    env.close()


if __name__ == "__main__":
    main()