from sys import argv
import numpy as np
from fractions import Fraction
from Parser import Parser
import simplex

def main(input_filename, output_filename):
    parser = Parser()
    
    # read and parse input
    parser.parse_input(input_filename)

    if parser.s:
        for i in range(len(parser.s[0])):
            parser.objective.append(0)

    # create Simplex inputs
    A = np.hstack((parser.A, parser.s))
    artificial_vars, artificial_costs, basic_vars = add_artificial_vars(A)
    b = np.array(parser.b)
    c = np.array(parser.objective)

    # perform the Simplex Method
    status, tableau, certificate, basic_vars, m = simplex.main(A, b, c, basic_vars, artificial_vars, artificial_costs)

    # handle the results of the Simplex Method
    tableau[0, -1] += parser.optimal_value
    if not parser.is_max:
        tableau[0, -1] = -tableau[0, -1]
    handle_status(status, tableau, certificate, basic_vars, output_filename, m)


def add_artificial_vars(A):
    y, x = A.shape
    I = np.eye(y)
    basic_vars = np.zeros(y, dtype=int)
    artificial_vars = np.zeros((y, y), dtype=int)
    artificial_costs = np.zeros(y, dtype=int)
    a_count = 0

    for i in range(y):
        var = check_column(A, I[:, i])
        # add new auxiliar variable
        if var == -1:
            artificial_vars[:, a_count] = I[:, i]
            artificial_costs[a_count] = 1
            var = x
            x += 1
            a_count += 1
        # add variable to the base
        basic_vars[i] = var
    
    artificial_vars = np.delete(artificial_vars, np.s_[a_count:], axis=1)
    artificial_costs = np.delete(artificial_costs, np.s_[a_count:])

    return artificial_vars, artificial_costs, basic_vars


def check_column(A, col):
    for i in range(A.shape[1]):
        if np.array_equal(A[:, i], col):
            return i
    return -1


def handle_status(status, tableau, certificate, basic_vars, output_filename, m):
    """Handle the results of the Simplex Method."""
    new_certificate = []
    for value in certificate:
        new_certificate.append(fraction_to_string(value))

    with open(output_filename, 'w') as f:
        f.write('Status: ')

        match status:
            case 'Infeasible':
                f.write('inviavel\n')
            case 'Unbound':
                f.write('ilimitado\n')
            case 'Optimal':
                f.write('otimo\n')
                f.write('Objetivo: ' + fraction_to_string(tableau[0, -1]) + '\n')
                f.write('Solucao:\n')
                for i in range(m, tableau.shape[1] - 1):
                    if i in basic_vars:
                        f.write(fraction_to_string(tableau[np.where(basic_vars == i)[0][0] + 1, -1]) + ' ')
                    else:
                        f.write(fraction_to_string(Fraction(0)) + ' ')
                f.write('\n')

        f.write('Certificado:' + '\n')
        for value in new_certificate:
            f.write(value + ' ')


def fraction_to_string(fraction: Fraction):
    ratio = fraction.as_integer_ratio()
    return str(ratio[0] / ratio[1])


main(argv[1], argv[2])
