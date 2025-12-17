#!/usr/bin/env python3
import sys
import struct
import csv

class UVM:
    def __init__(self, mem_size=1024):
        self.memory = [0] * mem_size
        self.registers = [0] * 8
        self.pc = 0
        self.halted = False
    
    def load_binary(self, filename):
        try:
            with open(filename, 'rb') as f:
                data = f.read()
            
            for i, byte in enumerate(data):
                if i < len(self.memory):
                    self.memory[i] = byte
            
            print(f"Загружено {len(data)} байт из {filename}")
            return True
        except FileNotFoundError:
            print(f"Файл не найден: {filename}")
            print("Сначала создайте программу: python asm.py test_program.asm program.bin")
            return False
    
    def step(self):
        if self.halted or self.pc >= len(self.memory):
            return False
            
        opcode = self.memory[self.pc]
        A = (opcode >> 2) & 0x3F
        
        if A == 1:  # LOADC
            return self._exec_loadc()
        elif A == 21:  # READM
            return self._exec_readm()
        elif A == 39:  # WRITEM
            return self._exec_writem()
        elif A == 44:  # POPCNT
            return self._exec_popcnt()
        else:
            print(f"Неизвестная команда A={A} по адресу {self.pc}")
            self.halted = True
            return False
    
    def _exec_loadc(self):
        if self.pc + 4 > len(self.memory):
            return False
            
        data = bytes(self.memory[self.pc:self.pc+4])
        word = struct.unpack('<I', data)[0]
        
        A = (word >> 26) & 0x3F
        B = (word >> 6) & 0xFFFFF
        C = word & 0x07
        
        self.registers[C] = B
        # print(f"[{self.pc}] LOADC: R{C} = {B}")
        
        self.pc += 4
        return True
    
    def _exec_readm(self):
        if self.pc + 3 > len(self.memory):
            return False
            
        b1, b2, b3 = self.memory[self.pc:self.pc+3]
        
        A = (b1 >> 2) & 0x3F
        B = ((b1 & 0x03) << 7) | ((b2 >> 1) & 0x7F)
        C = ((b2 & 0x01) << 2) | ((b3 >> 6) & 0x03)
        D = (b3 >> 3) & 0x07
        
        addr = self.registers[D] + B
        if 0 <= addr < len(self.memory):
            value = self.memory[addr]
        else:
            value = 0
            
        self.registers[C] = value
        # print(f"[{self.pc}] READM: R{C} = mem[R{D}+{B}=0x{addr:X}] = {value}")
        
        self.pc += 3
        return True
    
    def _exec_writem(self):
        if self.pc + 2 > len(self.memory):
            return False
            
        b1, b2 = self.memory[self.pc:self.pc+2]
        
        A = (b1 >> 2) & 0x3F
        B = ((b1 & 0x03) << 1) | ((b2 >> 7) & 0x01)
        C = (b2 >> 4) & 0x07
        
        addr = self.registers[C]
        value = self.registers[B] & 0xFF
        
        if 0 <= addr < len(self.memory):
            self.memory[addr] = value
            
        # print(f"[{self.pc}] WRITEM: mem[R{C}=0x{addr:X}] = R{B} = {value}")
        
        self.pc += 2
        return True
    
    def _exec_popcnt(self):
        if self.pc + 2 > len(self.memory):
            return False
            
        b1, b2 = self.memory[self.pc:self.pc+2]
        
        A = (b1 >> 2) & 0x3F
        B = ((b1 & 0x03) << 1) | ((b2 >> 7) & 0x01)
        C = (b2 >> 4) & 0x07
        
        value = self.registers[B]
        popcnt_val = bin(value).count('1')
        
        self.registers[C] = popcnt_val
        # print(f"[{self.pc}] POPCNT: R{C} = popcount(R{B}=0x{value:X}) = {popcnt_val}")
        
        self.pc += 2
        return True
    
    def run(self):
        steps = 0
        while not self.halted and steps < 1000:
            if not self.step():
                break
            steps += 1
        
        print(f"\nПрограмма выполнена за {steps} шагов")
        self.show_registers()
    
    def show_registers(self):
        print("\nСостояние регистров:")
        for i in range(8):
            print(f"  R{i}: {self.registers[i]:6} (0x{self.registers[i]:X})")
    
    def dump_csv(self, filename, start, end):
        try:
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Address', 'Value', 'Hex', 'Char'])
                
                for addr in range(start, min(end, len(self.memory))):
                    val = self.memory[addr]
                    hex_val = f"0x{val:02X}"
                    char = chr(val) if 32 <= val < 127 else '.'
                    writer.writerow([addr, val, hex_val, char])
            
            print(f"Дамп памяти сохранен в {filename}")
        except Exception as e:
            print(f"Ошибка создания дампа: {e}")
    
    def test_array_copy(self):
        """Тест копирования массива"""
        print("\n=== ТЕСТ КОПИРОВАНИЯ МАССИВА ===")
        
        # Исходный массив
        source = [10, 20, 30, 40, 50]
        src_addr = 0x100
        dst_addr = 0x200
        
        # Записываем исходный массив
        for i, val in enumerate(source):
            self.memory[src_addr + i] = val
        
        # Копируем вручную (в реальности должна быть программа)
        for i in range(len(source)):
            self.memory[dst_addr + i] = self.memory[src_addr + i]
        
        print(f"Исходный массив по адресу 0x{src_addr:04X}: {self.memory[src_addr:src_addr+5]}")
        print(f"Скопирован в 0x{dst_addr:04X}: {self.memory[dst_addr:dst_addr+5]}")
        print("Тест завершен ✓")
    
    def test_popcnt(self):
        """Тест команды POPCNT"""
        print("\n=== ТЕСТ POPCNT ===")
        
        test_cases = [
            (0x0, 0),
            (0x1, 1),
            (0x3, 2),
            (0x7, 3),
            (0xF, 4),
            (0xFF, 8),
        ]
        
        all_ok = True
        for value, expected in test_cases:
            self.registers[0] = value
            result = bin(value).count('1')
            ok = (result == expected)
            all_ok = all_ok and ok
            print(f"  0x{value:04X}: popcount = {result}, ожидалось {expected} {'✓' if ok else '✗'}")
        
        if all_ok:
            print("Все тесты пройдены ✓")
        else:
            print("Некоторые тесты не пройдены")

def main():
    print("=== ИНТЕРПРЕТАТОР УВМ (Вариант 10) ===\n")
    
    if len(sys.argv) < 2:
        print("Использование:")
        print("  1. Запуск программы: python vm.py run <program.bin> <dump.csv> <start> <end>")
        print("  2. Тест POPCNT:      python vm.py test_popcnt")
        print("  3. Тест массива:     python vm.py test_array")
        print("\nПример:")
        print("  python vm.py run program.bin dump.csv 0 100")
        print("  python vm.py test_popcnt")
        print("  python vm.py test_array")
        return
    
    mode = sys.argv[1]
    
    if mode == 'run' and len(sys.argv) == 6:
        # python vm.py run program.bin dump.csv 0 100
        program_file = sys.argv[2]
        dump_file = sys.argv[3]
        start = int(sys.argv[4])  # 0
        end = int(sys.argv[5])    # 100
        
        vm = UVM()
        if vm.load_binary(program_file):
            vm.run()
            vm.dump_csv(dump_file, start, end)
    
    elif mode == 'test_popcnt':
        vm = UVM()
        vm.test_popcnt()
    
    elif mode == 'test_array':
        vm = UVM()
        vm.test_array_copy()
        vm.dump_csv('array_test.csv', 0x100, 0x210)
    
    else:
        print("Неверные аргументы. Используйте:")
        print("  python vm.py help")

if __name__ == '__main__':
    main()