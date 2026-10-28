"""
demo_pruebas.py - Juega N partidas sin ventana, guarda los resultados y los dibuja.

  python3 main_muchaspartidas.py                       -> myTeam (rojo) contra myTeam (azul), 20 partidas
  python3 main_muchaspartidas.py baselineTeam          -> myTeam (rojo) contra baselineTeam (azul)
  python3 main_muchaspartidas.py baselineTeam baselineTeam       -> baselineTeam(rojo) contra baselineTeam(azul)

Genera resultados_<rojo>_vs_<azul>.csv y resultados_<rojo>_vs_<azul>.png
"""
import sys, os, csv, io, contextlib, importlib, collections

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..'))

for nombre in ['util', 'game', 'layout', 'distanceCalculator', 'captureAgents', 'graphicsUtils',
               'textDisplay', 'keyboardAgents', 'captureGraphicsDisplay']:
    try:
        sys.modules[nombre] = importlib.import_module('entorno.' + nombre)
    except ImportError:
        pass
import entorno.capture as capture

MI_EQUIPO = 'myTeam'
LARGO = 1800                 # movimientos máximos por partida (-i)

def buscar(nombre):
    aqui = os.path.dirname(os.path.abspath(__file__))
    for carpeta in [os.getcwd(), aqui, os.path.join(aqui, 'entorno')]:
        ruta = os.path.join(carpeta, nombre + '.py')
        if os.path.exists(ruta):
            return ruta
    raise SystemExit('No encuentro %s.py' % nombre)

def buscarLayout(nombre='flagCapture'):
    aqui = os.path.dirname(os.path.abspath(__file__))
    for carpeta in [os.getcwd(), aqui, os.path.join(aqui, 'entorno')]:
        ruta = os.path.join(carpeta, 'layouts', nombre + '.lay')
        if os.path.exists(ruta):
            return ruta
    return 'flagCapture'

def jugar(rojo, azul, n):
    """Juega n partidas seguidas (sin ventana) y devuelve [(partida, ganador, movimientos)]."""
    args = capture.readCommand(['-r', buscar(rojo), '-b', buscar(azul), '-n', str(n), '-q',
                                '-l', buscarLayout(), '-i', str(LARGO)])
    with contextlib.redirect_stdout(io.StringIO()):          # capture.py imprime mucho
        juegos = capture.runGames(**args)
    filas = []
    for i, g in enumerate(juegos, 1):
        d = g.state.data
        ganador = 'rojo' if d.score > 0 else ('azul' if d.score < 0 else 'empate')
        filas.append((i, ganador, LARGO - d.timeleft))
    return filas

def guardar(filas, ruta):
    with open(ruta, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['partida', 'ganador', 'movimientos'])
        w.writerows(filas)

def dibujar(filas, titulo, ruta):
    import matplotlib
    import matplotlib.pyplot as plt
    colores = {'rojo': '#d62728', 'azul': '#1f77b4', 'empate': '#9e9e9e'}
    cuenta = collections.Counter(f[1] for f in filas)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.5), gridspec_kw={'width_ratios': [1, 2.4]})
    # 1) Cuántas ganó cada uno
    nombres = ['rojo', 'azul', 'empate']
    a1.bar(nombres, [cuenta[x] for x in nombres], color=[colores[x] for x in nombres])
    for i, x in enumerate(nombres):
        a1.text(i, cuenta[x] + 0.2, str(cuenta[x]), ha='center')
    a1.set_title('Resultado de las %d partidas' % len(filas))
    a1.set_ylabel('partidas')
    # 2) Movimientos de cada partida
    a2.bar([f[0] for f in filas], [f[2] for f in filas], color=[colores[f[1]] for f in filas])
    a2.axhline(LARGO, color='black', linestyle='--', linewidth=1)
    a2.set_title('Movimientos por partida (gris = empate por límite)')
    a2.set_xlabel('partida')
    a2.set_ylabel('movimientos')
    a2.set_xticks(range(1, len(filas) + 1))
    fig.suptitle(titulo)
    fig.tight_layout()
    fig.savefig(ruta, dpi=130)
    try:
        if matplotlib.get_backend().lower() != 'agg':
            plt.show()
    except Exception:
        pass

if __name__ == '__main__':
    resto = sys.argv[1:]
    n = int(next((x for x in resto if x.isdigit()), 20))
    nombres = [x for x in resto if not x.isdigit()]
    if len(nombres) >= 2:
        rojo, azul = nombres[0], nombres[1]       
    elif len(nombres) == 1:
        rojo, azul = MI_EQUIPO, nombres[0]        
    else:
        rojo, azul = MI_EQUIPO, MI_EQUIPO
    print('Jugando %d partidas: %s (rojo) vs %s (azul)...' % (n, rojo, azul))
    filas = jugar(rojo, azul, n)
    base = 'resultados_%s_vs_%s' % (rojo, azul)
    guardar(filas, base + '.csv')
    for g in ['rojo', 'azul', 'empate']:
        print('  %-7s %d' % (g, sum(1 for f in filas if f[1] == g)))
    dibujar(filas, '%s (rojo) vs %s (azul)' % (rojo, azul), base + '.png')
    print('Guardado: %s.csv y %s.png' % (base, base))