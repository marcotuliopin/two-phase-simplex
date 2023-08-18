import numpy as np
from fractions import Fraction
from tabulate import tabulate

"""
    Extended Tableau:
    -----------------------------------------
    |    0    |       c       |    w    | 0 |
    -----------------------------------------
    |         |               |         |   |
    |    I    |       A       |    w    | b |
    |  m x m  |     m x n     |  m x m  |   |
    -----------------------------------------
"""

epsilon = 10**-5

def main(A, b, c, basic_vars, artificial_vars, artificial_costs):
    m, n = A.shape

    # add auxiliar variables for Simplex Phase 1
    A = np.hstack((A, artificial_vars))
    c_aux = np.concatenate((np.zeros(n), artificial_costs))

    # transpose the constraint row vector
    b = np.insert(b, 0, 0)[np.newaxis].T

    # initialize Extended Tableau
    tableau = np.vstack((np.zeros(m), np.eye(m)))
    tableau = np.hstack((tableau, np.vstack((c_aux, A))))
    tableau = np.hstack((tableau, b))

    tableau = tableau.astype(Fraction)
    for i in range(tableau.shape[0]):
        for j in range(tableau.shape[1]):
            tableau[i, j] = Fraction(tableau[i, j])

    basic_vars += m

    # Phase 1
    # efetuate Gaussian Elimination of the costs

    # add original objective function costs on top of the tableau
    tableau = np.vstack((tableau[0, :], tableau))
    tableau[0, m: m + n] = -c
    tableau[0, m + n:] = 0
    
    # pivot the tableau to turn the basic variables costs to zero
    for i in range(len(basic_vars)):
        tableau = gaussian_elimination(tableau = tableau, pivot_row = i + 2, pivot_column = basic_vars[i], m = m, c = 1)

    # call Simplex for the auxiliar Tableau
    tableau, status, certificate, basic_vars = simplex(tableau, m, basic_vars, c = 1)

    # check if Simplex found an error in the problem
    if status != 'Optimal':
        return [status, tableau, certificate, basic_vars, m]

    # check if problem is Infeasible
    if tableau[1, -1] < 0:
        certificate = tableau[0, :m]
        return ['Infeasible', tableau, certificate, basic_vars, m]

    # Phase 2
    # remove the auxiliar variables from the Tableau
    # tableau, basic_vars, m = remove_aux_variable(tableau, basic_vars, m, n)
    # store the auxiliar variables location on the Tableau
    w = np.s_[m + n: -1]

    # remove auxiliar variables columns
    tableau = np.delete(tableau, w, 1)
    tableau = np.delete(tableau, 1, 0)

    # call Simplex for the original Tableau
    tableau, status, certificate, basic_vars = simplex(tableau, m, basic_vars, c = 0)

    return [status, tableau, certificate, basic_vars, m]



def simplex(tableau, m, basic_vars, c):
    """Solves a linear programming problem using the Two-Phase Simplex."""
    # store indexes of the different tableau parts
    while True:
        # __print_tableau(tableau)
        # check if all costs are non-negative
        if np.all(tableau[c, m: -1] > -epsilon):
            # found optimal solution
            break

        # choose variable to enter the base (pivot column)
        for i in range(m, tableau.shape[1]):
            if tableau[c, i] < 0:
                pivot_column = i
                break
        
        # calculate ratios
        ratios = calculate_ratios(tableau, pivot_column, c)

        # check if the new base variable has unlimited growth potential
        unbound = True
        for ratio in ratios:
            if ratio > -epsilon:
                unbound = False
        if unbound:
            certificate = generate_unbound_certificate(tableau, m, pivot_column, basic_vars, c)
            return [tableau, 'Unbound', certificate, basic_vars]
       
        # choose variable to leave the base (pivot row)
        lower = np.inf
        for i in range(len(ratios)):
            if ratios[i] < lower and ratios[i] >= -epsilon:
                lower = ratios[i]
                pivot_row = i
        pivot_row += 1 + c

        # perform pivot operation
        tableau = gaussian_elimination(tableau, pivot_row, pivot_column, m, c)

        # update basic variables indices
        basic_vars[pivot_row - c - 1] = pivot_column

    certificate = tableau[0, :m]
    return [tableau, 'Optimal', certificate, basic_vars]


def generate_unbound_certificate(tableau, m, pivot_column, basic_vars, c):
    certificate = []
    for i in range(m, tableau.shape[1] - 1):
        if i == pivot_column:
            certificate.append(1)
        elif i in basic_vars:
            certificate.append(-tableau[np.where(basic_vars == i)[0] + c + 1, pivot_column][0])
        else:
            certificate.append(0)
    certificate = np.array(certificate)
    return  np.array(certificate) 


def calculate_ratios(tableau, pivot_column, c):
    """Calculate ratios for new base variable."""
    INF = 2**32 - 1
    ratios = []
    for i in range(c + 1, tableau.shape[0]):
        if tableau[i, pivot_column] <= epsilon:
            ratios.append(Fraction(-INF))
        else:
            ratios.append(Fraction(tableau[i, -1], tableau[i, pivot_column]))
    ratios = np.array(ratios)
    return ratios


def gaussian_elimination(tableau, pivot_row, pivot_column, m, c):
    """Efetuate Gaussian Elimination."""
    pivot = tableau[pivot_row, pivot_column]
    tableau[pivot_row, :] = tableau[pivot_row, :] / pivot
    for i in range(m + 1 + c):
        if i == pivot_row:
            continue
        aux = tableau[i, pivot_column]
        tableau[i, :] = tableau[i, :] - aux * tableau[pivot_row, :]
    return tableau


def remove_aux_variable(tableau, basic_vars, m, n):
    """Remove auxiliar variables from the base."""
    # check if any auxiliar variable was left in the column
    j = 0
    new_basic_vars = []
    for i in range(len(basic_vars)):
        # find an auxiliar variable in the base
        if basic_vars[i] >= m + n + j:
            # remove auxiliar variable from the base
            print(tableau[i + 2, m: m + n])
            if count_non_zero(tableau[i + 2 - j, m: m + n]):
                # find a candidate to enter the base
                for j in range(m, m + n):
                    # check if candidate is valid
                    if tableau[i + 2 - j, j] != 0 and j != basic_vars[i]:
                        # perform pivot operation on cadidate
                        tableau[i + 2 - j, :] = tableau[i + 2 - j, :] / tableau[i + 2 - j, j]
                        tableau[1, :] = tableau[1, :] - tableau[1, j] * tableau[i + 2 - j, :]
                        # add candidate to the base
                        new_basic_vars.append(j)
                        break
            # remove the constraint, as it is redundant
            else:
                tableau = np.delete(tableau, i + 2 - j, 0)
                tableau = np.delete(tableau, i, 1)

                m -= 1
                j += 1
        # the constraint does not refer to an auxiliar variable
        else:
            new_basic_vars.append(basic_vars[i])

    # store the auxiliar variables location on the Tableau
    w = np.s_[m + n: -1]

    # remove auxiliar variables columns
    tableau = np.delete(tableau, w, 1)
    tableau = np.delete(tableau, 1, 0)

    new_basic_vars = [i - j for i in new_basic_vars]
    return [tableau, np.array(new_basic_vars), m]


def count_non_zero(array):
    """Count number of non zeros in the array."""
    i = 0
    for c in array:
        if c != Fraction(0):
            i += 1
    return i


def __print_tableau(tableau):
    table = tabulate(tableau, tablefmt="fancy_grid")
    print(table)
