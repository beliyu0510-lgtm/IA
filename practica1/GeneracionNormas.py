"""The aim of this script is to automatically generate the rules of the game"""
"""The basics rules are:
    - Boxes next to the WUMPUS will emit reek (hedor)
    - Boxes next to a well (pozo) will emit breeze
    - Boxes in where the gold is will emit bright
    (for different amount of boxes, the number of rules will be different)"""

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

def id_var(concept, x,y): #Esta función se hace porque el ordenador solo entiende números, no entiende las proposiciones como nosotros
    """Converts a concept into an int number 

    Args:
        concept (string): Well (100), Breeze (200), Reek (300), Wumpus (400) 
        x (int): x coordinate
        y (int): y coordinate
    """
    codes = {"Well":100, "Breeze":200, "Reek":300, "Wumpus":400, "Bright": 500, "Gold":600}
    return codes[concept] + x*10 + y #esto devuelve por ejemplo 311 -> Hedor en (1,1)

def generate_rules(N) -> list:
    """Creates the list with all the rules for the game

    Args:
        N (int): size of the table

    Returns:
        list: List with all the rules  
    """
    rules = []
    for x in range(1, N+1):
        for y in range(1, N+1):
            neighbors = get_neighbors(x,y, N)

            # Rules for Breeze (Brisa <=> (Pozo1 v Pozo2...))

            # ========== Pasamos a FNC la proposición pero probamos solo con B, P1 y P2 ======== #
            # B <=> (P1 v P2); (B => (P1 v P2)) ∧ ((P1 v P2) => B); (¬B v (P1 v P2)) ∧ (¬(P1 v P2) v B);
            # (¬B v P1 v P2) ∧ ((¬P1 ∧ ¬P2) v B); (¬B v P1 v P2) v ((¬P1 v B)∧(¬P2 v B)); 
            # FNC = (¬B v P1 v P2) ∧ (¬P1 v B) ∧ (¬P2 v B)

            b_var = id_var('Breeze', x, y) #Devuelve las casillas donde hay brisa
            well = [id_var('Well', vx, vy) for vx, vy in neighbors] 

            rules.append([-b_var] + well)
            for pozo in well:
                rules.append([-pozo] + [b_var])

            # Rules for Reek (Reek <=> (Wumpus1, Wumpus2...))
            r_var = (id_var('Reek', x, y))
            wumpus = [id_var('Wumpus', vx, vy) for vx, vy in neighbors]

            rules.append([-r_var] + wumpus)
            for wps in wumpus:
                rules.append([-wps] + [r_var])

            # Rules for Bright (Resplandor <=> Oro)
            # ============== Pasamos a FNC ================ #
            # (R => O) ∧ (O => R); (¬R v O) ∧ (¬O v R);
            bt_var = (id_var('Bright', x, y))
            gold = (id_var('Gold', x, y))
            rules.append([-bt_var, gold])
            rules.append([-gold, bt_var])

    return rules
                



            




