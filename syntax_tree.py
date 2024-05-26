import re

# 词法分析器
def lexer(input_code):
    tokens = []
    for line in input_code.strip().split('\n'):  # 逐行读取输入代码
        parts = line.strip().split()  # 分割每行的内容
        if len(parts) == 3:
            token_type = parts[1]
            token_value = parts[2]
            # 根据不同类型的标记进行处理
            if token_type.startswith('INT'):
                token_value = int(token_value)
                token_type = 'NUMBER'
            elif token_type == 'IDN':
                token_type = 'ID'
            elif token_type == 'PLUS':
                token_value = '+'
                token_type = 'OP'
            elif token_type == 'MINUS':
                token_value = '-'
                token_type = 'OP'
            elif token_type == 'MULTI':
                token_value = '*'
                token_type = 'OP'
            elif token_type == 'RDIV':
                token_value = '/'
                token_type = 'OP'
            elif token_type == 'GT':
                token_value = '>'
                token_type = 'COMPARE'
            elif token_type == 'LT':
                token_value = '<'
                token_type = 'COMPARE'
            elif token_type == 'EQ':
                token_value = '='
                token_type = 'ASSIGN'
            elif token_type == 'SEMIC':
                token_value = ';'
                token_type = 'END'
            elif token_type == 'WHILE':
                token_value = 'while'
                token_type = 'WHILE'
            elif token_type == 'IF':
                token_value = 'if'
                token_type = 'IF'
            elif token_type == 'THEN':
                token_value = 'then'
                token_type = 'THEN'
            elif token_type == 'ELSE':
                token_value = 'else'
                token_type = 'ELSE'
            elif token_type == 'DO':
                token_value = 'do'
                token_type = 'DO'
            elif token_type == 'LR_BRAC':
                token_value = '('
                token_type = 'LPAREN'
            elif token_type == 'RR_BRAC':
                token_value = ')'
                token_type = 'RPAREN'
            tokens.append((token_type, token_value))  # 添加处理后的标记到列表中
    return tokens

# 语法树节点类
class ASTNode:
    def __init__(self, token_type, token_value):
        self.token_type = token_type
        self.token_value = token_value
        self.children = []

    def add_child(self, node):
        self.children.append(node)

    def __repr__(self, level=0):
        ret = "\t" * level + repr((self.token_type, self.token_value)) + "\n"
        for child in self.children:
            ret += child.__repr__(level + 1)
        return ret

# 语法分析器
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current_token_index = 0

    def current_token(self):
        if self.current_token_index < len(self.tokens):
            return self.tokens[self.current_token_index]
        else:
            return None, None

    def next_token(self):
        self.current_token_index += 1

    def parse(self):
        self.ast = self.S()
        return self.ast

    def S(self):
        token_type, token_value = self.current_token()
        node = ASTNode(token_type, token_value)
        print(f"Processing statement: {token_type}, {token_value}")  # 调试信息
        if token_type == 'ID':
            id_place = token_value
            self.next_token()
            if self.current_token()[0] == 'ASSIGN':
                node.add_child(ASTNode('ASSIGN', '='))
                self.next_token()
                E_place = self.E()
                node.add_child(E_place)
        elif token_type == 'IF':
            self.next_token()
            node.add_child(ASTNode('IF', 'if'))
            condition_node = self.C()
            node.add_child(condition_node)
            if self.current_token()[0] == 'THEN':
                self.next_token()
                then_node = ASTNode('THEN', 'then')
                node.add_child(then_node)
                then_node.add_child(self.S())
                if self.current_token()[0] == 'ELSE':
                    self.next_token()
                    else_node = ASTNode('ELSE', 'else')
                    node.add_child(else_node)
                    else_node.add_child(self.S())
            else:
                raise SyntaxError("Missing then")
        elif token_type == 'WHILE':
            self.next_token()
            node.add_child(ASTNode('WHILE', 'while'))
            condition_node = self.C()
            node.add_child(condition_node)
            if self.current_token()[0] == 'DO':
                self.next_token()
                do_node = ASTNode('DO', 'do')
                node.add_child(do_node)
                do_node.add_child(self.S())
            else:
                raise SyntaxError("Missing do")
        elif token_type == 'LPAREN':
            self.next_token()
            expr_node = self.E()
            node.add_child(expr_node)
            if self.current_token()[0] == 'RPAREN':
                self.next_token()
            else:
                raise SyntaxError("Missing closing parenthesis")
        elif token_type == 'END':
            self.next_token()
        else:
            raise SyntaxError(f"Invalid statement: {token_type} at index {self.current_token_index}")
        return node

    def C(self):
        E1_place = self.E()
        condition_node = ASTNode('CONDITION', 'condition')
        condition_node.add_child(E1_place)
        if self.current_token()[0] == 'COMPARE' or (self.current_token()[0] == 'ASSIGN' and self.current_token()[1] == '='):
            op = self.current_token()[1]
            self.next_token()
            E2_place = self.E()
            condition_node.add_child(ASTNode('OP', op))
            condition_node.add_child(E2_place)
        else:
            raise SyntaxError(f"Invalid comparison operator: {self.current_token()} at index {self.current_token_index}")
        return condition_node

    def E(self):
        T_place = self.T()
        expr_node = T_place
        while self.current_token()[0] == 'OP' and self.current_token()[1] in ['+', '-']:
            op = self.current_token()[1]
            self.next_token()
            T1_place = self.T()
            expr_node = ASTNode('EXPR', 'expr')
            expr_node.add_child(T_place)
            expr_node.add_child(ASTNode('OP', op))
            expr_node.add_child(T1_place)
            T_place = expr_node
        return expr_node

    def T(self):
        F_place = self.F()
        term_node = F_place
        while self.current_token()[0] == 'OP' and self.current_token()[1] in ['*', '/']:
            op = self.current_token()[1]
            self.next_token()
            F1_place = self.F()
            term_node = ASTNode('TERM', 'term')
            term_node.add_child(F_place)
            term_node.add_child(ASTNode('OP', op))
            term_node.add_child(F1_place)
            F_place = term_node
        return term_node

    def F(self):
        token_type, token_value = self.current_token()
        node = ASTNode(token_type, token_value)
        if token_type == 'LPAREN':
            self.next_token()
            expr_node = self.E()
            node.add_child(expr_node)
            if self.current_token()[0] == 'RPAREN':
                self.next_token()
                return node
            else:
                raise SyntaxError("Missing closing parenthesis")
        elif token_type in ['ID', 'NUMBER', 'HEX']:
            self.next_token()
            return node
        else:
            raise SyntaxError(f"Invalid factor: {self.current_token()} at index {self.current_token_index}")

# 主函数
def main():
    # 读取输入文件
    with open('lab1_output.txt', 'r') as file:
        input_code = file.read()

    # 词法分析
    tokens = lexer(input_code)

    # 输出词法分析结果
    print("Tokens:")
    for token in tokens:
        print(token)

    # 语法分析
    parser = Parser(tokens)
    ast = parser.parse()

    # 输出语法树
    print("Syntax Tree:")
    print(ast)

if __name__ == "__main__":
    main()
