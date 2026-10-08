from collections import deque
import time


def get_neighbors(x,y,N)-> list:
    """Get the valid neighbors

    Args:
        x (int): x coordinate
        y (int): y coordinate
        N (int): size of the table

    Returns:
        List of tuples with all the valid coordinates
    """
    neighbors = []
    for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
        nx, ny = x + dx, y + dy
        if 1 <= nx <= N and 1 <= ny <= N:
            neighbors.append((nx,ny))
    return neighbors

AGENTE = 'Agente'
CAJA = "C"
INICIO = (1,1)

class RobotWorld:
    def __init__(self, table, N, finish_line):
        self.N = N
        self.obstacles = {c for c,st in table.items() if st['Obstacle']}
        self.caja = next(c for c,st in table.items() if st['Box'])
        self.finish_line = finish_line

    def adyacent(self, a, b):
        """Mira si a y b son vecinos"""
        return b in get_neighbors(a[0], a[1], self.N)

    def neighbors(self, a):
        return get_neighbors(a[0], a[1], self.N)

#SITUACIONES Y FLUIDOS
def initial_state(world):
    """Construcción de la situación inicial S0"""
    return frozenset({ #Inmutable, esto es una realidad no cambiante
        ("En",AGENTE, INICIO),
        ("En", CAJA, world.caja),
    })

def position(objeto, s):
    """Busca en la situación s el fluente ('En', objeto, x) y devuelve x. Si no existe, devuelve None"""
    for f in s:
        if f[0] == 'En' and f[1] == objeto:
            return f[2]
    return None

# AXIOMAS DE POSIBILIDAD
def posible(mundo, a, s):
    x = position(AGENTE, s)
    if a[0] == 'Ir':
        _, origen, y = a
        if origen != x or not mundo.adyacent(x,y):
            return False
        if y in mundo.obstacles:
            return False
        return True

    if a[0] == 'Coger':
        return position(CAJA, s) == x and ('Sosteniendo', CAJA) not in s
    if a[0] == 'Soltar':
        return ('Sosteniendo', CAJA) in s
    return False

def acciones_posibles(mundo, s):
    x = position(AGENTE, s)
    candidatas = [('Ir',x,y) for y in mundo.neighbors(x)]
    candidatas += [('Coger', CAJA), ('Soltar', CAJA)]
    return [a for a in candidatas if posible(mundo, a, s)]

# AXIOMAS DE EFECTO
def efecto_pos(mundo, a, s):
    if a[0] == 'Ir':
        _,x,y = a
        # Mientras la caja está sostenida no tiene fluente En(C, ·):
        # su posición es implícitamente la del agente.
        return {('En', AGENTE, y)}

    if a[0] == "Coger":
        return {('Sosteniendo', CAJA)}

    if a[0] == 'Soltar':
        return {('En', CAJA, position(AGENTE, s))}
    return set()

def efecto_neg(mundo, a, s):
    if a[0] == 'Ir':
        _, x, y = a
        return {("En", AGENTE, x)}
    if a[0] == "Coger":
        # La caja deja de estar "en" su casilla al sostenerla
        return {("En", CAJA, position(CAJA, s))}
    if a[0] == "Soltar":
        return {("Sosteniendo", CAJA)}
    return set()

# AXIOMA ESTADO-SUCESOR
def resultado(mundo, a, s):
    if not posible(mundo, a, s):
        raise ValueError(f"Acción no posible: {nombre_accion(a)}")
    return frozenset((s - efecto_neg(mundo, a, s)) | efecto_pos(mundo, a, s))

# Proyección
def proyeccion(mundo, seq, s):
    if not seq:
        return s
    return proyeccion(mundo, seq[1:], resultado(mundo, seq[0], s))


def objetivo(mundo, s):
    return ("En", CAJA, mundo.finish_line) in s and ("Sosteniendo", CAJA) not in s

# BFS
def bfs(mundo, s0):
    """Búsqueda en anchura (BFS) sobre situaciones.

    Nodos = situaciones alcanzables desde S0.
    Aristas = acciones posibles (axioma de posibilidad).
    Transición = axioma estado-sucesor.

    Returns:
        plan (list | None): secuencia de acciones más corta, o None
        stats (dict): expandidos, generados, podados y tiempo
    """
    t0 = time.perf_counter()
    stats = {"expandidos": 0, "generados": 1, "podados": 0}

    if objetivo(mundo, s0):
        stats["tiempo"] = time.perf_counter() - t0
        return [], stats

    # Cola FIFO: garantiza optimalidad en nº de acciones
    frontera = deque([(s0, [])])
    visitadas = {s0}

    while frontera:
        s, plan = frontera.popleft()
        stats["expandidos"] += 1

        for a in acciones_posibles(mundo, s):
            s_sig = resultado(mundo, a, s)

            if s_sig in visitadas:
                stats["podados"] += 1
                continue

            stats["generados"] += 1
            plan_sig = plan + [a]

            if objetivo(mundo, s_sig):
                stats["tiempo"] = time.perf_counter() - t0
                return plan_sig, stats

            visitadas.add(s_sig)
            frontera.append((s_sig, plan_sig))

    stats["tiempo"] = time.perf_counter() - t0
    return None, stats

# Utilidades de impresión

def casilla(c):
    return f"[{c[0]},{c[1]}]"


def nombre_accion(a):
    if a[0] == "Ir":
        return f"Ir({casilla(a[1])}, {casilla(a[2])})"
    return f"{a[0]}({a[1]})"


def nombre_flujo(f):
    if f[0] == "En":
        return f"En({f[1]}, {casilla(f[2])})"
    if len(f) == 1:
        return f"{f[0]}"
    return f"{f[0]}({f[1]})"


def describir_situacion(s):
    return " ∧ ".join(sorted(nombre_flujo(f) for f in s))
