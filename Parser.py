from sys import argv
from fractions import Fraction
from tabulate import tabulate
import numpy as np
import re

"""
Possible cases:
1- MIN x1 + x2 [DONE]
2- MAX x1 + x2 [DONE]
3- x1 + x2 >= +- 1 [DONE]
4- x1 + x2 <= +- 1 [DONE]
5- x1 + x2 == +- 1 [DONE]
6- x1 >= 0 [DONE]
7- x1 >= i; i != 0 [DONE]
8- x1 <= i [DONE]
9- x1 == 0 [DONE]
10- variável livre [DONE]
11- -x1 >= i [DONE]
12- -x1 <= i [DONE] 
"""

class Parser():
    """Reads the input LP for Simplex. Put the expressions in standard form while reading.

    Attributes:
        var_count : int
            number of variables in the LP. 
        variables : dict[str, Variable]
            variables information. See Variable definition for more.
        slack     : list[int]
            column index in coefficient matrix.
        objective : list[int]
            coefficients of the objective function.
        A         : list[list[int]]
            coefficient matrix of the constraints.
        b         : list[int]
            right-hand side values of the constraints.
    """
    def __init__(self):
        self.var_count = 0
        self.variables = {}
        self.slack = []
        self.objective = []
        self.A = []
        self.b = []
        self.free = []


    def parse_input(self, file_name):
        """Parses input data to create simplex input."""

        with open(file_name, 'r') as file:
            for line in file:
                if line.isspace(): # skip empty lines
                    continue
                equation =  line.split()
                print(line, end='')
                match equation[0]:
                    case "MIN":
                        # get objective function when it's minimization
                        equation = self.__transform_max_case(equation[1:])
                        self.objective = self.get_objective_function(equation)
                    case 'MAX':
                        # get objective function when it's maximization
                        self.objective = self.get_objective_function(equation[1:])
                    case _:
                        # get constraint and add it to coefficient matrix and constraint vector
                        self.get_constraint(equation)
        
        # if self.free:
        #     # handle any free variable
        #     for var in self.free:
        #         self.handle_free_var(var)
        if self.free:
            # handle any free variable
            self.handle_free_var()
        # empty list of free variables
        self.free.clear()

        self.__test_result()
        print()
        print()


    def get_objective_function(self, equation: list[str]):
        """Builds objective function from expression."""
        objective = [Fraction(0) for i in range(self.var_count)] # objective function

        # get the coefficients and variables of the equation
        i = 0
        while i < len(equation):
            if equation[i] in ['+', '-']:
                i += 1
                continue

            expression, j = self.__get_expression(equation[i:])

            # divide the expression into coefficient and variable
            coeff, var = self.__parse_expression(expression)

            # treat cases of subtraction
            if i > 0 and equation[i - 1] == '-':
                coeff = -coeff

            # ignore the expression if it's a literal
            if not var:
                continue
            # add new variable to the dictionary
            elif not var in self.variables:
                self.__add_variable(var)
                # add new variable to the objective function
                objective.append(0)

            # add coefficient to objective function
            objective[self.variables[var].index] += coeff
            i += j

        return objective


    def get_constraint(self, equation: list[str]):
        """Get constraint from equation.""" 
        if '>=' in equation:
            self.handle_greater_equal(equation)
        elif '<=' in equation:
            self.handle_less_equal(equation)
        else:
            self.handle_equality(equation)
        return


    def handle_greater_equal(self, equation: list[str]): # x1 + x2 >= 1
        """Put a lower bound inequality in the standard form and add it to the matrix."""
        idx = equation.index('>=')

        # get right hand side of constraint
        if equation[idx + 1] == '-':
            new_equation = self.__transform_max_case(equation[:idx])
            new_equation.extend(['<=', equation[idx + 2]])
            self.handle_less_equal(new_equation)
            return
        else:
            b = Fraction(equation[idx + 1])

        # get coefficients and any literal on left hand side of constraint
        a, b_aux = self.parse_constraint(equation[:idx])
        b += b_aux # Ex: x1 + x2 + 3 >= 1

        # handle a bounding constraint. Ex: x >= l
        if '+' not in equation and '-' not in equation:
            # get coefficient and variable name
            coeff, var = self.__parse_expression(equation[0])
            # get right hand side of constraint
            constraint = Fraction(b, coeff) # Ex: 2*x >= 2 -> x >= 1
            # variable is bounded
            if constraint >= 0:
                self.free.remove(var)
                if constraint == 0: # x >= 0
                    return

        self.__add_constraint_with_slack_var(-1, a, b)


    def handle_less_equal(self, equation: list[str]): # x1 + x2 <= 1
        """Put an upper bound inequality in the standard form and add it to the matrix."""
        idx = equation.index('<=')

        # get right hand side of constraint
        if equation[idx + 1] == '-':
            new_equation = self.__transform_max_case(equation[:idx])
            new_equation.extend(['<=', equation[idx + 2]])
            self.handle_less_equal(new_equation)
            return
        else:
            b = Fraction(equation[idx + 1])

        # get coefficients and any literal on left hand side of constraint
        a, b_aux = self.parse_constraint(equation[:idx])
        b += b_aux # Ex: x1 + x2 + 3 <= 1

        self.__add_constraint_with_slack_var(1, a, b)


    def handle_equality(self, equation: list[str]): # x1 + x2 == 1
        """Handles a equality constraint and put it in standard form."""
        idx = equation.index('==')

        # check if right hand side of constraint is negative
        if equation[idx + 1] == '-':
            new_equation = self.__transform_max_case(equation[:idx])
            new_equation.extend(['==', equation[idx + 2]])
            equation = new_equation

        # check if it's a bounding constraint. Ex: x == 0
        if '+' not in equation and '-' not in equation:
            eq1 = equation # create lower bound equation
            eq1[idx] = '>='
            self.get_constraint(eq1) # parse equation

            eq2 = equation # create upper bound equation
            eq2[idx] = '<='
            self.get_constraint(eq2) # parse equation
            return

        # get right side of the inequation
        idx = equation.index('==')
        b = Fraction(int(equation[idx + 1]))
        # get coefficients and any literal on left hand side of constraint
        a, b_aux = self.parse_constraint(equation[:idx])
        b += b_aux # Ex: x1 + x2 + 3 <= 1

        # add new values to coefficient matrix
        self.__add_row(a)
        # add new constraint to constraint list
        self.b.append(b)


    # def handle_free_var(self, var):
    #     """Separates free variables onto two bound variables."""
    #     # create new variable
    #     self.variables[var].sindex = self.var_count
    #     self.var_count += 1

    #     # create column for new variable
    #     col = [-a[self.variables[var].index] for a in self.A]
    #     # add column to matrix
    #     for (a, c) in zip(self.A, col):
    #         a.append(c)
        
    #     # add variable to the objective function
    #     val = -self.objective[self.variables[var].index]
    #     self.objective.append(val)

    def handle_free_var(self):
        """Separates free variables onto two bound variables."""
        # create new variable
        new_var = 'W'
        self.__add_variable(new_var)
        self.free.remove(new_var)

        # create column for new variable
        col = [0 for a in self.A]
        for var in self.free:
            idx = self.variables[var].index
            for i in range(len(self.A)):
                col[i] -= self.A[i][idx]
        # add column to matrix
        for (a, c) in zip(self.A, col):
            a.append(c)
        
        # add variable to the objective function
        val = 0
        for c in self.objective:
            val -= c
        self.objective.append(val)


    def parse_constraint(self, equation: list[str]):
        """Helps parsing constraint equation."""
        a = [Fraction(0) for i in range(self.var_count)] # coefficients
        b = 0 # constraint

        i = 0
        while i < len(equation):
            if equation[i] in ['+', '-']:
                i += 1
                continue

            expression, j = self.__get_expression(equation[i:])

            # divide the expression into coefficient and variable
            coeff, var = self.__parse_expression(expression)

            # treat cases of subtraction
            if i > 0 and equation[i - 1] == '-':
                coeff = -coeff

            # coeff is a free number, so subtract it from constraint
            if not var:
                b -= coeff
                continue
            # add new variable to the dictionary
            elif not var in self.variables:
                self.__add_variable(var)
                a.append(0)

            # add coefficient to objective function
            a[self.variables[var].index] += coeff
            i += j
        
        return [a, b]


    def __parse_expression(self, expression: str): # 2*x1
        """Divides an expression into coefficient and variable."""
        # get name of var
        var_regex = re.compile('([*/]?-?)([0-9]*[a-zA-Z]+[a-zA-Z0-9]*)([*/]?)')
        var = var_regex.search(expression).group(2)

        # substitute var name with '1' in expression
        f = lambda match : match.group(1) + '1' + match.group(3)
        expression = var_regex.sub(f, expression)

        # get coefficient value
        coeff = self.__calculate_coeff(expression)
        return [coeff, var]
    

    def __add_constraint_with_slack_var(self, coeff, a, b):
        """Helps adding slack variable."""
        # add slack variable
        self.slack.append(self.var_count)
        self.var_count += 1
        a.append(Fraction(coeff))

        # add new values to coefficient matrix
        self.__add_row(a)
        # add new constraint to constraint list
        self.b.append(b)


    def __add_row(self, row: list[int]):
        """Adds new row to coefficient matrix."""
        if self.A:
            while len(self.A[0]) < len(row):
                for a in self.A:
                    a.append(Fraction(0))
        self.A.append(row)

        while len(self.objective) < len(row):
            self.objective.append(Fraction(0))


    def __add_variable(self, var: str):
        """Adds new variable to dictionary. Initially, also add it as a free variable."""
        self.variables[var] = Variable(self.var_count)
        self.var_count += 1
        self.free.append(var)
    

    def __get_expression(self, equation: list[str]):
        """Joins multiple symbols into an expression."""
        # join the symbols from the expression
        expression = ''
        j = 0
        for i in range(len(equation)):
            if equation[i] in ['+', '-']:
                break
            expression = expression + equation[i]
            j += 1

        return [expression, j]


    def __transform_max_case(self, equation: list[str]):
        """Multiplies equation by minus one."""
        new_equation = []
        if equation[0] != '-': 
            new_equation.append('-')
        if equation[0] == '+' or equation[0] == '-':
            equation = equation[1:]
        new_equation.append(equation[0])
        for word in equation[1:]:
            if word == '-':
                new_equation.append('+')
            elif word == '+':
                new_equation.append('-')
            else:
                new_equation.append(word)
        return new_equation

    def __calculate_coeff(self, expression: list[str]):
        """Calculates coefficient value."""
        symbols = re.split('([*/])', expression)
        coeff = Fraction(symbols[0])
        for i in range(1, len(symbols), 2):
            if symbols[i] == '*':
                coeff *= Fraction(symbols[i + 1])
            else:
                coeff /= Fraction(symbols[i + 1])
        return coeff
    

    def __test_result(self):
        """Prints test."""
        print()
        print('--------------------------------------------')
        print('Resultado:')
        print('MAX ', self.objective)
        print('--------------------------------------------')
        print('[', end='')
        slack = 1
        for i in range(len(self.A[0])):
            p = True
            for name, var in self.variables.items():
                if var.index == i or var.sindex == i:
                    print(name, end='')
                    if i < len(self.A[0]) - 1:
                        print(',', end='')
                    p = False
            if p: 
                print('s'+str(slack), end='')
                if i < len(self.A[0]) - 1:
                    print(',', end='')
                slack += 1
        print(']')
        # aux = []
        # for i in range(len(self.A)):
        #     aux.append(self.A[i])
        #     aux[i].append(self.b[i])
        # table = tabulate(aux, tablefmt="fancy_grid")
        # print(table)

class Variable():
    """Variable of a LP.
    
    Attributes:

    index  : int
        index of variable in the coefficient matrix.
    sindex : int
        index of substitution variable in the coefficient matrix (var = var' + var").
    """ 
    def __init__(self, _idx1: int, _idx2: int = -1):
        self.index = _idx1
        self.sindex = _idx2