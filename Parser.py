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
6- x1 >= 0 [DONE]
7- x1 >= i; i != 0 [DONE]
8- x1 <= i [DONE]
9- x1 == 0 [DONE]
10- variável livre [DONE]
"""

class Parser():
    """Read the input LP for Simplex. Put the expressions in standard form while reading.

    Attributes:
        epsilon   : int
            small constant for rounding numbers.
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
        self.epsilon = 10 ** -4
        self.var_count = 0
        self.variables = {}
        self.slack = []
        self.objective = []
        self.A = []
        self.b = []
        self.free = []


    """TODO: ver como tratar pontos flutuantes"""
    def parse_input(self, file_name):
        """Parse input data to create simplex input."""

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
        
        if self.free:
            # handle any free variable
            for var in self.free:
                self.handle_free_var(var)

        # empty list of free variables
        self.free.clear()

        self.__test_result()


    def get_objective_function(self, equation: list[str]): # MIN x1 + 2*x2
        """Build objective function from expression."""
        objective = [0 for i in range(self.var_count)] # objective function

        # get the coefficients and variables of the equation
        for i in range(len(equation)):
            if equation[i] == '+' or equation[i] == '-':
                continue
            # divide the expression into coefficient and variable
            coeff, var = self.__parse_expression(equation[i])
            if i > 0 and equation[i - 1] == '-':
                # treat cases of subtraction
                coeff = -coeff
            if not var:
                # ignore the expression if it's a literal
                continue
            elif not var in self.variables:
                # add new variable to the dictionary
                self.__add_variable(var)
                # add new variable to the objective function
                objective.append(0)
            # add coefficient to objective function
            objective[self.variables[var].index] += coeff
        return objective


    def get_constraint(self, equation: list[str]): # x1 + x2 <= 1 ou x1 + x2 == 1 ou x1 + x2 >= 0
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

        # handle a bounding constraint. Ex: x >= l
        if '+' not in equation and '-' not in equation:
            self.handle_bounding_greater_equal(equation)
            return

        # TODO: handle negative right side of constraint

        # get right hand side of constraint
        b = int(equation[idx + 1])
        # get coefficients and any literal on left hand side of constraint
        a, b_aux = self.parse_constraint(equation[:idx])
        b += b_aux # Ex: x1 + x2 + 3 >= 1

        self.__add_slack_var(-1, a, b)


    # TODO: considerar casos:
    # 1. - x >= i
    def handle_bounding_greater_equal(self, equation: list[str]): # x1 >= i
        """Handle a bounding upper bound inequality and put it in standard form."""
        # get coefficient and variable name
        coeff, var = self.__parse_expression(equation[0])

        self.free.remove(var)

        # get right hand side of constraint
        b = int(equation[2])/coeff # Ex: 2*x >= 2 -> x >= 1

        # constraint is already in the standard form
        if b == 0:
            return

        # add variable to the dictionary if never seen before
        if not var in self.variables:
            self.__add_variable(var)

        # handle x >= l; l < 0
        if b < 0:
            # make substitution x = x' - x"
            self.handle_free_var(var)

        # get coefficients and any literal on left hand side of constraint
        a, b_aux = self.parse_constraint(equation[:equation.index('>=')])
        # add coefficient to the variable generated by the substitution x = x' - x"
        if b < 0:
            a[len(a) - 1] = -coeff
        b += b_aux # Ex: x1 + x2 + 3 >= 1

        self.__add_slack_var(-1, a, b)
            

    def handle_less_equal(self, equation: list[str]): # x1 + x2 <= 1
        """Put an upper bound inequality in the standard form and add it to the matrix."""
        idx = equation.index('<=')
        a = [] # coefficients
        b = 0 # constraint

        # handle a bounding constraint. Ex: x <= 0
        if '+' not in equation and '-' not in equation:
            self.handle_bounding_less_equal(equation)
            return

        # TODO: handle negative right side of constraint

        # get right side of the inequation
        b = int(equation[idx + 1])

        # get coefficients and any literal on left hand side of constraint
        a, b_aux = self.parse_constraint(equation[:idx])
        b += b_aux # Ex: x1 + x2 + 3 <= 1

        self.__add_slack_var(1, a, b)


    # TODO: considerar casos:
    # 1. - x <= i
    def handle_bounding_less_equal(self, equation: list[str]): # x1 <= i
        """Handle a bounding upper bound inequality and put it in standard form."""
        # get coefficient and variable name
        coeff, var = self.__parse_expression(equation[0])

        self.free.remove(var)

        b = int(equation[2])/coeff # Ex: 2*x >= 2 -> x >= 1

        # addd variable to the dictionary if never seen before
        if not var in self.variables:
            self.__add_variable(var)

        # make substitution x = x' - x"
        self.handle_free_var(var)
        # get coefficients and any literal on left hand side of constraint
        a, b_aux = self.parse_constraint(equation[:equation.index('<=')])
        # add coefficient to the variable generated by the substitution x = x' - x"
        a[len(a) - 1] = -coeff
        b += b_aux # Ex: x1 + x2 + 3 <= 1

        self.__add_slack_var(1, a, b)


    def handle_equality(self, equation: list[str]): # x1 + x2 == 1
        """Turn an equality into two inequalities, using the property that u == v
        is the same as u <= v and u >= v. After that, put both in the standard form
        and add to the matrix."""
        idx = equation.index('==')

        # check if it's a bounding constraint. Ex: x == 0
        if '+' not in equation and '-' not in equation:
            eq1 = equation # create lower bound equation
            eq1[idx] = '>='
            self.get_constraint(eq1) # parse equation

            eq2 = equation # create upper bound equation
            eq2[idx] = '<='
            self.get_constraint(eq2) # parse equation

        # get right side of the inequation
        b = int(equation[idx + 1])

        # get coefficients and any literal on left hand side of constraint
        a, b_aux = self.parse_constraint(equation[:idx])
        b += b_aux # Ex: x1 + x2 + 3 <= 1

        # add new values to coefficient matrix
        self.__add_row(a)
        # add new constraint to constraint list
        self.b.append(b)


    def handle_free_var(self, var):
        """Separate free variables onto two bound variables."""
        # create new variable
        self.variables[var].sindex = self.var_count
        self.var_count += 1
        # create column for new variable
        col = [-a[self.variables[var].index] for a in self.A]
        # add column to matrix
        for (a, c) in zip(self.A, col):
            a.append(c)


    # TODO: está errado. Consertar.
    def parse_constraint(self, equation: list[str]):
        """Help parsing constraint equation."""
        a = [0 for i in range(self.var_count)] # coefficients
        b = 0 # constraint

        for i in range(len(equation)):
            if equation[i] == '+' or equation[i] == '-':
                continue
            # divide the expression into coefficient and variable
            coeff, var = self.__parse_expression(equation[i])
            if i > 0 and equation[i - 1] == '-':
                # treat cases of subtraction
                coeff = -coeff
            if not var:
                # coeff is a free number, so subtract it from constraint
                b -= coeff
                continue
            elif not var in self.variables:
                # add new variable to the dictionary
                self.__add_variable(var)
                a.append(0)
            # add coefficient to objective function
            a[self.variables[var].index] += coeff
        
        return [a, b]


    def __parse_expression(self, expression: list[str]): # 2*x1
        """Divide an expression into coefficient and variable."""
        if len(expression) == 1:
            # the coefficient equals one
            return [1, expression]

        # get name of var
        var_regex = re.compile('([*/]?)(-?[0-9]*[a-zA-Z]+[a-zA-Z0-9]*)([*/]?)')
        var = var_regex.search(expression).group(2)

        # substitute var name with '1' in expression
        f = lambda match : match.group(1) + '1' + match.group(3)
        expression = var_regex.sub(f, expression)

        # get coefficient value
        coeff = self.__calculate_coeff(expression)
        return [coeff, var]
    

    def __add_slack_var(self, coeff, a, b):
        """Helper for adding slack variable."""
        # add slack variable
        self.slack.append(self.var_count)
        self.var_count += 1
        a.append(coeff)

        # add new values to coefficient matrix
        self.__add_row(a)
        # add new constraint to constraint list
        self.b.append(b)


    def __add_row(self, row: list[int]):
        """Add new row to coefficient matrix."""
        if self.A:
            while len(self.A[0]) < len(row):
                for a in self.A:
                    a.append(0)
        self.A.append(row)
        return


    def __add_variable(self, var: str):
        """Add new variable to dictionary. Initially, also add it as a free variable."""
        self.variables[var] = Variable(self.var_count)
        self.var_count += 1
        self.free.append(var)


    # (x1 + x2) -> (-x1 - x2)
    def __transform_max_case(self, equation: list[str]):
        """Multiply equation by minus one."""
        new_equation = []
        if equation[0][0] != '-':
            equation[0] = '-'+equation[0]
        new_equation.append(equation[0])
        for word in equation[1:]:
            if word == '-':
                new_equation.append('+')
            elif word == '+':
                new_equation.append('-')
            else:
                new_equation.append(word)
        return new_equation


    # 2*3*5 -> 30
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
    

    def __test_result(self):
        """Print test."""
        print()
        print('--------------------------------------------')
        print('Resultado:')
        print('MIN ', self.objective)
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
        for i in range(len(self.A)):
            print(self.A[i], self.b[i])

class Variable():
    """Variable of a LP.
    
    Attributes:

    index  : int
        index of variable in the coefficient matrix.
    sindex : int
        index of substitution variable in the coefficient matrix (var = var' + var").
    m      : int
        value of the substitution var = var' + m.
    n      : int
        value of the substitution var = var' * n.
    """
    def __init__(self, _idx1: int, _idx2: int = -1):
        self.index = _idx1
        self.sindex = _idx2
    
    def get_value(self, objective: list[int]):
        if self.sindex != -1:
            return objective[self.index] + objective[self.sindex]
        return objective[self.index]