#!/usr/bin/env python3
"""
Интерфейс командной строки для парсера конфигурационного языка (Вариант 21)
"""

import sys
import json
import argparse
from pathlib import Path
from src.parser import ConfigParser, ParserError


def main():
    parser = argparse.ArgumentParser(
        description='Конвертер учебного конфигурационного языка в JSON (Вариант 21)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Примеры:
  %(prog)s config.conf                    # Вывод в stdout
  %(prog)s input.txt -o output.json       # Сохранение в файл
  %(prog)s --help                         # Справка

Синтаксис языка:
  • Комментарии: |# многострочный #|
  • Числа: 0b1010, 0B1101 (двоичные)
  • Таблицы: table([NAME = VALUE, ...])
  • Имена: только A-Z
  • Константы: значение -> NAME
  • Ссылки: .(NAME).
        '''
    )
    
    parser.add_argument(
        'input_file',
        help='Входной файл с конфигурацией на учебном языке'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Файл для вывода JSON (по умолчанию stdout)'
    )
    
    parser.add_argument(
        '-v', '--version',
        action='version',
        version='%(prog)s 1.0 (Вариант 21)'
    )
    
    args = parser.parse_args()
    
    try:
        # Чтение входного файла
        input_path = Path(args.input_file)
        if not input_path.exists():
            print(f"Ошибка: файл '{args.input_file}' не найден", file=sys.stderr)
            return 1
        
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Парсинг
        config_parser = ConfigParser()
        result = config_parser.parse(content)
        
        # Преобразование в JSON
        json_output = json.dumps(result, indent=2, ensure_ascii=False)
        
        # Вывод
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(json_output + '\n')
            print(f"Результат сохранен в: {output_path}", file=sys.stderr)
        else:
            print(json_output)
        
        return 0
        
    except ParserError as e:
        print(f"Синтаксическая ошибка: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())