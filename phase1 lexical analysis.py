import re

class LexicalAnalyzer:
    def __init__(self):
        self.Arithmetic_Operators = {'+', '-', '*', '/'}
        self.Relational_Operators = {'==', '>=', '<=', '!=', '>', '<'}
        self.Logical_Operators = {'AND', 'OR', 'NOT'}
        self.Compound_Assignment_Operators = {'+=', '-=', '*=', '/='}
        self.Assignment_Operators = {'='}
        self.Crement_Operators = {'++', '--'}
        self.special_characters = {"(", ")", ",", "[", "]"}
        self.keywords = {
            "LET", "IF", "THEN", "ELSE", "ENDIF", "WHILE", "DO", "ENDWHILE",
            "FOR", "TO", "STEP", "ENDFOR", "FUNC", "BEGIN", "RETURN", "END",
            "CALL", "REPEAT", "UNTIL", "IN"
        }
        # Combine all operators into one set
        self.operators = (
            self.Arithmetic_Operators
            | self.Relational_Operators
            | self.Logical_Operators
            | self.Compound_Assignment_Operators
            | self.Crement_Operators
            | self.Assignment_Operators
        )
        self.symbol_table = {}
        self.tokens = []

    def tokenize(self, source_code):
        lines = source_code.split("\n")
        for line_num, line in enumerate(lines, start=1):
            line = line.strip()
            i = 0
            while i < len(line):
                char = line[i]

                # Skip whitespace
                if char.isspace():
                    i += 1
                    continue

                # Handle comments
                if char == "{":
                    comment_end = line.find("}", i)
                    if comment_end == -1:
                        raise SyntaxError(f"Unclosed comment starting at line {line_num}, position {i}")
                    i = comment_end + 1
                    continue

                # Handle string literals (single quotes)
                if char == "'":
                    string_start = i
                    i += 1
                    while i < len(line) and line[i] != "'":
                        i += 1
                    if i >= len(line):
                        raise SyntaxError(f"Unmatched quote starting at line {line_num}, position {string_start}")
                    string_value = line[string_start + 1:i]
                    self.tokens.append(("string", string_value))
                    i += 1
                    continue

                # Handle numbers
                if char.isdigit():
                    number_start = i
                    while i < len(line) and (line[i].isdigit() or line[i] == "."):
                        i += 1
                    number_value = line[number_start:i]
                    self.tokens.append(("number", number_value))
                    continue

                # Handle identifiers and keywords
                if char.isalpha() or char == "_":
                    identifier_start = i
                    while i < len(line) and (line[i].isalnum() or line[i] == "_"):
                        i += 1
                    identifier = line[identifier_start:i]
                    identifier_upper = identifier.upper()

                    # Distinguish between keywords, logical operators, and identifiers
                    if identifier_upper in self.keywords:
                        self.tokens.append(("keyword", identifier_upper))
                    elif identifier_upper in self.Logical_Operators:
                        self.tokens.append(("Logical Operator", identifier_upper))
                    else:
                        # Detect function calls or variable declarations
                        if self.tokens and self.tokens[-1][1] == "CALL":
                            # Add as a function call
                            params_start = line.find("(", i)
                            if params_start != -1:
                                params_end = line.find(")", params_start)
                                if params_end != -1:
                                    params = line[params_start + 1:params_end].split(",")
                                    params = [p.strip() for p in params if p.strip()]
                                    self.symbol_table[identifier] = {"type": "function", "parameters": params}
                                    i = params_end + 1
                                else:
                                    raise SyntaxError(f"Unclosed parentheses for function call at line {line_num}")
                            else:
                                self.symbol_table[identifier] = {"type": "function", "parameters": []}
                        else:
                            # Add as a variable
                            if identifier not in self.symbol_table:
                                self.symbol_table[identifier] = {"type": "unknown"}

                        self.tokens.append(("identifier", identifier))
                    continue

                # Handle operators
                for op in sorted(self.operators, key=len, reverse=True):
                    if line.startswith(op, i):
                        operator_type = self._get_operator_type(op)
                        self.tokens.append((operator_type, op))
                        i += len(op)
                        break
                else:
                    # Handle special characters
                    if char in self.special_characters:
                        self.tokens.append(("special", char))
                        i += 1
                    else:
                        # Invalid character
                        raise ValueError(f"Invalid character '{char}' at line {line_num}, position {i}")

        # Update symbol table types based on LET assignments
        self._infer_variable_types()

        return self.tokens

    def _get_operator_type(self, operator):
        if operator in self.Arithmetic_Operators:
            return "Arithmetic Operator"
        elif operator in self.Relational_Operators:
            return "Relational Operator"
        elif operator in self.Logical_Operators:
            return "Logical Operator"
        elif operator in self.Compound_Assignment_Operators:
            return "Compound Assignment Operator"
        elif operator in self.Crement_Operators:
            return "Crement Operator"
        elif operator in self.Assignment_Operators:
            return "Assignment Operator"  # Added handling for '='
        return "Unknown Operator"

    def _infer_variable_types(self):
        # Infer types from LET assignments and expressions
        for i, token in enumerate(self.tokens):
            if token[1] == "LET" and i + 2 < len(self.tokens):
                identifier_token = self.tokens[i + 1]
                assignment_operator = self.tokens[i + 2]
                if (
                    identifier_token[0] == "identifier" 
                    and assignment_operator[1] == "="
                ):
                    value_token = self.tokens[i + 3] if i + 3 < len(self.tokens) else None
                    if value_token:
                        if value_token[0] == "number":
                            self.symbol_table[identifier_token[1]]["type"] = "integer"
                        elif value_token[0] == "string":
                            self.symbol_table[identifier_token[1]]["type"] = "string"
                        elif value_token[0] == "identifier":
                            var_name = value_token[1]
                            if var_name in self.symbol_table:
                                # Copy the type of the variable
                                self.symbol_table[identifier_token[1]]["type"] = self.symbol_table[var_name]["type"]
                        elif value_token[0] == "Arithmetic Operator":
                            # Arithmetic operations return integers by default
                            self.symbol_table[identifier_token[1]]["type"] = "integer"

    def display_tokens(self):
        for token in self.tokens:
            print(f"Token: {token[0]}, Lexeme: {token[1]}")

    def display_symbol_table(self):
        print("\nSymbol Table:")
        for name, info in self.symbol_table.items():
            type_info = info["type"]
            if type_info == "function":
                if len(info["parameters"]) == 0:
                    params = "with no parameters"
                else:
                    params = f"with parameters: {', '.join(info['parameters'])}"
                print(f"Name: {name}, Type: {type_info} ({params})")
            else:
                print(f"Name: {name}, Type: {type_info}")


# Example source code
source_code = """
LET name = 'muhammed'
LET a = 5 
LET b = 10 
LET z = 2
IF a == b OR a > z
THEN  
LET c = a + b 
LET d = c * 2 
a++
ELSE 
LET e = a - b 
z+=a
ENDIF 
CALL myFunction(a, b) 
CALL Help
"""

# Instantiate and tokenize
lexer = LexicalAnalyzer()
try:
    lexer.tokenize(source_code)
    lexer.display_tokens()
    lexer.display_symbol_table()
except (SyntaxError, ValueError) as e:
    print(f"Error: {e}")
