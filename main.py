import re

# 词法分析器
def lexer(input_code):
    tokens = []
    token_specification = [
        ('NUMBER',   r'\b\d+(\.\d*)?\b'),   # 整数或小数
        ('ASSIGN',   r'='),                 # 赋值运算符
        ('END',      r';'),                 # 语句结束符
        ('ID',       r'\b[a-zA-Z_][a-zA-Z_0-9]*\b'),  # 标识符
        ('OP',       r'[+\-*/]'),           # 运算符
        ('COMPARE',  r'[<>]'),              # 比较运算符
        ('LPAREN',   r'\('),                # 左括号
        ('RPAREN',   r'\)'),                # 右括号
        ('LBRACE',   r'\{'),                # 左大括号
        ('RBRACE',   r'\}'),                # 右大括号
        ('WHILE',    r'\bwhile\b'),         # 关键字 while
        ('IF',       r'\bif\b'),            # 关键字 if
        ('THEN',     r'\bthen\b'),          # 关键字 then
        ('ELSE',     r'\belse\b'),          # 关键字 else
        ('DO',       r'\bdo\b'),            # 关键字 do
        ('HEX',      r'0x[0-9a-fA-F]+'),    # 十六进制整数
        ('SKIP',     r'[ \t]+'),            # 跳过空白字符
        ('MISMATCH', r'.'),                 # 其他不匹配字符
    ]
    tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)
    for mo in re.finditer(tok_regex, input_code):
        kind = mo.lastgroup
        value = mo.group(kind)
        if kind == 'NUMBER':
            value = float(value) if '.' in value else int(value)
        elif kind == 'ID' and value in ('while', 'if', 'then', 'else', 'do'):
            kind = value.upper()
        elif kind == 'SKIP':
            continue
        elif kind == 'MISMATCH':
            raise RuntimeError(f'{value!r} unexpected on line 1')
        tokens.append((kind, value))
    return tokens

# 语法分析器和三地址代码生成器
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current_token_index = 0
        self.temp_count = 0
        self.label_count = 0
        self.code = []

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
            return None, None

    def next_token(self):
        self.current_token_index += 1

    def parse(self):
        while self.current_token_index < len(self.tokens):
            self.L()
        return self.code

    def L(self):
        if self.current_token_index < len(self.tokens):
            self.S()
            if self.current_token()[0] == 'END':
                self.next_token()
            else:
                raise SyntaxError("Missing semicolon")

    def S(self):
        token_type, token_value = self.current_token()
        if token_type == 'ID':
            id_place = token_value
            self.next_token()
            if self.current_token()[0] == 'ASSIGN':
                self.next_token()
                E_place = self.E()
                self.gen(f'{id_place} := {E_place}')
        elif token_type == 'IF':
            self.next_token()
            C_true = self.new_label()
            C_false = self.new_label()
            S_next = self.new_label()
            self.C(C_true, C_false)
            if self.current_token()[0] == 'THEN':
                self.next_token()
                self.gen(f'{C_true}:')
                self.S()
                self.gen(f'goto {S_next}')
                if self.current_token()[0] == 'ELSE':
                    self.next_token()
                    self.gen(f'{C_false}:')
                    self.S()
                    self.gen(f'{S_next}:')
                else:
                    self.gen(f'{C_false}:')
                    self.gen(f'{S_next}:')
            else:
                raise SyntaxError("Missing then")
        elif token_type == 'WHILE':
            self.next_token()
            S_begin = self.new_label()
            C_true = self.new_label()
            C_false = self.new_label()
            self.gen(f'{S_begin}:')
            self.C(C_true, C_false)
            if self.current_token()[0] == 'DO':
                self.next_token()
                self.gen(f'{C_true}:')
                self.S()
                self.gen(f'goto {S_begin}')
                self.gen(f'{C_false}:')
            else:
                raise SyntaxError("Missing do")
        elif token_type == 'LBRACE':
            self.next_token()
            self.P()
            if self.current_token()[0] == 'RBRACE':
                self.next_token()
            else:
                raise SyntaxError("Missing closing brace")
        else:
            raise SyntaxError("Invalid statement")

    def C(self, true_label, false_label):
        E1_place = self.E()
        if self.current_token()[0] == 'COMPARE' or (self.current_token()[0] == 'ASSIGN' and self.current_token()[1] == '='):
            op = self.current_token()[1]
            self.next_token()
            E2_place = self.E()
            self.gen(f'if {E1_place} {op} {E2_place} goto {true_label}')
            self.gen(f'goto {false_label}')
        else:
            raise SyntaxError(f"Invalid comparison operator: {self.current_token()}")

    def E(self):
        T_place = self.T()
        while self.current_token()[0] == 'OP' and self.current_token()[1] in ['+', '-']:
            op = self.current_token()[1]
            self.next_token()
            T1_place = self.T()
            E_place = self.new_temp()
            self.gen(f'{E_place} := {T_place} {op} {T1_place}')
            T_place = E_place
        return T_place

    def T(self):
        F_place = self.F()
        while self.current_token()[0] == 'OP' and self.current_token()[1] in ['*', '/']:
            op = self.current_token()[1]
            self.next_token()
            F1_place = self.F()
            T_place = self.new_temp()
            self.gen(f'{T_place} := {F_place} {op} {F1_place}')
            F_place = T_place
        return F_place

    def F(self):
        token_type, token_value = self.current_token()
        if token_type == 'LPAREN':
            self.next_token()
            E_place = self.E()
            if self.current_token()[0] == 'RPAREN':
                self.next_token()
                return E_place
            else:
                raise SyntaxError("Missing closing parenthesis")
        elif token_type in ['ID', 'NUMBER', 'HEX']:
            self.next_token()
            return token_value
        else:
            raise SyntaxError(f"Invalid factor: {self.current_token()}")

# 主函数
def main():
    # 读取输入文件
    with open('input.txt', 'r') as file:
        input_code = file.read()

    # 词法分析
    tokens = lexer(input_code)

    # 输出词法分析结果
    print("Tokens:")
    for token in tokens:
        print(token)

    # 语法分析和三地址代码生成
    parser = Parser(tokens)
    code = parser.parse()

    # 输出三地址代码
    print("Three Address Code:")
    for line in code:
        print(line)

if __name__ == "__main__":
    main()
