from typing import SupportsIndex, Optional, Mapping

import argparse
import tabulate

memory = 2**12 * [0]

class Label:
    def __init__(self, name, address, size):
        self.name = name
        self.address = address
        self.size = size
    
    def get_address(self):
        return self.address
    
    def get_buffer(self):
        return memory[self.address : self.address + self.size]


class Program:
    labels: Mapping[str, Label]
    
    def __init__(self):
        self.clear()
    
    def clear(self):
        self.source = []
        self.labels = {}
        self.codemap = {}

p = Program()


class constant:
    def __init__(self, x):
        self.x = [x]
    
    def get_value(self):
        return self.read(0)
    
    def read(self, offset):
        return self.x[offset]


class pointer:
    def __init__(self, addr):
        self.p = addr
    
    def get_value(self):
        return self.p
    
    def read(self, offset):
        return memory[self.p + offset]
    
    def write(self, offset, x):
        memory[self.p + offset] = x


def get_nibble(x, nibble):
    return (x >> (4 * nibble)) % 16


def split_fields(s: str,
                 sep: Optional[str] = None,
                 maxsplit: SupportsIndex = -1):
    return [i.strip().lower() for i in s.split(sep,maxsplit) if i]


def consume_directive(s: str):
    if s.startswith('.'):
        return split_fields(s, maxsplit=1)
    return '', s


def parse(source: str):
    p.clear()
    
    address = 0
    
    def pad(alignment, offset=0):
        nonlocal address
        while (address % alignment) != (offset % alignment):
            memory[address] = '-'
            address += 1

    alignment = 1
    for line_index, line_text in enumerate(source.splitlines()):
        p.source.append(line_text)

        try:
            line_text, _ = line_text.split(';', maxsplit=1)
        except ValueError:
            pass

        i = line_text.find(':')
        if i != -1:
            label = line_text[:i].strip()
            instruction = line_text[i+1:].strip()
        else:
            label = None
            instruction = line_text.strip()

        directive, instruction = consume_directive(instruction)
        if directive == '.align':
            alignment = int(instruction)
            instruction = ''
            directive = ''
        elif directive == '.alias':
            alias, target = split_fields(instruction, maxsplit=1)
            target, offset = split_fields(target, '+')
            p.labels[alias] = Label(alias, p.labels[target].get_address() + int(offset), 0)
            directive = ''

        if label:
            pad(alignment, -1)
            memory[address] = f'!{label}'
            p.codemap[address] = line_index
            address += 1

            label_address = address
            if directive.startswith('.@'):
                target_label = instruction
                target_addr = p.labels[target_label].get_address()
                pad(alignment)
                memory[address] = get_nibble(target_addr, 0)
                memory[address + 1] = get_nibble(target_addr, 1)
                memory[address + 2] = get_nibble(target_addr, 2)
                address += 3
                instruction = ''
                directive = ''
            elif directive == '.dw':
                pad(alignment)
                for x in split_fields(instruction):
                    memory[address] = int(x)
                    address += 1
                instruction = ''
                directive = ''
            p.labels[label] = Label(label, label_address, address - label_address)

        if label or instruction:
            pad(alignment)
            memory[address] = instruction if instruction else '!'
            p.codemap[address] = line_index
            address += 1
            alignment = 1
        
        assert directive == ''


def print_raw():
    index_width = len('{:x}'.format(len(program) - 1))
    line_format = f'{{:0{index_width}X}} {{}}'
    return '\n'.join((line_format.format(i, c) for i, c in enumerate(code)))


def print_formatted():
    index_width = len('{:x}'.format(len(program) - 1))
    index_format = f'{{:0{index_width}X}}'

    label_width = max((len(label) for label in label_addr.keys()), default=0)

    statement_width = max((len(statement) for statement in program), default=0)

    label_lut = {line: label for label, line in label_addr.items()}
    def make_line(line_index):
        items = [index_format.format(line_index)]
        if label_width > 0:
            try:
                label = f'{label_lut[line_index]}:'
            except KeyError:
                label = ''
            items.append(label.ljust(label_width + 1))
        if statement_width > 0:
            statement = program[line_index]
            items.append(statement.ljust(statement_width))
        comment = comments[line_index]
        if comment:
            items.append(comment)
        return ' '.join(items)
    text = '\n'.join(
        make_line(i).strip() for i in range(len(program))
    )
    return text


imp = 'imp'
imm = 'imm'
abs = 'abs'
abx = 'abx'
ind = 'ind'
idx = 'idx'
jdd = 'jdd'

def parse_operand_macro(operand):
    if operand.startswith('@'):
        label, nibble = operand[1:].split('_')
        return pointer(p.labels[label].get_address() + int(nibble))
    if operand.startswith('_'):
        label, nibble = operand[1:].split('_')
        return constant(get_nibble(p.labels[label].get_address(), int(nibble)))
    raise RuntimeError()

def parse_instruction(instr: str):
    items = split_fields(instr)
    if len(items) == 1:
        opcode, = items
        return opcode, imp, cpu.mar
    if len(items) == 2:
        opcode, operand = items

        is_immediate = operand.startswith('#')
        if is_immediate:
            operand = operand[1:]
        
        is_indirect = operand.startswith('(') and operand.endswith(')')
        if is_indirect:
            operand = operand[1:-1]

        is_indexed = operand.endswith('+x')
        if is_indexed:
            operand = operand[:-2]
            index = cpu.x
        else:
            index = 0
        
        is_double_indirect = operand.startswith('[') and operand.endswith(']')
        if is_double_indirect:
            operand = operand[1:-1]
        
        if is_immediate:
            if operand.startswith('.'):
                accessor = parse_operand_macro(operand[1:])
            else:
                accessor = constant(int(operand))
            mode = imm
        elif is_indirect:
            taddr = p.labels[operand].get_address() + index
            accessor = pointer(memory[taddr]
                               + 16 * memory[taddr + 1]
                               + 256 * memory[taddr + 2])
            if is_indexed:
                mode = idx
            else:
                mode = ind
        elif is_double_indirect:
            taddr = p.labels[operand].get_address() + index
            taddr = (memory[taddr]
                     + 16 * memory[taddr + 1]
                     + 256 * memory[taddr + 2])
            accessor = pointer(memory[taddr]
                               + 16 * memory[taddr + 1]
                               + 256 * memory[taddr + 2])
            mode = jdd
        else:
            if operand.startswith('.'):
                assert not is_indexed
                accessor = parse_operand_macro(operand[1:])
            else:
                accessor = pointer(p.labels[operand].get_address() + index)
            # try:
            # except KeyError:
                # addr = None
                # data = None
            if is_indexed:
                mode = abx
            else:
                mode = abs
        
        return opcode, mode, accessor
    raise RuntimeError(instr)


class Cpu:
    def __init__(self) -> None:
        self.acc = 0
        self.x = 0
        self.c = 0
        self.mar = constant(0)
        self.pc = 0

cpu = Cpu()

def nop(p):
    cpu.pc += 1

def load(p):
    cpu.acc = p.read(0)
    cpu.pc += 1

def loadx(p):
    cpu.x = p.read(0)
    cpu.pc += 1

def store(p):
    p.write(0, cpu.acc)
    cpu.pc += 1

def storex(p):
    p.write(0, cpu.x)
    cpu.pc += 1

def swapax(p):
    cpu.acc, cpu.x = cpu.x, cpu.acc
    cpu.pc += 1

def add(p):
    cpu.acc += p.read(0)
    cpu.c = 0 if cpu.acc < 16 else 1
    cpu.acc %= 16
    cpu.pc += 1

def sub(p):
    cpu.acc -= p.read(0)
    cpu.c = 0 if cpu.acc < 0 else 1
    cpu.acc %= 16
    cpu.pc += 1

def jump(p):
    cpu.pc = p.get_value()

def jump_indirect(p):
    cpu.pc = p.read(0) + 16 * p.read(1) + 256 * p.read(2)

def jump_if(pred):
    def check_and_jump(p):
        if pred():
            jump(p)
        else:
            nop(p)
    return check_and_jump

def addx(p):
    cpu.x += p.read(0)
    cpu.c = 0 if cpu.x < 16 else 1
    cpu.x %= 16
    cpu.pc += 1

def lea(p):
    cpu.mar = p
    cpu.pc += 1

supported = {
    ('ld', imp): (1, 3, load),
    ('ld', imm): (1, 3, load),
    ('ld', abs): (1, 6, load),
    ('ld', abx): (1, 6, load),
    ('ld', ind): (1, 9, load),
    ('ld', idx): (1, 9, load),

    ('st', imp): (1, 3, store),
    ('st', imm): (1, 3, store),
    ('st', abs): (1, 6, store),
    ('st', abx): (1, 6, store),
    ('st', ind): (1, 9, store),
    ('st', idx): (1, 9, store),

    ('add', imp): (1, 3, add),
    ('add', imm): (1, 3, add),
    ('add', abs): (1, 6, add),
    ('add', abx): (1, 6, add),
    ('add', ind): (1, 9, add),
    ('add', idx): (1, 9, add),

    ('sub', imp): (1, 3, sub),
    ('sub', imm): (1, 3, sub),
    ('sub', abs): (1, 6, sub),
    ('sub', abx): (1, 6, sub),
    ('sub', ind): (1, 9, sub),
    ('sub', idx): (1, 9, sub),

    ('ldx', imp): (1, 3, loadx),
    ('ldx', imm): (1, 3, loadx),
    ('ldx', abs): (1, 6, loadx),
    ('ldx', abx): (1, 6, loadx),
    ('ldx', ind): (1, 9, loadx),
    ('ldx', idx): (1, 9, loadx),

    ('stx', imp): (1, 3, storex),
    ('stx', imm): (1, 3, storex),
    ('stx', abs): (1, 6, storex),
    ('stx', abx): (1, 6, storex),
    ('stx', ind): (1, 9, storex),
    ('stx', idx): (1, 9, storex),

    ('addx', imp): (1, 3, addx),
    ('addx', imm): (1, 3, addx),
    ('addx', abs): (1, 6, addx),
    ('addx', abx): (1, 6, addx),
    ('addx', ind): (1, 9, addx),
    ('addx', idx): (1, 9, addx),

    ('swapax', imp): (1, 3, swapax),

    ('j', imp): (1, 5, jump),
    ('j', imm): (1, 6, jump),
    ('j', abs): (1, 5, jump),
    ('j', abx): (1, 5, jump),
    ('j', ind): (1, 8, jump),
    ('j', idx): (1, 8, jump),
    
    ('j', jdd): (1, 11, jump),

    ('jc', imp): (1, 5, jump_if(lambda: cpu.c != 0)),
    ('jc', imm): (1, 6, jump_if(lambda: cpu.c != 0)),
    ('jc', abs): (1, 5, jump_if(lambda: cpu.c != 0)),
    ('jc', abx): (1, 5, jump_if(lambda: cpu.c != 0)),
    ('jc', ind): (1, 8, jump_if(lambda: cpu.c != 0)),
    ('jc', idx): (1, 8, jump_if(lambda: cpu.c != 0)),

    ('lea', imp): (1, 6, lea),
    ('lea', imm): (1, 5, lea),
    ('lea', abs): (1, 5, lea),
    ('lea', abx): (1, 5, lea),
    ('lea', ind): (1, 8, lea),
    ('lea', idx): (1, 8, lea),
}

stats = {k: 0 for k in supported.keys()}


def print_buffers():
    print('buffers')
    print(tabulate.tabulate([[label.name, label.get_address(), label.get_buffer()] for label in p.labels.values() if label.size > 0]))

def run():
    ictr, cctr = 0, 0

    step_by_step = False
    step_by_step = True
    while True:
        prompt = f'ictr={ictr:>4d}, cctr={cctr:>4d} | acc={cpu.acc:x} x={cpu.x:x} c={cpu.c:x} mar={cpu.mar.get_value():03x} pc={cpu.pc:03x} | {p.source[p.codemap[cpu.pc]]} '
        if step_by_step:
            command = input(prompt)
            if command == 'q':
                break
            if command == 'r':
                step_by_step = False
            if command == 'b':
                print_buffers()
                continue
        else:
            print(prompt)

        instr = memory[cpu.pc]
        if instr.startswith('!'):
            nop(None)
            continue

        opcode, mode, accessor = parse_instruction(instr)
        if opcode == 'stop':
            break
        ic, cc, f = supported[opcode, mode]
        f(accessor)
        ictr += ic
        cctr += cc
        stats[opcode, mode] += 1
        continue

    print()
    print_buffers()
    print()
    print('statistics')
    print(tabulate.tabulate([[opcode, mode, icount, icount * supported[opcode, mode][1]] for ((opcode, mode), icount) in stats.items() if icount > 0]))



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source_file')
    args = parser.parse_args()

    with open(args.source_file, 'r') as src:
        parse(src.read())
    run()
