"""This script represents the DPLL algorithm"""

def clause_status(clause, learned):
    """Verifies if a clause is True or False, the proposition used is B v A 

    Args:
        clause (list): rules established for the spot using generate_rules
        learned (list): knowledge the agent has gained during his exploration

    Returns:
        Boolean True or False depending on the clause
    """
    unknown = False #This elem is for the rules that the agent didn't learned
    for elem in clause:
        if elem in learned: 
            return True
        if -elem in learned:
            continue
        unknown = True
    if unknown:
        return None
    return False

def choose_variable(clauses, assignment):
    assigned_variable = [abs(x) for x in assignment]
    for clause in clauses:
        for literal in clause:
            variable = abs(literal)
            if variable not in assigned_variable:
                return variable
    return None

def dpll(clauses, asignment = None):
    if asignment == None:
        asignment = []

    statuses = []

    for clause in clauses:
        status = clause_status(clause, asignment)
        statuses.append(status)

    if all(status is True for status in statuses):
        return True
    if any(status is False for status in statuses):
        return False

    # In case there is still varibles without being determined:
    variable = choose_variable(clauses, asignment)
    new_asignment = asignment.copy()
    new_asignment.append(variable)

    if dpll(clauses, new_asignment):
        return True
    
    new_asignment = asignment.copy()
    new_asignment.append(-variable)
    
    return dpll(clauses, new_asignment)