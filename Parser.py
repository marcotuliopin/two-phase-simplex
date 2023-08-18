from fractions import Fraction
import re


class Parser():
    """Reads the input LP for Simplex. Put the expressions in standard form while reading.

    Attributes:
        var_count : int
            number of variables in the LP. 
        is_max : bool
            check if it's a maximization LP.
        variables : dict[str, Variable]
            variables information. See Variable definition for more.
        slack : list[int]
            column index in coefficient matrix.
        optimal_value : int
            initial value of objective function.
        objective : list[int]
            coefficients of the objective function.
        A : list[list[int]]
            coefficient matrix of the constraints.
        s : list[list[int]]
            coefficient matrix of the slack variables.
        b : list[int]
            right-hand side values of the constraints.
    """
    def __init__(self):
        self.var_count = 0
        self.is_max = True
        self.variables = {}
        self.objective = []
        self.optimal_value = Fraction(0) 
        self.A = []
        self.b = []
        self.s = []
        self.free = []


    def parse_input(self, file_name):
        """Parses input data to create simplex input."""

        with open(file_name, 'r') as file:
            for line in file:
                if line.isspace(): # skip empty lines
                    continue
                equation =  line.split()
                match equation[0]:
                    case "MIN":
                        # get objective function when it's minimization
                        self.is_max = False
                        equation = self.__transform_max_case(equation[1:])
                        self.objective = self.get_objective_function(equation)
                    case 'MAX':
                        # get objective function when it's maximization
                        self.is_max = True
                        self.objective = self.get_objective_function(equation[1:])
                    case _:
                        # get constraint and add it to coefficient matrix and constraint vector
                        self.get_constraint(equation)
        
        if self.free:
            # handle any free variable
            for var in self.free:
                self.handle_free_var(var)
        self.free.clear()


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

            # the expression if it's a literal
            if not var:
                self.optimal_value += coeff
                i += j
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
        constraint = self.__get_constraint(equation[idx + 1:])
        if constraint < 0: # handle negative right-side of equation. Ex: x >= -3
            new_equation = self.__transform_max_case(equation[:idx])
            new_equation.append('<=')
            new_equation.extend(equation[idx + 2:])
            self.handle_less_equal(new_equation)
            return
        else:
            b = Fraction(constraint)

        # get coefficients and any literal on left hand side of constraint
        a, b_aux = self.parse_constraint(equation[:idx])
        b += b_aux # Ex: x1 + x2 + 3 >= 1

        # handle a bounding constraint. Ex: x >= l
        if len(equation[:idx]) < 2:
            # get coefficient and variable name
            coeff, var = self.__parse_expression(equation[0])
            # get right hand side of constraint
            constraint = Fraction(b, coeff) # Ex: 2*x >= 2 -> x >= 1
            # variable is bounded
            if constraint >= 0:
                self.free.remove(var)
                if constraint == 0: # x >= 0
                    return

        # add slack variable
        for row in self.s:
            row.append(0) 
        if not self.s:
            self.s.append([-1])
        else:
            new_row = [0 for i in range(len(self.s[0]) - 1)]
            new_row.append(-1)
            self.s.append(new_row)

        # add new values to coefficient matrix
        self.__add_row(a)
        # add new constraint to constraint list
        self.b.append(b)

        # self.__add_constraint_with_slack_var(-1, a, b)


    def handle_less_equal(self, equation: list[str]): # x1 + x2 <= 1
        """Put an upper bound inequality in the standard form and add it to the matrix."""
        idx = equation.index('<=')

        # get right hand side of constraint
        constraint = self.__get_constraint(equation[idx + 1:])

        # handle - x <= 0 
        if equation[0] == '-' and len(equation[:idx]) == 2:
            if str(constraint) == '0':
                new_equation = equation[1]
                new_equation.extend(['>=', str(constraint)])
                self.handle_greater_equal(new_equation)
                return

        if constraint < 0:
            new_equation = self.__transform_max_case(equation[:idx])
            new_equation.append('>=')
            new_equation.extend(equation[idx + 2:])
            self.handle_greater_equal(new_equation)
            return
        else:
            b = Fraction(constraint)

        # get coefficients and any literal on left hand side of constraint
        a, b_aux = self.parse_constraint(equation[:idx])
        b += b_aux # Ex: x1 + x2 + 3 <= 1

        # add slack variable
        for row in self.s:
            row.append(0) 
        if not self.s:
            self.s.append([1])
        else:
            new_row = [0 for i in range(len(self.s[0]) - 1)]
            new_row.append(1)
            self.s.append(new_row)

        # add new values to coefficient matrix
        self.__add_row(a)
        # add new constraint to constraint list
        self.b.append(b)

        # self.__add_constraint_with_slack_var(1, a, b)


    def handle_equality(self, equation: list[str]): # x1 + x2 == 1
        """Handles a equality constraint and put it in standard form."""
        idx = equation.index('==')

        # check if right hand side of constraint is negative
        constraint = self.__get_constraint(equation[idx + 1:])
        if constraint < 0:
            new_equation = self.__transform_max_case(equation[:idx])
            new_equation.append('==')
            new_equation.extend(equation[idx + 2:])
            equation = new_equation
            b = -constraint
        else:
            b = constraint

        idx = equation.index('==')

        # get right side of the inequation
        # get coefficients and any literal on left hand side of constraint
        a, b_aux = self.parse_constraint(equation[:idx])
        b += b_aux # Ex: x1 + x2 + 3 <= 1

        # add slack variable
        # for row in self.s:
        #     row.append(0) 
        if not self.s:
            self.s.append([0])
        else:
            new_col = [0 for i in range(len(self.s[0]) - 1)]
            new_col.append(0)
            self.s.append(new_col)

        # add new values to coefficient matrix
        self.__add_row(a)
        # add new constraint to constraint list
        self.b.append(b)


    def handle_free_var(self, var):
        """Separates free variables onto two bound variables."""
        # create new variable
        self.variables[var].sindex = self.var_count
        self.var_count += 1

        # create column for new variable
        col = [-a[self.variables[var].index] for a in self.A]
        # add column to matrix
        for (a, c) in zip(self.A, col):
            a.append(c)
        
        # add variable to the objective function
        val = -self.objective[self.variables[var].index]
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
                i += j
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
        var_regex = re.compile('([*/]?-?)([a-zA-ZÇç_]+[a-zA-ZÇç_0-9]*)([*/]?)')
        var = var_regex.search(expression)
        if var:
            var = var.group(2)

        # substitute var name with '1' in expression
        f = lambda match : match.group(1) + '1' + match.group(3)
        expression = var_regex.sub(f, expression)

        # get coefficient value
        coeff = self.__calculate_coeff(expression)
        return [coeff, var]


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

    
    def __get_constraint(self, equation: list[str]):
        sign = 0
        if (equation[0] == '-'):
            equation = equation[1:]
            sign = 1
        constraint, j = self.__get_expression(equation)
        constraint = self.__calculate_coeff(constraint)
        if sign:
            constraint = -constraint
        return constraint
    

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

    def __calculate_coeff(self, expression: str):
        """Calculates coefficient value."""
        expression = expression.replace('(', '')
        expression = expression.replace(')', '')
        symbols = re.split('([*/])', expression)
        coeff = Fraction(symbols[0])
        for i in range(1, len(symbols), 2):
            if symbols[i] == '*':
                coeff *= Fraction(symbols[i + 1])
            else:
                coeff /= Fraction(symbols[i + 1])
        return coeff


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
