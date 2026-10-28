# Ejercicio 2 – Colonia en escasez (comunicación entre agentes, sin LLMs, opción 2)

## Problema
Se reutiliza el entorno de Berkeley del ejercicio 1 (laberinto, `layout.py`, `distanceCalculator.py`, `game.py`),
pero ya no hay dos equipos enfrentados: **6 recolectores forman una única colonia** que coopera.

* Aparecen **suministros** en sitios aleatorios y caducan (30–50 turnos). Hay pocos.
* Cada agente **solo ve a distancia ≤ 5** (observabilidad parcial).
* Llevar un suministro al **almacén (D)** suma +1 a la colonia.
* Moverse gasta 1 de batería, esperar 0,25. Con batería 0 el agente queda **agotado** para siempre.
* Solo hay **2 estaciones de carga** y cada una carga **a un agente a la vez** (recurso escaso).
* La batería de cada agente es **información privada**: nadie la conoce si no se comunica.

Objetivo colectivo: maximizar los suministros entregados en 500 turnos sin perder agentes.
El reto es de **comunicación**: qué decir, a quién y cuándo, con el menor número de mensajes.

## Agentes
* `AgenteRecolector` (6): explora, recoge, entrega y recarga.
* `AgenteEstacion` (2, fijos): gestiona la cola de su estación y responde peticiones.

## Comunicación (`mensajes.py`)
Mensajes con estructura **FIPA-ACL** (performativa, emisor, receptor, tema, contenido, conversación, en-respuesta-a).
Canal con **punto a punto, broadcast, multicast y publicar-suscribir** (con mensajes retenidos, como MQTT),
latencia de 1 turno y **pérdida de mensajes configurable**.

| Protocolo | Patrón | Performativas |
|---|---|---|
| P1 Avistamientos | publicar-suscribir, tema `recursos` (solo suscritos los agentes libres) | INFORM |
| P2 Reparto de suministros | publicar-suscribir + punto a punto | PROPOSE, REJECT_PROPOSAL, CANCEL |
| P3 Reserva de estaciones | multicast + petición-respuesta, reintentos si se pierde la respuesta | QUERY_REF, INFORM, REQUEST, AGREE, REFUSE, CANCEL |
| P4 Exploración | publicar-suscribir, tema `exploracion` | INFORM |

Con reservas, la estación arbitra por **urgencia** (menor batería estimada primero, con la batería que le comunicó el agente),
y rechaza recargas no urgentes si hay cola. Sin comunicación, atiende por orden de llegada.

## Estrategias comparadas
`sin_com`, `broadcast` (cada agente repite a todos lo que ve en cada turno), `pubsub_sin_reclamos`,
`pubsub_sin_reservas` y `pubsub` (propuesta completa).

## Cómo ejecutar (desde `practica2/`)
```
python3 ejercicio2/colonia.py                         # una partida, estrategia pubsub
python3 ejercicio2/colonia.py -e sin_com -s 4         # otra estrategia / semilla
python3 ejercicio2/colonia.py -v --pausa 0.1          # ver el mapa en la consola
python3 ejercicio2/colonia.py --log -t 60             # ver todos los mensajes
python3 ejercicio2/colonia.py --gif partida.gif -t 150   # animación (necesita matplotlib)
python3 ejercicio2/colonia.py --perdida 0.3           # 30 % de mensajes perdidos
python3 ejercicio2/experimentos.py --semillas 30      # todos los experimentos (~1 min) -> resultados/
```
Requisitos: Python 3; `matplotlib` solo para gráficas y GIF.

## Resultados (30 semillas, 500 turnos)
| Estrategia | Entregados | Espera en estaciones | Viajes en vano | Mensajes |
|---|---|---|---|---|
| Sin comunicación | 41,5 | 140 | 4,2 | 0 |
| Broadcast | 44,8 | 155 | 1,3 | 9 511 |
| Pub/sub completo | 44,3 | 87 | 0,8 | 2 011 |

* Comunicar sube los entregados un 7–9 % (diferencia emparejada significativa).
* Pub/sub logra lo mismo que broadcast con **~79 % menos mensajes**, y el coste crece mucho menos con el nº de agentes.
* Los reclamos reducen los viajes en vano (2,0 → 0,8). Las reservas reducen la espera un 22 % (112 → 87).
* Con poca energía (carga 3,5), las reservas evitan agotamientos: 1,1 → 0 agentes perdidos.
* Limitación: pub/sub no repite mensajes, así que es **menos robusto a pérdidas** que broadcast
  (30 % de pérdida: 44,3 → 39,5); broadcast es robusto gracias a su redundancia, pero muy caro.
