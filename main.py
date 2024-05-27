import subprocess


def run_lexer():
    try:
        # 编译lab1.c
        compile_result = subprocess.run(['gcc', 'lab1.c', '-o', 'lab1'], check=True, timeout=30)
        print("Compilation succeeded.")

        # 运行编译生成的可执行文件
        run_result = subprocess.run(['./lab1'], check=True, timeout=30)
        print("Execution succeeded.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred during compilation or execution: {e}")
    except subprocess.TimeoutExpired:
        print("Compilation or execution timed out.")

def read_lab1_output():
    # 读取lab1_output.txt文件的内容
    with open('lab1_output.txt', 'r') as file:
        return file.read()


def lexer(input_code):
    tokens = []
    for line in input_code.strip().split('\n'):
        parts = line.strip().split()
        if len(parts) == 3:
            token_type = parts[1]
            token_value = parts[2]
            if token_type.startswith('INT'):
                token_value = int(token_value)
                token_type = 'NUMBER'
            elif token_type == 'REAL10' or token_type == 'REAL16':
                token_value = float(token_value)
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

            tokens.append((token_type, token_value))
    return tokens


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current_token_index = 0
        self.temp_count = 0
        self.label_count = 0
        self.code = []
        self.generated_labels = set()

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
        if label not in self.generated_labels:
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
            print(f"Current Token: {self.current_token()}")
            self.S()
        return self.code

    def S(self):
        token_type, token_value = self.current_token()
        print(f"Processing statement: {token_type}, {token_value}")
        if token_type == 'ID':
            id_place = token_value
            self.next_token()
            if self.current_token()[0] == 'ASSIGN':
                self.next_token()
                E_place = self.E()
                self.gen(f'{id_place} := {E_place}')
            elif self.current_token()[0] == 'SEMIC':
                self.next_token()
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
        if self.current_token()[0] in ['COMPARE', 'ASSIGN']:
            op = self.current_token()[1]
            self.next_token()
            E2_place = self.E()
            self.gen(f'if {E1_place} {op} {E2_place} goto {true_label}')
            self.gen(f'goto {false_label}')
        else:
            raise SyntaxError(
                f"Invalid comparison operator: {self.current_token()} at index {self.current_token_index}")

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
        elif token_type in ['ID', 'NUMBER']:
            self.next_token()
            return token_value
        else:
            raise SyntaxError(f"Invalid factor: {self.current_token()} at index {self.current_token_index}")
def process_three_address_code(tac):
    # 如果 tac 是列表，将其转换为字符串
    if isinstance(tac, list):
        tac = '\n'.join(tac)

    # 继续处理代码
    lines = tac.strip().split('\n')

    # 存储原始标签到新标签的映射
    label_map = {}
    new_lines = []
    previous_label = None

    # 第一次遍历，移除冗余标签
    for line in lines:
        stripped = line.strip()

        if stripped.endswith(':'):
            label = stripped[:-1]
            if previous_label is not None:
                # 发现连续的两个标签，将当前标签映射到之前的标签
                label_map[label] = previous_label
                #print(f"Removing redundant label: {label}")
            else:
                new_lines.append(line)
                previous_label = label  # 更新之前的标签
        else:
            # 遇到非标签行，重置之前的标签
            previous_label = None
            new_lines.append(line)

    # 第二次遍历，处理标签后面跟随的`goto`语句
    i = 0
    while i < len(new_lines) - 1:
        current_line = new_lines[i].strip()
        next_line = new_lines[i + 1].strip()

        if current_line.endswith(':') and next_line.startswith('goto'):
            label = current_line[:-1]
            target_label = next_line.split()[-1]

            # 添加映射
            label_map[label] = target_label
            #print(f"Replacing goto {label} with goto {target_label} and removing {label}: and {next_line}")

            # 移除当前标签和接下来的`goto`语句
            new_lines.pop(i)
            new_lines.pop(i)
        else:
            i += 1

    # 解析标签映射的函数
    def resolve_label(label):
        seen_labels = set()
        while label in label_map and label not in seen_labels:
            seen_labels.add(label)
            label = label_map[label]
        return label

    # 最后一次遍历，根据标签映射调整`goto`语句
    final_lines = []
    for line in new_lines:
        if 'goto' in line:
            parts = line.split()
            label = resolve_label(parts[-1])
            final_lines.append(' '.join(parts[:-1]) + ' ' + label)
        else:
            final_lines.append(line)

    # 在最终的行中识别所有剩余的标签
    labels = set()
    for line in final_lines:
        stripped = line.strip()
        if stripped.endswith(':'):
            labels.add(stripped[:-1])

    # 创建唯一的标签的排序列表
    sorted_labels = sorted(labels)
    new_label_mapping = {label: f"L{i+1}" for i, label in enumerate(sorted_labels)}

    # 最后一遍遍历，用连续的标签替换原有标签
    final_lines_sequential = []
    for line in final_lines:
        if line.strip().endswith(':'):
            label = line.strip()[:-1]
            final_lines_sequential.append(new_label_mapping[label] + ':')
        elif 'goto' in line:
            parts = line.split()
            label = parts[-1]
            final_lines_sequential.append('\t' + ' '.join(parts[:-1]) + ' ' + new_label_mapping[label])
        else:
            final_lines_sequential.append('\t' + line)  # 非标签行前面加一个tab

    return '\n'.join(final_lines_sequential)

def analyze_and_generate_code(tokens):
    if not tokens:
        with open('output.txt', 'w') as file:
            file.write("No tokens found. Please check the input file.\n")
        return

    # 输出词法分析结果
    with open('output.txt', 'w') as file:
        file.write("Tokens:\n")
        for token in tokens:
            file.write(f"{token}\n")

    # 语法分析和三地址代码生成
    parser = Parser(tokens)
    code = parser.parse()

    # 输出三地址代码
    with open('output.txt', 'a') as file:
        file.write("Three Address Code:\n")
        for line in code:
            file.write(f"{line}\n")

        file.write("\n\n\nProcessed Code:\n")
        processed_code = process_three_address_code(code)
        file.write(f"{processed_code}\n")

def main():
    # 运行lab1.exe
    run_lexer()

    # 读取lab1_output.txt文件的内容
    input_code = read_lab1_output()

    # 词法分析
    tokens = lexer(input_code)

    analyze_and_generate_code(tokens)


if __name__ == "__main__":
    main()