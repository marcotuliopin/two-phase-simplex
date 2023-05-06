import numpy as np
from tabulate import tabulate
from fractions import Fraction

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

def main(A, b, c):
    m, n = A.shape

    # add auxiliar variables for Simplex Phase 1
    A = np.hstack((A, np.eye(m)))
    c_aux = np.concatenate((np.zeros(n), np.ones(m)))

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

    # store the position of the basic and the non-basic variables
    non_basic_vars = np.arange(m, m + n)
    basic_vars = np.arange(m + n, 2*m + n)

    # store the auxiliar variables location on the Tableau
    w = np.s_[m + n: -1]

    # Phase 1
    # efetuate Gaussian Elimination of the costs

    # TODO
    __print_tableau(tableau)

    # add original objective function costs on top of the tableau
    tableau = np.vstack((tableau[0, :], tableau))
    tableau[0, m: m + n] = -c
    tableau[0, m + n:] = 0

    # TODO
    __print_tableau(tableau)


    # pivot the tableau to turn the basic variables costs to zero
    for i in basic_vars:
        tableau[1, :] = tableau[1, :] - tableau[1, i] * tableau[2 + i - basic_vars[0], :]

        # TODO
        __print_tableau(tableau)

    # call Simplex for the auxiliar Tableau
    tableau, status, certificate = simplex(tableau, m, c = 1)

    # check if Simplex found an error in the problem
    if status != 'Optimal':
        return [status, tableau, certificate]

    # check if problem is Unviable
    if tableau[1, -1] < 0:
        certificate = tableau[0, :m]
        return ['Unviable', tableau, certificate]


    # Phase 2
    # remove the auxiliar variables from the Tableau
    tableau = np.delete(tableau, w, 1)
    tableau = np.delete(tableau, 1, 0)

    # TODO
    __print_tableau(tableau)

    # call Simplex for the original Tableau
    tableau, status, certificate = simplex(tableau, m, c = 0)

    # TODO
    __print_tableau(tableau)

    return [status, tableau, certificate]



def simplex(tableau, m, c):
    """Solves a linear programming problem using the Two-Phase Simplex."""
    # store indexes of the different tableau parts

    while True:
        # check if all costs are non-negative
        if not np.any(tableau[c, m: -1] < 0):
            # found optimal solution
            break

        # choose variable to enter the base (pivot column)
        pivot_column = np.argmin(tableau[c, m: -1]) + m
        # for i in range(m, tableau.shape[1]):
        #     if tableau[c, i] < 0:
        #         pivot_column = i
        #         break
        
        # check if the new base variable has unlimited growth potential
        if np.all(tableau[c + 1:, pivot_column] <= 0):
            certificate = tableau[c + 1:, pivot_column].T
            return [tableau, 'Unbound', certificate]

        # calculate ratios
        ratios = calculate_ratios(tableau, pivot_column, c)

        # check if all ratios are non-positive
        if np.all(ratios <= 0):
            return [tableau , 'Unbound']

       
        # choose variable to leave the base (pivot row)
        ratios = np.where(ratios > 0, ratios, np.inf)
        pivot_row = ratios.argmin() + 1 + c

        # perform pivot operation
        tableau = gaussian_elimination(tableau, pivot_row, pivot_column, m)

        # TODO
        __print_tableau(tableau)

    certificate = tableau[0, :m]
    return [tableau, 'Optimal', certificate]


def calculate_ratios(tableau, pivot_column, c):
    """Calculate ratios for new base variable."""
    INF = 2**32 - 1
    ratios = []
    for i in range(c + 1, tableau.shape[0]):
        if tableau[i, pivot_column] == 0:
            ratios.append(Fraction(INF) if tableau[i, -1] > 0 else Fraction(-INF))
        else:
            ratios.append(Fraction(tableau[i, - 1], tableau[i, pivot_column]))
    ratios = np.array(ratios)
    return ratios


def gaussian_elimination(tableau, pivot_row, pivot_column, m):
    """Efetuate Gaussian Elimination."""
    pivot = tableau[pivot_row, pivot_column]
    tableau[pivot_row, :] = tableau[pivot_row, :] / pivot
    for i in range(m + 1):
        if i == pivot_row:
            continue
        aux = tableau[i, pivot_column]
        tableau[i, :] = tableau[i, :] - aux * tableau[pivot_row, :]
    return tableau


def __print_tableau(tableau):
    table = tabulate(tableau, tablefmt="fancy_grid")
    print(table)
