"""This script implements the DPLL algorithm from the power point"""
# Esta es una actualización del DPLL inicial hecho para la entrega parcial 1, que como pudimos ver presentaba un rendimiento muy bajo, tardando mucho en cada casilla para tomar 
# la siguiente decisión, esto es debido a que probaba muchas posibilidades una a una, entonces cuando aumentaba el número de variables se hacía muy lenta. Sin embargo, esta versión
# descarta aquellas opciones que sabe que no va a funcionar antes de probarlas; para ello, hace uso de los símbolos puros y clases unitarias, que permiten tomar decisiones 
# directamente sin tener que probar todas las combinaciones, reduciendo mucho el número de caminos que tiene que comprobar el algoritmo.

def clause_status(clause, model):
    """Verifies if clause is True or False

    Args:
        clause (list): list with all the clauses
        model (set): set with the variables
    
    Example:
        >>> clause_status([1,2], {1})
        True
        >>> clause_status([1,2], {-1})
        None
        >>> clause_status([1,2],{-1,-2})
        False
    """
    unknown = False
    for literal in clause:
        if literal in model:
            return True  
        if -literal not in model:
            unknown = True
    if unknown:
        return None
    return False

def find_pure_symbols(symbols, clauses, model):
    """Encuentra los símbolos que tienen el mismo signo siempre, en las cláusulas que aun nos interesan"""

    for symbol in symbols:
        if symbol in model or -symbol in model:
            continue
        positive = True
        negative = False

        for clause in clauses:
            if clause_status(clause, model) is True:
                continue
            if symbol in clause:
                positive = True
            if -symbol in clause:
                negative = True

        if positive and not negative:
            return symbol, True
        if negative and not positive:
            return symbol, False
    
    return None, None

def find_unit_clause(clauses, model):
    """Finds a Unit clause"""
    for clause in clauses:
        if clause_status(clause, model) is True:
            continue

        unassigned = [] #Se guardan los literales que no sabemos si son True o False
        for literal in clause:
            if literal not in model and -literal not in model:
                unassigned.append(literal)

        if len(unassigned) == 1: #Solo queda uno, así que es una cláusula unitaria
            literal = unassigned[0]
            return abs(literal), literal > 0
    return None, None

def choose_symbol(symbols, model):
    for symbol in symbols:
        if symbol not in model and -symbol not in model:
            return abs(symbol)
    return None

def dpll_recursive(clauses, symbols, model = None):
    if model is None:
        model = set()

    all_true = True
    for clause in clauses:
        status = clause_status(clause, model)
        if status is False:
            return False
        if status is None:
            all_true = False

    if all_true:
        return True

    symbol, value = find_pure_symbols(symbols, clauses, model)
    if symbol is not None:
        new_model = model.copy()
        if value: 
            new_model.add(symbol)
        else:
            new_model.add(-symbol)

        new_symbols = symbols.copy()
        new_symbols.discard(symbol)

        return dpll_recursive(clauses, new_symbols, new_model)

    symbol, value = find_unit_clause(clauses, model)
    if symbol is not None:
        new_model = model.copy()
        if value:
            new_model.add(symbol)
        else:
            new_model.add(-symbol)

        new_symbols = symbols.copy()
        new_symbols.discard(symbol)
        
        return dpll_recursive(clauses, new_symbols, new_model)

    symbol = choose_symbol(symbols, model)
    if symbol is None:
        return False
    new_symbols = symbols.copy()
    new_symbols.discard(symbol)

    model_true = model.copy()
    model_true.add(symbol)

    if dpll_recursive(clauses, new_symbols, model_true):
        return True

    model_false = model.copy()
    model_false.add(-symbol)
    return dpll_recursive(clauses, new_symbols, model_false)

def dpll(clauses):
    symbols = set()

    for clause in clauses:

        for literal in clause:
            symbols.add(abs(literal))

    model = set()

    return dpll_recursive(
        clauses,
        symbols,
        model
    )