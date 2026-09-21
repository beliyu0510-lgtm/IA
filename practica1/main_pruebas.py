import pygame
import sys
from GeneracionTablero import generate_table
from RenderizadoTabla import VisualizadorWumpus

def main():
    # CONFIGURACIÓN DEL MAPA
    N = 4             # Tamaño del tablero (4x4)
    PROB_POZO = 0.2   # 20% probabilidad de pozos

    # 1. Generar el entorno aleatorio
    tablero = generate_table(N=N, prob_well=PROB_POZO)

    # 2. Crear ventana de Pygame
    renderizador = VisualizadorWumpus(N=N, tamaño_celda=120)

    print("=== VISOR DEL MUNDO DEL WUMPUS ===")
    print("Controles:")
    print(" - Presiona [ESPACIO] o [R] para regenerar un tablero nuevo.")
    print(" - Cierra la ventana para salir.")

    # Bucle de la aplicación
    ejecutando = True
    mantiene_redibujado = True

    while ejecutando:
        if mantiene_redibujado:
            renderizador.renderizar(tablero, pos_agente=(1, 1))
            mantiene_redibujado = False

        for evento in pygame.event.get():
            # Evento: Cerrar la ventana
            if evento.type == pygame.QUIT:
                ejecutando = False

            # Evento: Teclas presionales
            elif evento.type == pygame.KEYDOWN:
                # Tecla ESPACIO o R: Generar un mapa totalmente nuevo
                if evento.key == pygame.K_SPACE or evento.key == pygame.K_r:
                    print("Generando nuevo tablero...")
                    tablero = generate_table(N=N, prob_well=PROB_POZO)
                    mantiene_redibujado = True

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()