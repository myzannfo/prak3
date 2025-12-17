#!/usr/bin/env python3
import sys
import struct

def assemble(input_file, output_file, test_mode=False):
    try:
        with open(input_file, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Ошибка: файл '{input_file}' не найден!")
        print("Создайте файл test_program.asm")
        return
    
    binary = bytearray()
    
    print(f"Ассемблирование {input_file}...")
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        
        if not line or line.startswith(';'):
            continue
            
        if ';' in line:
            line = line.split(';')[0].strip()
            
        parts = line.split()
        if not parts:
            continue
            
        mnemonic = parts[0].upper()
        args = []
        
        for arg in parts[1:]:
            if arg.startswith('0x'):
                args.append(int(arg[2:], 16))
            else:
                try:
                    args.append(int(arg))
                except:
                    args.append(0)
        
        if mnemonic == 'LOADC':
            if len(args) != 3:
                print(f"Ошибка строки {line_num}: LOADC требует 3 аргумента")
                continue
                
            const, _, dest = args
            A = 1
            B = const
            C = dest
            
            word = (A << 26) | (B << 6) | C
            binary.extend(struct.pack('<I', word))
            
            if test_mode:
                hex_bytes = ' '.join(f'{b:02X}' for b in struct.pack('<I', word))
                print(f"[{line_num}] LOADC: R{dest} = {const} → {hex_bytes}")
            
        elif mnemonic == 'READM':
            if len(args) != 4:
                print(f"Ошибка строки {line_num}: READM требует 4 аргумента")
                continue
                
            offset, src, dest, base = args
            A = 21
            B = offset
            C = dest
            D = base
            
            byte1 = (A << 2) | (B >> 7)
            byte2 = ((B & 0x7F) << 1) | (C >> 2)
            byte3 = ((C & 0x03) << 6) | (D << 3)
            
            binary.extend([byte1, byte2, byte3])
            
            if test_mode:
                hex_bytes = f'{byte1:02X} {byte2:02X} {byte3:02X}'
                print(f"[{line_num}] READM: R{dest} = mem[R{base}+{offset}] → {hex_bytes}")
            
        elif mnemonic == 'WRITEM':
            if len(args) != 3:
                print(f"Ошибка строки {line_num}: WRITEM требует 3 аргумента")
                continue
                
            src, dest, base = args
            A = 39
            B = src
            C = base
            
            byte1 = (A << 2) | (B >> 1)
            byte2 = ((B & 0x01) << 7) | (C << 4)
            
            binary.extend([byte1, byte2])
            
            if test_mode:
                hex_bytes = f'{byte1:02X} {byte2:02X}'
                print(f"[{line_num}] WRITEM: mem[R{base}] = R{src} → {hex_bytes}")
            
        elif mnemonic == 'POPCNT':
            if len(args) != 3:
                print(f"Ошибка строки {line_num}: POPCNT требует 3 аргумента")
                continue
                
            src, dest, base = args
            A = 44
            B = src
            C = base
            
            byte1 = (A << 2) | (B >> 1)
            byte2 = ((B & 0x01) << 7) | (C << 4)
            
            binary.extend([byte1, byte2])
            
            if test_mode:
                hex_bytes = f'{byte1:02X} {byte2:02X}'
                print(f"[{line_num}] POPCNT: R{base} = popcount(R{src}) → {hex_bytes}")
            
        else:
            print(f"Неизвестная команда в строке {line_num}: {mnemonic}")
    
    with open(output_file, 'wb') as f:
        f.write(binary)
    
    print(f"\nСоздан файл: {output_file} ({len(binary)} байт)")
    
    if test_mode:
        print("\nШестнадцатеричный дамп:")
        for i in range(0, len(binary), 16):
            chunk = binary[i:i+16]
            hex_str = ' '.join(f'{b:02X}' for b in chunk)
            print(f"{i:04X}: {hex_str}")

def main():
    if len(sys.argv) < 3:
        print("Использование: python asm.py <input.asm> <output.bin> [test]")
        print("Пример: python asm.py test_program.asm program.bin test")
        return
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    test_mode = len(sys.argv) > 3 and sys.argv[3].lower() == 'test'
    
    assemble(input_file, output_file, test_mode)

if __name__ == '__main__':
    main()