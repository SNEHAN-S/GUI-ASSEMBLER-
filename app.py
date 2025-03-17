from flask import Flask, request, jsonify, render_template # type: ignore
import os
import re

app = Flask(__name__)

class RISCAssembler:
    def __init__(self):
        self.register_map = {
            'r0': '0000', 'r1': '0001', 'r2': '0010', 'r3': '0011',
            'r4': '0100', 'r5': '0101', 'r6': '0110', 'r7': '0111',
            'r8': '1000', 'r9': '1001', 'r10': '1010', 'r11': '1011',
            'r12': '1100', 'r13': '1101', 'r14': '1110', 'r15': '1111'
        }
        self.opcode_map = {
            'add': '00000', 'sub': '00001', 'mul': '00010', 'div': '00011',
            'mod': '00100', 'and': '00101', 'or': '00110', 'not': '00111',
            'lsl': '01000', 'lsr': '01001', 'asr': '01010', 'ld': '01011',
            'st': '01100', 'cmp': '01101', 'mov': '01110', 'beq': '01111',
            'bgt': '10000', 'b': '10001', 'call': '10010', 'ret': '10011',
            'nop': '10100'
        }

    def tokenize(self, line):
        try:
            line = re.sub(r'(0[xX][0-9a-fA-F]+)', r' \1 ', line)
            tokens = re.findall(r'0[xX][0-9a-fA-F]+|\w+|[^\w\s]', line)
            return tokens
        except Exception as e:
            return []

    def is_register(self, token):
        """Check if token is a valid register name"""
        return token in self.register_map

    def is_immediate(self, token):
        """Check if token represents an immediate value"""
        if token.startswith('0x') or token.startswith('0X'):
            try:
                int(token, 16)
                return True
            except ValueError:
                return False
        else:
            try:
                int(token)
                return True
            except ValueError:
                return False

    def parse(self, tokens):
        try:
            instructions = []
            if not tokens:
                return instructions
                
            op = tokens[0]
            if op in ['add', 'sub', 'mul', 'div', 'mod', 'and', 'or']:
                if len(tokens) < 4:
                    return instructions
                
                rd = tokens[1]
                if tokens[2] != ',':
                    return instructions
                
                rs1 = tokens[3]
                if len(tokens) < 5 or tokens[4] != ',':
                    return instructions
                
                rs2_or_imm = tokens[5]
                if self.is_register(rs2_or_imm):
                    instruction = {
                        'op': op,
                        'rd': rd,
                        'rs1': rs1,
                        'rs2': rs2_or_imm,
                        'type': 'R'
                    }
                elif self.is_immediate(rs2_or_imm):
                    instruction = {
                        'op': op,
                        'rd': rd,
                        'rs1': rs1,
                        'imm': rs2_or_imm,
                        'type': 'I'
                    }
                else:
                    return instructions
                
                instructions.append(instruction)
            elif op in ['ld', 'st']:
                if len(tokens) < 4:
                    return instructions
                
                rd = tokens[1]
                if tokens[2] != ',':
                    return instructions
                
                address = tokens[3]
                instruction = {
                    'op': op,
                    'rd': rd,
                    'address': address
                }
                instructions.append(instruction)
            elif op in ['beq', 'bgt', 'b', 'call']:
                if len(tokens) < 2:
                    return instructions
                
                offset = tokens[1]
                instruction = {
                    'op': op,
                    'offset': offset
                }
                instructions.append(instruction)
            elif op == 'ret' or op == 'nop':
                instruction = {
                    'op': op
                }
                instructions.append(instruction)
            
            return instructions
        except Exception as e:
            return []

    def parse_address_value(self, address_str):
        """
        Parse address value which can be in decimal or hexadecimal format.
        Returns the integer value of the address.
        """
        try:
            if address_str.startswith('0x') or address_str.startswith('0X'):
                return int(address_str, 16)
            else:
                return int(address_str)
        except ValueError:
            return 0

    def generate_machine_code(self, parsed_instructions):
        try:
            machine_code = []
            for instruction in parsed_instructions:
                op = instruction['op']
                if op in ['add', 'sub', 'mul', 'div', 'mod', 'and', 'or']:
                    if instruction.get('type') == 'I':
                        rd = instruction['rd']
                        rs1 = instruction['rs1']
                        imm_str = instruction['imm']
                        imm_value = self.parse_address_value(imm_str)
                        imm = format(imm_value & 0xFFFF, '016b')
                        machine_code.append(f"{self.opcode_map[op]}1{self.register_map[rd]}{self.register_map[rs1]}{imm}"[:30])
                    else:
                        rd = instruction['rd']
                        rs1 = instruction['rs1']
                        rs2 = instruction['rs2']
                        machine_code.append(f"{self.opcode_map[op]}0{self.register_map[rd]}{self.register_map[rs1]}{self.register_map[rs2]}{'0' * 12}"[:30])
                elif op in ['ld', 'st']:
                    rd = instruction['rd']
                    address = instruction['address']
                    if '[' in address and ']' in address:
                        imm_rs = address.split('[')
                        imm_str = imm_rs[0]
                        rs_str = imm_rs[1].split(']')[0]
                        
                        imm_value = self.parse_address_value(imm_str)
                        imm = format(imm_value & 0xFFFF, '016b')
                        
                        rs1 = self.register_map.get(rs_str, '0000')
                        machine_code.append(f"{self.opcode_map[op]}1{self.register_map[rd]}{rs1}{imm}"[:30])
                    else:
                        imm_value = self.parse_address_value(address)
                        imm = format(imm_value & 0xFFFF, '016b')
                        rs1 = '0000'
                        machine_code.append(f"{self.opcode_map[op]}1{self.register_map[rd]}{rs1}{imm}"[:30])
                elif op in ['beq', 'bgt', 'b', 'call']:
                    offset_value = self.parse_address_value(instruction['offset'])
                    offset = format(offset_value & 0x1FFFFFF, '025b')
                    machine_code.append(f"{self.opcode_map[op]}{offset}"[:30])
                elif op == 'ret' or op == 'nop':
                    machine_code.append(f"{self.opcode_map[op]}{'0' * 25}"[:30])
            return machine_code
        except Exception as e:
            return []

    def assemble(self, assembly_code):
        try:
            lines = assembly_code.strip().split('\n')
            machine_code = []
            errors = []
            
            for i, line in enumerate(lines):
                line = line.strip()
                if line:
                    tokens = self.tokenize(line)
                    parsed_instructions = self.parse(tokens)
                    
                    if not parsed_instructions:
                        errors.append(f"Line {i+1}: Syntax error in '{line}'")
                        continue
                        
                    line_machine_code = self.generate_machine_code(parsed_instructions)
                    if not line_machine_code:
                        errors.append(f"Line {i+1}: Failed to generate machine code for '{line}'")
                    else:
                        machine_code.extend(line_machine_code)
            
            return {
                "success": len(errors) == 0,
                "machine_code": machine_code,
                "errors": errors
            }
        except Exception as e:
            return {
                "success": False,
                "machine_code": [],
                "errors": [f"An error occurred: {str(e)}"]
            }

@app.route('/api/assemble', methods=['POST'])
def assemble():
    data = request.json
    assembly_code = data.get('code', '')
    
    assembler = RISCAssembler()
    result = assembler.assemble(assembly_code)
    
    return jsonify(result)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)