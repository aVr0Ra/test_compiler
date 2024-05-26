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

# 语法分析器和三地址代码生成器
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current_token_index = 0
        self.temp_count = 0
        self.label_count = 0
        self.code = []
        self.generated_labels = set()  # 用于跟踪已生成的标签

    def new_temp(self):
        self.temp_count += 1
        return f't{self.temp_count}'

    def new_label(self):
        self.label_count += 1
        return f'L{self.label_count}'

    def gen(self, code):
        self.code.append(code)

    def gen_unique(self, code):
        label = code.split(':')[0]
        if label not in self.generated_labels:  # 确保标签唯一
            self.code.append(code)
            self.generated_labels.add(label)

    def current_token(self):
        if self.current_token_index < len(self.tokens):
            return self.tokens[self.current_token_index]
        else:
            return None, None

    def next_token(self):
        self.current_token_index += 1

    def parse(self):
        while self.current_token_index < len(self.tokens):
            self.S()
        return self.code

    def S(self):
        token_type, token_value = self.current_token()
        print(f"Processing statement: {token_type}, {token_value}")  # 调试信息
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
                self.gen_unique(f'{C_true}:')
                self.S()
                self.gen(f'goto {S_next}')
                if self.current_token()[0] == 'ELSE':
                    self.next_token()
                    self.gen_unique(f'{C_false}:')
                    self.S()
                    self.gen_unique(f'{S_next}:')
                else:
                    self.gen_unique(f'{C_false}:')
                    self.gen_unique(f'{S_next}:')
            else:
                raise SyntaxError("Missing then")
        elif token_type == 'WHILE':
            self.next_token()
            S_begin = self.new_label()
            C_true = self.new_label()
            C_false = self.new_label()
            self.gen_unique(f'{S_begin}:')
            self.C(C_true, C_false)
            if self.current_token()[0] == 'DO':
                self.next_token()
                self.gen_unique(f'{C_true}:')
                self.S()
                self.gen(f'goto {S_begin}')
                self.gen_unique(f'{C_false}:')
            else:
                raise SyntaxError("Missing do")
        elif token_type == 'LPAREN':
            self.next_token()
            self.E()
            if self.current_token()[0] == 'RPAREN':
                self.next_token()
            else:
                raise SyntaxError("Missing closing parenthesis")
        elif token_type == 'END':
            self.next_token()
        else:
            raise SyntaxError(f"Invalid statement: {token_type} at index {self.current_token_index}")

    def C(self, true_label, false_label):
        E1_place = self.E()
        if self.current_token()[0] == 'COMPARE' or (self.current_token()[0] == 'ASSIGN' and self.current_token()[1] == '='):
            op = self.current_token()[1]
            self.next_token()
            E2_place = self.E()
            self.gen(f'if {E1_place} {op} {E2_place} goto {true_label}')
            self.gen(f'goto {false_label}')
        else:
            raise SyntaxError(f"Invalid comparison operator: {self.current_token()} at index {self.current_token_index}")

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

    # 语法分析和三地址代码生成
    parser = Parser(tokens)
    code = parser.parse()

    # 输出三地址代码
    print("Three Address Code:")
    for line in code:
        print(line)

if __name__ == "__main__":
    main()
