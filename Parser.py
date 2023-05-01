from sys import argv
import numpy as np
import re

"""
Possible cases:
1- MIN x1 + x2 [DONE]
2- MAX x1 + x2 [DONE]
3- x1 + x2 >= +- 1 [DONE]
4- x1 + x2 <= +- 1 [DONE]
5- x1 + x2 == +- 1 [DONE]
6- x1 >= 0 [TODO]
7- x1 >= i; i != 0 [TODO]
8- x1 <= i [TODO]
9- x1 == 0 [TODO]
"""

class Parser():
    def __init__(self):
        self.epsilon = 10 ** -4
        self.var_count = 0 # number of variables
        self.variables = {} # variables {name of variable, column index in self.A}
        self.slack = [] # slack variables[ column index in self.A]
        self.objective = [] # objective function [coefficients]
        self.A = np.empty(0) # coefficient matrix
        self.b = [] # constraint vector

    """TODO: ver como tratar pontos flutuantes"""
    # CLASSIFICADO
    def parse_input(self, file_name):
        """Parse input data to create simplex input."""

        with open(file_name, 'r') as file:
            for line in file:
                equation =  line.split()
                if equation[0] == '#': # read a comment in the text
                    continue
                match equation[0]:
                    case "MIN":
                        # get objective function when it's minimization
                        equation = self.__transform_max_case(equation[1:])
                        objective = self.get_objective_function(equation)
                    case 'MAX':
                        # get objective function when it's maximization
                        objective = self.get_objective_function(equation[1:])
                    case _:
                        # get constraint and add it to coefficient matrix and constraint vector
                        self.get_constraint(equation)


    # CLOSED
    # CLASSIFICADO
    def get_objective_function(self, equation: list[str]): # MIN x1 + 2*x2
        """Build objective function from expression."""
        objective = [0 for i in range(self.var_count)] # objective function

        # get the coefficients and variables of the equation
        for i in range(len(equation)):
            if i > 0 and equation[i] != '+' and equation[i] != '-':
                continue
            # divide the expression into coefficient and variable
            coeff, var = self.__parse_expression(equation[i + 1])
            if equation[i] == '-':
                # treat cases of subtraction
                coeff = -coeff
            if not var:
                # ignore the expression if it's a literal
                continue
            elif not var in self.variables:
                # add new variable to the dictionary
                self.variables[var] = self.var_count
                self.var_count += 1
                objective.append(0)
            # add coefficient to objective function
            objective[self.variables[var]] += coeff
        return objective


    # CLASSIFICADO
    def get_constraint(self, equation: list[str]): # x1 + x2 <= 1 ou x1 + x2 == 1 ou x1 + x2 >= 0
        """Get constraint from equation.""" 
        if '>=' in equation:
            self.handle_lower_bound(equation)
        elif '<=' in equation:
            self.handle_upper_bound(equation)
        else:
            self.handle_equality(equation)
        
        return


    # CLASSIFICADO
    def handle_lower_bound(self, equation: list[str]): # x1 + x2 >= 1
        """Put a lower bound inequality in the standard form and add it to the matrix."""
        idx = equation.index('>=')
        a = [] # coefficients
        b = 0 # constraint

        # TODO
        # check if it's a bounding constraint. Ex: x >= 0
        if '+' not in equation and '-' not in equation:
            pass

        if equation[idx + 1] == '-': # x1 + x2 >= -1 -> - x1 - x2 >= 1
            # handle negative constraint
            b = equation[idx + 2]
            equation[:idx] = self.__transform_max_case(equation[:idx])
            

        # get coefficients and constraint
        a, b_aux = self.parse_constraint(equation)
        b += b_aux

        # add slack variable
        self.slack.append(self.var_count)
        self.var_count += 1
        a.append(-1)

        # add new values to coefficient matrix
        self.__add_row(a)
        # add new constraint to constraint list
        self.b = b.append(b)

        return
        

    # CLASSIFICADO
    def handle_upper_bound(self, equation: list[str]): # x1 + x2 <= 1
        """Put an upper bound inequality in the standard form and add it to the matrix."""
        idx = equation.index('<=')
        a = [] # coefficients
        b = 0 # constraint

        # TODO
        # check if it's a bounding constraint. Ex: x <= 0
        if '+' not in equation and '-' not in equation:
            # handle_bounding_upper_bound(A, B, equation, variables, var_count)
            pass

        if equation[idx + 1] == '-': # x1 + x2 >= -1 -> - x1 - x2 >= 1
            # handle negative constraint
            b = equation[idx + 2]
            equation[:idx] = self.__transform_max_case(equation[:idx])

        # get coefficients and constraint
        a, b_aux = self.parse_constraint(equation)
        b += b_aux

        # add slack variable
        self.slack.append(self.var_count)
        self.var_count += 1
        a.append(1)

        # add new values to coefficient matrix
        self.__add_row(a)
        # add new constraint to constraint list
        self.b = b.append(b)

        return


    # CLASSIFICADO
    def handle_equality(self, equation: list[str]): # x1 + x2 == 1
        """Turn an equality into two inequalities, using the property that u == v
        is the same as u <= v and u >= v. After that, put both in the standard form
        and add to the matrix."""
        idx = equation.index('==')

        # TODO
        # check if it's a bounding constraint. Ex: x == 0
        if '+' not in equation and '-' not in equation:
            pass

        eq1 = equation # create lower bound equation
        eq1[idx] = '>='
        self.get_constraint(eq1) # parse equation

        eq2 = equation # create upper bound equation
        eq2[idx] = '<='
        self.get_constraint(eq2) # parse equation


    # CLASSIFICADO
    def handle_bounding_upper_bound(self, equation: list[str]): # x1 >= i
        """Handle a bounding upper bound inequality and put it in standard form."""
        free = []
        # handle base case: x >= 0
        if equation[0] != '-': # equation[0] is the variable of the inequality
            var = equation[0]
            if equation[2] == '0': # equation[2] is the constraint
                free.pop(free.index(var))
            if not var in self.variables:
                self.variables[var] = self.var_count
                self.var_count += 1


    # TODO: está errado. Consertar.
    # CLASSIFICADO
    def parse_constraint(self, equation: list[str]):
        """Help parsing constraint equation."""
        a = [0 for i in range(self.var_count)] # coefficients
        b = 0 # constraint

        for i in range(len(equation)):
            if i > 0 and equation[i] != '+' and equation[i] != '-':
                continue
            # divide the expression into coefficient and variable
            coeff, var = self.__parse_expression(equation[i + 1])
            if equation[i] == '-':
                # treat cases of subtraction
                coeff = -coeff
            if not var:
                # coeff is a free number, so subtract it from constraint
                b -= coeff
                continue
            elif not var in self.variables:
                # add new variable to the dictionary
                self.variables[var] = self.var_count
                self.var_count += 1
                a.append(0)
            # add coefficient to objective function
            a[self.variables[var]] += coeff
        
        return [a, b]


    # CLOSED
    # CLASSIFICADO
    def __parse_expression(self, expression: list[str]): # 2*x1
        """Divide an expression into coefficient and variable."""
        if len(expression) == 1:
            # the coefficient equals one
            return [1, expression]

        # get name of var
        var_regex = re.compile('([*/]?)([0-9]*[a-zA-Z]+[a-zA-Z0-9]*)([*/]?)')
        var = var_regex.search(expression).group(2)

        # substitute var name with '1' in expression
        f = lambda match : match.group(1) + '1' + match.group(3)
        expression = var_regex.sub(f, expression)

        # get coefficient value
        coeff = self.__calculate_coeff(expression)
        return [coeff, var]


    # CLASSIFICADO
    def __add_row(self, row: list[int]):
        """Add new row to coefficient matrix."""
        if self.A.shape[1] < len(row):
            # give A the same number of columns as row
            aux = np.zeros(self.A.shape[0], len(row) - self.A.shape[1])
            self.A = np.hstack((self.A, aux))
        self.A = np.vstack((self.A, row)) 
        return


    # CLOSED
    # (x1 + x2) -> (- x1 - x2)
    # CLASSIFICADO
    def __transform_max_case(self, equation: list[str]):
        """Multiply equation by minus one."""
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


    # CLOSED
    # 2*3*5 -> 30
    # CLASSIFICADO
    def __calculate_coeff(self, expression: list[str]):
        """Calculate coefficient value."""
        symbols = re.split('([*/])', expression)
        coeff = int(symbols[0])
        for i in range(1, len(symbols), 2):
            if symbols[i] == '*':
                coeff *= int(symbols[i + 1])
            else:
                coeff /= int(symbols[i + 1])
        return coeff