#!/usr/bin/env python3
"""
Парсер учебного конфигурационного языка (Вариант 21)
Поддерживает:
- Многострочные комментарии |# ... #|
- Двоичные числа: 0b1010, 0B1101
- Словари: table([ИМЯ = ЗНАЧЕНИЕ, ...])
- Константы: значение -> ИМЯ и .(ИМЯ).
"""

import re
from typing import Dict, Any, List, Union, Optional


class ParserError(Exception):
    """Класс для ошибок парсера"""
    def __init__(self, message: str, line: int = 0, column: int = 0):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"Line {line}, column {column}: {message}")


class ConfigParser:
    """Парсер конфигурационного языка"""
    
    def __init__(self):
        self.text = ""
        self.pos = 0
        self.line = 1
        self.column = 1
        self.constants: Dict[str, Any] = {}
    
    def reset(self):
        """Сброс состояния парсера"""
        self.pos = 0
        self.line = 1
        self.column = 1
        self.constants = {}
    
    def error(self, message: str):
        """Генерация ошибки с текущей позицией"""
        raise ParserError(message, self.line, self.column)
    
    def peek(self, n: int = 1) -> str:
        """Посмотреть на n символов вперед без перемещения"""
        if self.pos + n <= len(self.text):
            return self.text[self.pos:self.pos + n]
        return ""
    
    def consume(self, n: int = 1):
        """Пропустить n символов"""
        for _ in range(n):
            if self.pos >= len(self.text):
                return
            if self.text[self.pos] == '\n':
                self.line += 1
                self.column = 1
            else:
                self.column += 1
            self.pos += 1
    
    def skip_whitespace_and_comments(self):
        """Пропустить пробелы и комментарии"""
        while self.pos < len(self.text):
            # Пробельные символы
            if self.text[self.pos] in ' \t\r':
                self.consume()
            # Новая строка
            elif self.text[self.pos] == '\n':
                self.consume()
            # Многострочный комментарий
            elif self.peek(2) == '|#':
                self.consume(2)  # Пропускаем |#
                while self.pos < len(self.text) - 1:
                    if self.peek(2) == '#|':
                        self.consume(2)  # Пропускаем #|
                        break
                    self.consume()
                else:
                    self.error("Незакрытый многострочный комментарий")
            else:
                break
    
    def parse_name(self) -> str:
        """Парсинг имени [A-Z]+"""
        self.skip_whitespace_and_comments()
        
        start = self.pos
        while self.pos < len(self.text) and self.text[self.pos].isupper():
            self.consume()
        
        if self.pos == start:
            self.error("Ожидалось имя из заглавных букв (A-Z)")
        
        return self.text[start:self.pos]
    
    def parse_binary_number(self) -> int:
        """Парсинг двоичного числа 0[bB][01]+"""
        self.skip_whitespace_and_comments()
        
        # Проверяем начало числа
        if self.peek(2).lower() != '0b':
            self.error("Ожидалось двоичное число (начинается с 0b или 0B)")
        
        self.consume(2)  # Пропускаем 0b или 0B
        
        # Собираем двоичные цифры
        start = self.pos
        while self.pos < len(self.text) and self.text[self.pos] in '01':
            self.consume()
        
        if self.pos == start:
            self.error("Отсутствуют двоичные цифры после 0b")
        
        binary_str = self.text[start:self.pos]
        try:
            return int(binary_str, 2)
        except ValueError:
            self.error(f"Некорректное двоичное число: 0b{binary_str}")
    
    def parse_constant_reference(self) -> Any:
        """Парсинг ссылки на константу .(ИМЯ)."""
        if not self.match('.'):
            self.error("Ожидалось '.' для ссылки на константу")
        
        self.skip_whitespace_and_comments()
        if not self.match('('):
            self.error("Ожидалось '(' после '.'")
        
        name = self.parse_name()
        
        self.skip_whitespace_and_comments()
        if not self.match(')'):
            self.error("Ожидалось ')' после имени константы")
        
        self.skip_whitespace_and_comments()
        if not self.match('.'):
            self.error("Ожидалось '.' после ')'")
        
        if name not in self.constants:
            self.error(f"Неопределенная константа: {name}")
        
        return self.constants[name]
    
    def match(self, expected: str) -> bool:
        """Проверяет, соответствует ли следующий текст ожидаемому"""
        if self.peek(len(expected)) == expected:
            self.consume(len(expected))
            return True
        return False
    
    def parse_value(self) -> Any:
        """Парсинг значения (число, таблица или константа)"""
        self.skip_whitespace_and_comments()
        
        # Ссылка на константу
        if self.peek(2) == '.(':
            return self.parse_constant_reference()
        
        # Двоичное число
        elif self.peek(2).lower() == '0b':
            return self.parse_binary_number()
        
        # Таблица
        elif self.peek(5) == 'table':
            return self.parse_table()
        
        else:
            self.error("Ожидалось значение (число, таблица или ссылка на константу)")
    
    def parse_table(self) -> Dict[str, Any]:
        """Парсинг таблицы table([...])"""
        if not self.match('table'):
            self.error("Ожидалось 'table'")
        
        self.skip_whitespace_and_comments()
        if not self.match('('):
            self.error("Ожидалось '(' после 'table'")
        
        self.skip_whitespace_and_comments()
        if not self.match('['):
            self.error("Ожидалось '[' после 'table('")
        
        result = {}
        first = True
        
        while True:
            self.skip_whitespace_and_comments()
            
            # Проверка на закрывающую скобку
            if self.peek() == ']':
                self.consume()  # Пропускаем ']'
                self.skip_whitespace_and_comments()
                if self.match(')'):
                    return result
                else:
                    self.error("Ожидалось ')' после ']'")
            
            # Запятая между элементами (кроме первого)
            if not first:
                if not self.match(','):
                    self.error("Ожидалась ',' между элементами таблицы")
                self.skip_whitespace_and_comments()
            
            # Парсинг пары имя=значение
            name = self.parse_name()
            
            self.skip_whitespace_and_comments()
            if not self.match('='):
                self.error(f"Ожидалось '=' после имени '{name}'")
            
            value = self.parse_value()
            
            result[name] = value
            first = False
    
    def parse_constant_declaration(self) -> None:
        """Парсинг объявления константы: значение -> ИМЯ"""
        value = self.parse_value()
        
        self.skip_whitespace_and_comments()
        if not self.match('-'):
            self.error("Ожидалось '-' в объявлении константы")
        
        if not self.match('>'):
            self.error("Ожидалось '>' после '-'")
        
        name = self.parse_name()
        
        # Необязательная точка с запятой
        self.skip_whitespace_and_comments()
        if self.peek() == ';':
            self.consume()
        
        self.constants[name] = value
    
    def parse(self, text: str) -> Dict[str, Any]:
        """Основной метод парсинга"""
        self.reset()
        self.text = text
        
        self.skip_whitespace_and_comments()
        
        # Если текст начинается с table, парсим таблицу
        if self.peek(5) == 'table':
            return self.parse_table()
        
        # Иначе парсим объявления констант
        while self.pos < len(self.text):
            self.skip_whitespace_and_comments()
            
            if self.pos >= len(self.text):
                break
            
            self.parse_constant_declaration()
        
        return self.constants.copy()