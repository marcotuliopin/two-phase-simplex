from sys import argv
import numpy as np
from fractions import Fraction
from tabulate import tabulate
from Parser import Parser
import simplex

def main(input_filename, output_filename):
    parser = Parser()
    
    # read and parse input
    parser.parse_input(input_filename)

    # create Simplex inputs
    A = np.array(parser.A)
    b = np.array(parser.b)
    c = np.array(parser.objective)
    __print_tableau(np.hstack((A, b[np.newaxis].T)))
    print(c)

    # perform the Simplex Method
    status, tableau, certificate, basic_vars, m = simplex.main(A, b, c)

    # handle the results of the Simplex Method
    tableau[0, -1] += parser.optimal_value
    handle_status(status, tableau, certificate, basic_vars, output_filename, m)


def handle_status(status, tableau, certificate, basic_vars, output_filename, m):
    """Handle the results of the Simplex Method."""
    new_certificate = []
    for value in certificate:
        new_certificate.append(fraction_to_string(value))

    with open(output_filename, 'w') as f:
        f.write('Status: ')

        match status:
            case 'Unviable':
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


def __print_tableau(tableau):
    table = tabulate(tableau, tablefmt="fancy_grid")
    print(table)


if __name__ == '__main__':
    # main(argv[1], argv[2])

    with open(argv[1], 'r') as file:
        for line in file:
            names = line.split()
            main('input/'+names[0], 'output/'+names[1])
