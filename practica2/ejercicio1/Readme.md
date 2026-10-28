"""Esquema mental de lo que debemos hacer:
- Cuadro general de la práctica: Queremos hacer un multiagente clásico de dos equuipos de 3 agentes en un juego de captura de la bandera con fase pacman/fantasma, donde
el problema central es resolver los conflictos dentro de un equipo. Quién ataca, quién defiende y quién se mueve por dónde se decide en cada momento y por negociación, no con roles fijados de antemano
- Se hará uso del algoritmo será ContractNetProtocol
- Formalización del problema:
    - 3 agentes por equipo, autónomos, con vista local del tablero y comunicación solo dentro de su equipo
    - Objetivo común del equipo: capturar la bandera del rival y llevarla a casa, sin perder la propia
    - Objetivos individuales: un atacante quiere seguir hacia la bandera, un defensor quiere perseguir a un intruso, y los dos al vez no cabben
    - Conflictos (con la tipología de la clase)
- Conflictos:
    - Quién ataca y quién defiende cada zona --> ContractNet (negociación)
    - Dos agentes quieren la misma casilla o pasillo --> arbitraje por prioridad
    - Cada agente cree que el rival está en un sitio distinto --> consenso por broadcast
    - El atacante quiere huir, el equipo necesita que cubra --> arbitraje por reglas

2. Arquitectura (híbrida)
Capa de equipo, descentralizada: los roles se negocian por subasta. No hay un jefe fijo, y el “gerente” de cada ronda rota (por ejemplo, el agente que detecta el evento).
Capa individual, local: cada agente planifica su movimiento por sí mismo con A* o BFS, evitando casillas peligrosas.
Así cuentas con las ventajas de las diapositivas: sin punto único de fallo, y con un reparto razonablemente bueno.   

3. Mecanismo central: Contract Net
    1. Disparadores: se abre una ronda cuando ocurre algo (se ve un intruso, cae la bandera, un agente es eliminado o reaparece) o cada K turnos.
    2. Tareas anunciadas: atacar la bandera, defender la entrada A, defender la entrada B, perseguir al intruso visible.
    3. Pujas: cada agente calcula una puja por tarea, algo como puja(i, t) = a·(cercanía al objetivo) − b·(riesgo) − c·(coste de cambiar de rol). El término de cambio de rol evita que los roles oscilen.
    4. Adjudicación: con solo 3 agentes y 3-4 tareas, el gerente resuelve una asignación óptima (o una voraz) y adjudica.
    5. Aceptación: los agentes confirman y ejecutan, y se mide cuántos mensajes costó.
    
4. Resolución de los otros conflictos
Colisiones: se detectan comparando los planes de los agentes y se arbitran con una regla fija (el portador de la bandera tiene prioridad, luego el que persigue, y el desempate es por índice).
Creencias: cada agente difunde lo que ve (posición, momento de la observación) y los demás lo fusionan quedándose con lo más reciente.

5. Evaluación (lo que da la nota de “validar y justificar”)
Comparativas:
    Aleatorio
    Roles fijos 1+2 sin comunicación
    Asignación centralizada con un gerente fijo
    Tu CNP descentralizado
"""

"""Cambios en el entorno: Berkeley
    1. capture.py (1032 líneas) =>	Es donde más cambia. Hay que pasar de 2 a 3 agentes por equipo en loadAgents (índices 0,2,4 y 1,3,5), sustituir la lógica de comida por 
    bandera (consume(), condiciones de fin y victoria en torno a las líneas 396-408 y 488-508, getProgress) y ajustar agentCrash, que usa % 2.

    2. layout.py =>	En processLayoutChar (línea 128) solo se aceptan los dígitos 1-4. Hay que añadir 5 y 6 y un carácter para la bandera.

    3. layouts/*.lay =>	Cada mapa necesita 6 posiciones de inicio y la bandera de cada equipo. Empieza con uno solo (por ejemplo tinyCapture o defaultCapture) y no toques los demás.

    4. captureGraphicsDisplay.py =>	Dibujar la bandera. Los colores van por index % 2, así que los 6 agentes ya salen bien.

    5. captureAgents.py => Añadir el buzón de mensajes (broadcast y punto a punto) a CaptureAgent, con contador de mensajes para medir el coste de comunicación.

    6. myTeam.py =>	Aquí van tus agentes con CNP. Hay que cambiar createTeam para que reciba 3 índices en vez de 2.

    7. baselineTeam.py => Cambia createTeam igual (3 agentes) y úsalo como rival de comparación.
"""