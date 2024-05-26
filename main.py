import re

class Token:
    def __init__(self, token_type, value):
        self.token_type = token_type
        self.value = value

    def __repr__(self):
        return f'Token({self.token_type}, {self.value})'

def read_tokens_from_file(file_path):
    tokens = []
    with open(file_path, 'r') as file:
        for line in file:
            parts = line.split()
            if len(parts) >= 3:
                token_type = parts[1]
                value = parts[2] if parts[2] != '-' else None
                tokens.append(Token(token_type, value))
    return tokens

class Node:
    def __init__(self, token):
        self.token = token
        self.children = []

    def add_child(self, child):
        self.children.append(child)

    def __repr__(self):
        return f'Node({self.token}, {self.children})'

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current_token_index = 0
        self.temp_count = 0
        self.label_count = 0
        self.code = []
        self.root = None

    def new_temp(self):
        self.temp_count += 1
        return f't{self.temp_count}'

    def new_label(self):
        self.label_count += 1
        return f'L{self.label_count}'

    def gen(self, code):
        self.code.append(code)

    def current_token(self):
        if self.current_token_index < len(self.tokens):
            return self.tokens[self.current_token_index]
        else:
            return None

    def next_token(self):
        self.current_token_index += 1

    def parse(self):
        self.root = self.L()
        return self.root

    def L(self):
        node = Node(Token('L', None))
        while self.current_token() is not None:
            stmt_node = self.S()
            if stmt_node:
                node.add_child(stmt_node)
            if self.current_token() and self.current_token().token_type == 'SEMIC':
                self.next_token()
        return node

    def S(self):
        token = self.current_token()
        if token is None:
            raise SyntaxError("Unexpected end of input")

        print(f"Parsing statement: {token}")  # 调试信息

        node = Node(token)
        if token.token_type == 'ID':
            self.next_token()
            if self.current_token() and self.current_token().token_type == 'EQ':
                node.add_child(Node(self.current_token()))
                self.next_token()
                node.add_child(self.E())
        elif token.token_type == 'IF':
            self.next_token()
            node.add_child(self.C())
            if self.current_token() and self.current_token().token_type == 'THEN':
                node.add_child(Node(self.current_token()))
                self.next_token()
                node.add_child(self.S())
                if self.current_token() and self.current_token().token_type == 'ELSE':
                    node.add_child(Node(self.current_token()))
                    self.next_token()
                    node.add_child(self.S())
        elif token.token_type == 'WHILE':
            self.next_token()
            node.add_child(self.C())
            if self.current_token() and self.current_token().token_type == 'DO':
                node.add_child(Node(self.current_token()))
                self.next_token()
                node.add_child(self.S())
        elif token.token_type in ['INT10', 'INT16', 'ID', 'NUMBER', 'HEX']:
            self.next_token()
            return node
        else:
            self.next_token()  # 跳过无效或意外的 token
            return None
        return node

    def C(self):
        node = Node(Token('C', None))
        node.add_child(self.E())
        if self.current_token() and self.current_token().token_type in ['GT', 'LT', 'EQ']:
            node.add_child(Node(self.current_token()))
            self.next_token()
            node.add_child(self.E())
        else:
            raise SyntaxError(f"Invalid comparison operator: {self.current_token()}")
        return node

    def E(self):
        node = Node(Token('E', None))
        node.add_child(self.T())
        while self.current_token() and self.current_token().token_type in ['PLUS', 'MINUS']:
            op_node = Node(self.current_token())
            self.next_token()
            op_node.add_child(node)
            op_node.add_child(self.T())
            node = op_node
        return node

    def T(self):
        node = Node(Token('T', None))
        node.add_child(self.F())
        while self.current_token() and self.current_token().token_type in ['MULTI', 'DIV']:
            op_node = Node(self.current_token())
            self.next_token()
            op_node.add_child(node)
            op_node.add_child(self.F())
            node = op_node
        return node

    def F(self):
        token = self.current_token()
        node = Node(token)
        if token.token_type == 'LPAREN':
            self.next_token()
            node.add_child(self.E())
            if self.current_token() and self.current_token().token_type == 'RPAREN':
                self.next_token()
            else:
                raise SyntaxError("Missing closing parenthesis")
        elif token.token_type in ['ID', 'NUMBER', 'HEX', 'INT10', 'INT16']:
            self.next_token()
        else:
            raise SyntaxError(f"Invalid factor: {self.current_token()}")
        return node

    def generate_three_address_code(self, node):
        if node.token.token_type == 'L':
            for child in node.children:
                self.generate_three_address_code(child)
        elif node.token.token_type == 'ID' and len(node.children) > 1 and node.children[0].token.token_type == 'EQ':
            id_node = node
            expr_node = node.children[1]
            self.generate_three_address_code(expr_node)
            self.gen(f"{id_node.token.value} := {expr_node.token.value}")
        elif node.token.token_type == 'C':
            expr1_node = node.children[0]
            comp_node = node.children[1]
            expr2_node = node.children[2]
            self.generate_three_address_code(expr1_node)
            self.generate_three_address_code(expr2_node)
            temp = self.new_temp()
            self.gen(f"{temp} := {expr1_node.token.value} {comp_node.token.value} {expr2_node.token.value}")
            node.token.value = temp
        elif node.token.token_type == 'E':
            if len(node.children) == 1:
                self.generate_three_address_code(node.children[0])
                node.token.value = node.children[0].token.value
            else:
                expr1_node = node.children[0]
                op_node = node.children[1]
                expr2_node = node.children[2]
                self.generate_three_address_code(expr1_node)
                self.generate_three_address_code(expr2_node)
                temp = self.new_temp()
                self.gen(f"{temp} := {expr1_node.token.value} {op_node.token.value.lower()} {expr2_node.token.value}")
                node.token.value = temp
        elif node.token.token_type == 'T':
            if len(node.children) == 1:
                self.generate_three_address_code(node.children[0])
                node.token.value = node.children[0].token.value
            else:
                term1_node = node.children[0]
                op_node = node.children[1]
                term2_node = node.children[2]
                self.generate_three_address_code(term1_node)
                self.generate_three_address_code(term2_node)
                temp = self.new_temp()
                self.gen(f"{temp} := {term1_node.token.value} {op_node.token.value.lower()} {term2_node.token.value}")
                node.token.value = temp
        elif node.token.token_type == 'F':
            if len(node.children) == 1:
                node.token.value = node.children[0].token.value

    def get_code(self):
        return self.code

def print_tree(node, level=0):
    if node is not None:
        print('  ' * level + repr(node.token))
        for child in node.children:
            print_tree(child, level + 1)

def main():
    tokens = read_tokens_from_file('lab1_output.txt')

    print("Tokens:")
    for token in tokens:
        print(token)

    parser = Parser(tokens)
    try:
        syntax_tree = parser.parse()

        print("Syntax Tree:")
        print_tree(syntax_tree)

        parser.generate_three_address_code(syntax_tree)

        print("\nThree Address Code:")
        for line in parser.get_code():
            print(line)
    except SyntaxError as e:
        print(f"SyntaxError: {e}")

if __name__ == "__main__":
    main()
