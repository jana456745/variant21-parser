#!/usr/bin/env python3
"""
Тесты для парсера конфигурационного языка (Вариант 21)
"""

import unittest
import json
import tempfile
import os
from src.parser import ConfigParser, ParserError


class TestConfigParser(unittest.TestCase):
    """Тесты основного парсера"""
    
    def setUp(self):
        self.parser = ConfigParser()
    
    def test_binary_numbers(self):
        """Тест парсинга двоичных чисел"""
        test_cases = [
            ("0b1010", 10),
            ("0B1101", 13),
            ("0b0", 0),
            ("0b11111111", 255),
        ]
        
        for input_str, expected in test_cases:
            with self.subTest(input=input_str):
                text = f"{input_str} -> TEST"
                result = self.parser.parse(text)
                self.assertEqual(result["TEST"], expected)
    
    def test_names_uppercase_only(self):
        """Тест имен - только заглавные буквы"""
        # Корректные имена
        text = "0b1 -> ABC"
        result = self.parser.parse(text)
        self.assertIn("ABC", result)
        
        # Некорректные имена
        with self.assertRaises(ParserError):
            self.parser.parse("0b1 -> abc")
        
        with self.assertRaises(ParserError):
            self.parser.parse("0b1 -> Abc")
        
        with self.assertRaises(ParserError):
            self.parser.parse("0b1 -> ABC123")
    
    def test_table_basic(self):
        """Тест простой таблицы"""
        text = """
table([
    PORT = 0b1010,
    HOST = 0b1100,
])
"""
        result = self.parser.parse(text)
        self.assertEqual(result["PORT"], 10)
        self.assertEqual(result["HOST"], 12)
    
    def test_nested_tables(self):
        """Тест вложенных таблиц"""
        text = """
table([
    SERVER = table([
        IP = 0b11000000,
        PORT = 0b10100000,
    ]),
    CLIENT = table([
        TIMEOUT = 0b1111,
    ]),
])
"""
        result = self.parser.parse(text)
        self.assertEqual(result["SERVER"]["IP"], 192)
        self.assertEqual(result["SERVER"]["PORT"], 160)
        self.assertEqual(result["CLIENT"]["TIMEOUT"], 15)
    
    def test_constants(self):
        """Тест объявления и использования констант"""
        text = """
0b1010 -> BASE_VALUE
.(BASE_VALUE). -> COPY_VALUE
table([
    ORIGINAL = .(BASE_VALUE).,
    COPY = .(COPY_VALUE).,
])
"""
        result = self.parser.parse(text)
        self.assertEqual(result["BASE_VALUE"], 10)
        self.assertEqual(result["COPY_VALUE"], 10)
        self.assertEqual(result["ORIGINAL"], 10)
        self.assertEqual(result["COPY"], 10)
    
    def test_comments(self):
        """Тест многострочных комментариев"""
        text = """
|# 
Это многострочный
комментарий 
#|
0b1100 -> VALUE_A
|# Однострочный #| 0b0011 -> VALUE_B
"""
        result = self.parser.parse(text)
        self.assertEqual(result["VALUE_A"], 12)
        self.assertEqual(result["VALUE_B"], 3)
    
    def test_error_undefined_constant(self):
        """Тест ошибки неопределенной константы"""
        text = ".(UNDEFINED). -> TEST"
        with self.assertRaises(ParserError) as ctx:
            self.parser.parse(text)
        self.assertIn("Неопределенная константа", str(ctx.exception))
    
    def test_error_unclosed_comment(self):
        """Тест незакрытого комментария"""
        text = "|# Незакрытый комментарий"
        with self.assertRaises(ParserError) as ctx:
            self.parser.parse(text)
        self.assertIn("Незакрытый многострочный комментарий", str(ctx.exception))
    
    def test_error_invalid_binary(self):
        """Тест некорректного двоичного числа"""
        text = "0b102 -> TEST"
        with self.assertRaises(ParserError) as ctx:
            self.parser.parse(text)
        self.assertIn("двоичные цифры", str(ctx.exception))
    
    def test_empty_table(self):
        """Тест пустой таблицы"""
        text = "table([])"
        result = self.parser.parse(text)
        self.assertEqual(result, {})
    
    def test_multiple_constants_with_semicolon(self):
        """Тест нескольких констант с точкой с запятой"""
        text = """
0b0001 -> CONST_A;
0b0010 -> CONST_B;
0b0011 -> CONST_C;
"""
        result = self.parser.parse(text)
        self.assertEqual(result["CONST_A"], 1)
        self.assertEqual(result["CONST_B"], 2)
        self.assertEqual(result["CONST_C"], 3)
    
    def test_complex_nesting(self):
        """Тест сложной вложенности"""
        text = """
0b0010 -> TWO
0b0100 -> FOUR

table([
    CONFIG = table([
        VERSION = 0b0001,
        SETTINGS = table([
            TIMEOUT = .(TWO).,
            RETRIES = .(FOUR).,
        ]),
    ]),
    DATA = table([
        SIZE = 0b10000000,
        COUNT = 0b00001000,
    ]),
])
"""
        result = self.parser.parse(text)
        self.assertEqual(result["TWO"], 2)
        self.assertEqual(result["FOUR"], 4)
        self.assertEqual(result["CONFIG"]["VERSION"], 1)
        self.assertEqual(result["CONFIG"]["SETTINGS"]["TIMEOUT"], 2)
        self.assertEqual(result["CONFIG"]["SETTINGS"]["RETRIES"], 4)
        self.assertEqual(result["DATA"]["SIZE"], 128)
        self.assertEqual(result["DATA"]["COUNT"], 8)


class TestCLI(unittest.TestCase):
    """Тесты командной строки"""
    
    def test_cli_success(self):
        """Тест успешного запуска через CLI"""
        import subprocess
        
        # Создаем временный файл
        with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
            f.write("0b1010 -> ANSWER\ntable([QUESTION = .(ANSWER).])")
            temp_file = f.name
        
        try:
            # Запускаем CLI
            result = subprocess.run(
                ['python', 'cli.py', temp_file],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            self.assertEqual(result.returncode, 0)
            
            # Проверяем JSON
            parsed = json.loads(result.stdout)
            self.assertEqual(parsed["ANSWER"], 10)
            self.assertEqual(parsed["QUESTION"], 10)
            
        finally:
            os.unlink(temp_file)
    
    def test_cli_file_not_found(self):
        """Тест ошибки при отсутствии файла"""
        import subprocess
        
        result = subprocess.run(
            ['python', 'cli.py', 'nonexistent.conf'],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("не найден", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)