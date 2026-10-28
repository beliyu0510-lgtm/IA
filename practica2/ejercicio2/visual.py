"""
visual.py - Animación (GIF) de una partida del ejercicio 2, útil para las diapositivas.

Se dibujan: muros, almacén (D), estaciones de carga, suministros, agentes con su barra
de batería y líneas finas entre emisor y receptor de los mensajes entregados ese turno.
"""

COLORES = ['#e6194b', '#3cb44b', '#4363d8', '#f58231', '#911eb4', '#42d4f4', '#f032e6', '#9a6324']


def capturar(col):
    """Foto ligera del estado (no necesita matplotlib)."""
    return {
        'turno': col.turno,
        'agentes': [(e.pos, e.bateria, e.lleva, e.agotado) for e in col.estados],
        'recursos': dict(col.recursos),
        'mensajes': list(col.canal.ultimasEntregas),
        'entregados': col.stats['entregados'],
        'caducados': col.stats['caducados'],
        'agotados': col.stats['agotados'],
        'nMensajes': col.canal.entregas,
    }


def guardarGif(col, fotos, ruta, fps=8):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation, PillowWriter
    from matplotlib.patches import Rectangle, Circle

    m = col.mapa
    bat = col.cfg.bateriaMax
    posEstacion = {'E%d' % k: p for k, p in enumerate(m.estaciones)}
    fig, ax = plt.subplots(figsize=(m.ancho * 0.32, m.alto * 0.32 + 0.6), dpi=90)

    def posDe(foto, quien):
        if isinstance(quien, str):
            return posEstacion.get(quien)
        return foto['agentes'][quien][0]

    def pintar(i):
        f = fotos[i]
        ax.clear()
        ax.set_xlim(-0.5, m.ancho - 0.5)
        ax.set_ylim(-0.5, m.alto - 0.5)
        ax.set_aspect('equal')
        ax.axis('off')
        for x in range(m.ancho):
            for y in range(m.alto):
                if m.muros[x][y]:
                    ax.add_patch(Rectangle((x - 0.5, y - 0.5), 1, 1, color='#1f2a44'))
        ax.add_patch(Rectangle((m.almacen[0] - 0.45, m.almacen[1] - 0.45), 0.9, 0.9, color='#c9a227'))
        ax.text(m.almacen[0], m.almacen[1], 'D', ha='center', va='center', fontsize=8, weight='bold')
        for p in m.estaciones:
            ax.add_patch(Rectangle((p[0] - 0.45, p[1] - 0.45), 0.9, 0.9, color='#7fd1ae'))
            ax.text(p[0], p[1], '⚡', ha='center', va='center', fontsize=8)
        for p in f['recursos']:
            ax.plot(p[0], p[1], marker='*', color='#ff9f1c', markersize=9)
        for emisor, receptor, _ in f['mensajes']:
            a, b = posDe(f, emisor), posDe(f, receptor)
            if a and b and a != b:
                ax.plot([a[0], b[0]], [a[1], b[1]], color='#888888', lw=0.6, alpha=0.6)
        for idx, (p, b, lleva, agotado) in enumerate(f['agentes']):
            c = '#555555' if agotado else COLORES[idx % len(COLORES)]
            ax.add_patch(Circle(p, 0.38, color=c, ec='black' if lleva else c, lw=2 if lleva else 0))
            if lleva:
                ax.plot(p[0], p[1], marker='*', color='white', markersize=6)
            ax.add_patch(Rectangle((p[0] - 0.45, p[1] + 0.45), 0.9, 0.12, color='#dddddd'))
            ax.add_patch(Rectangle((p[0] - 0.45, p[1] + 0.45), 0.9 * max(0, b) / bat, 0.12,
                                   color='#2ca02c' if b > 0.3 * bat else '#d62728'))
        ax.set_title('turno %d   entregados %d   caducados %d   agotados %d   mensajes %d'
                     % (f['turno'], f['entregados'], f['caducados'], f['agotados'], f['nMensajes']), fontsize=9)

    anim = FuncAnimation(fig, pintar, frames=len(fotos), interval=1000 / fps)
    anim.save(ruta, writer=PillowWriter(fps=fps))
    plt.close(fig)
