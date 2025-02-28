from parser_file import ParserFile
from tokens import Token, TokenEnum

_KEYWORDS: dict = {
    "if":       TokenEnum.If,
    "else":     TokenEnum.Else,
    "switch":   TokenEnum.Switch,
    "case":     TokenEnum.Case,
    "default":  TokenEnum.Default,
    "while":    TokenEnum.While,
    "for":      TokenEnum.For,
    "continue": TokenEnum.Continue,
    "break":    TokenEnum.Break,
    "const":    TokenEnum.Const,
    "macro":    TokenEnum.Macro,
    "extern":   TokenEnum.Extern,
    "pub":      TokenEnum.Pub,
    "inline":   TokenEnum.Inline,
    "return":   TokenEnum.Return,
    "module":   TokenEnum.Module,
    "import":   TokenEnum.Import,
    "as":       TokenEnum.As,
    "not":      TokenEnum.BoolNot,
    "and":      TokenEnum.BoolAnd,
    "or":       TokenEnum.BoolOr,
}

# come on python, I want this function so badly
def is_hex(ch: str):
    return ch.isdecimal() or ch in "abcdefABCDEF"

class Lexer:
    def __init__(self, src: ParserFile):
        self.src = src
        self.token_start = 0
    
    def _make_token(self, token_type):
        return Token(token_type, self.token_start, self.src.pos - self.token_start)

    def scan_escape(self):
        ch = self.src.getc()
        if ch in ('0', 'a', 'b', 'e', 'f', 'n', 'r', 't', 'v', '\\', '\'', '"'):
            return True
        elif ch == 'x':
            ch = self.src.getc()
            if not is_hex(ch):
                return False
            ch = self.src.getc()
            if not is_hex(ch):
                return False
            return True
        else:
            return False

    def scan_multiline_comment(self):
        ch = None
        nesting = 1

        while nesting > 0:
            ch = self.src.getc()

            if self.src.is_eof():
                return

            if ch == '*' and self.src.peek() == '/':
                nesting -= 1
            elif ch == '/' and self.src.peek() == '*':
                nesting += 1

        # capture the final '/'
        self.src.getc()


    def scan_single_line_comment(self):
        while True:
            ch = self.src.getc();
            if ch == '\n' or self.src.is_eof():
                return

    def scan_identifier(self):
        ch = self.src.peek()
        while ch.isalnum() or ch == '_':
            self.src.pos += 1
            ch = self.src.peek()

    def scan_integer(self):
        ch = self.src.peek()
        while ch.isdecimal():
            self.src.pos += 1
            ch = self.src.peek()
    
    def scan_number(self):
        ch = self.src.peek()

        if ch == 'x':
            self.src.pos += 1
            if not is_hex(self.src.peek()):
                return self._make_token(TokenEnum.Invalid)

            while is_hex(self.src.peek()):
                self.src.pos += 1
            return self._make_token(TokenEnum.HexLiteral)

        self.scan_identifier()
        ch = self.src.peek()
        
        if ch == '.':
            self.src.pos += 1;
            ch = self.src.peek()

            if not ch.isdecimal():
                return self._make_token(TokenEnum.Invalid)

            self.scan_integer()
            ch = self.src.peek()

            if ch != 'e':
                return self._make_token(TokenEnum.FloatLiteral)

            self.src.pos += 1
            ch = self.src.peek()

            if not ch.isdecimal():
                return self._make_token(TokenEnum.Invalid)

            self.scan_integer()

            return self._make_token(TokenEnum.FloatLiteral)
        else:
            return self._make_token(TokenEnum.IntegerLiteral)

    def scan_char(self):
        ch = self.src.getc()

        if ch == '\\' and not self.scan_escape():
            return self._make_token(TokenEnum.Invalid)
        elif not ch.isprintable():
            return self._make_token(TokenEnum.Invalid)

        # capture the ending '\''
        ch = self.src.getc()
        if ch != '\'':
            return self._make_token(TokenEnum.Invalid)

        return self._make_token(TokenEnum.CharLiteral)

    def scan_string(self):
        ch = self.src.getc()

        while ch != '"':
            if not ch.isprintable():
                return self._make_token(TokenEnum.Invalid)

            if ch == '\\' and not self.scan_escape():
                return self._make_token(TokenEnum.Invlaid)

            ch = self.src.getc()

        return self._make_token(TokenEnum.StringLiteral)

    def next(self):
        while True:
            self.token_start = self.src.pos

            if self.src.is_eof():
                return self._make_token(TokenEnum.Eof)

            ch = self.src.getc()
            
            if ch == '\n':
                return self._make_token(TokenEnum.Newline)
            if ch.isspace():
                continue
            if ch == '#':
                self.scan_single_line_comment()
                continue
            if ch == '/' and self.src.peek() == '/':
                self.scan_single_line_comment()
                continue
            elif ch == '/' and self.src.peek() == '*':
                self.src.pos += 1 # pos++ because we already know it's valid
                self.scan_multiline_comment()
                continue

            elif ch.isdecimal():
                return self.scan_number()

            elif ch.isalpha() or ch == '_':
                self.scan_identifier()
                s = self.src.src[self.token_start: self.src.pos]
                return self._make_token(_KEYWORDS.get(s, TokenEnum.Identifier))

            elif ch == ':':
                return self._make_token(TokenEnum.Colon)
            elif ch == ',':
                return self._make_token(TokenEnum.Comma)
            elif ch == ';':
                return self._make_token(TokenEnum.Semicolon)
            elif ch == '@':
                return self._make_token(TokenEnum.Address)
            elif ch == '=':
                return self._make_token(TokenEnum.Assignment)

            elif ch == '(':
                return self._make_token(TokenEnum.LeftParen)
            elif ch == ')':
                return self._make_token(TokenEnum.RightParen)
            elif ch == '[':
                return self._make_token(TokenEnum.LeftSquare)
            elif ch == ']':
                return self._make_token(TokenEnum.RightSquare)
            elif ch == '{':
                return self._make_token(TokenEnum.LeftCurly)
            elif ch == '}':
                return self._make_token(TokenEnum.RightCurly)
            
            # Dots
            elif ch == '.' and self.src.peek() == '.':
                self.src.pos += 1
                if self.src.peek() != '.':
                    return self._make_token(TokenEnum.Invalid)
                return self._make_token(TokenEnum.Ellipsis)
            elif ch == '.':
                return self._make_token(TokenEnum.Period)
            
            elif ch == '\'':
                return self.scan_char()
            elif ch == '"':
                return self.scan_string()

            # Add
            elif ch == '+' and self.src.peek() == '+':
                self.src.pos += 1
                return self._make_token(TokenEnum.Increment)
            elif ch == '+' and self.src.peek() == '=':
                self.src.pos += 1
                return self._make_token(TokenEnum.AssignAdd)
            elif ch == '+':
                return self._make_token(TokenEnum.Addition)

            # Sub
            elif ch == '-' and self.src.peek() == '>':
                self.src.pos += 1
                return self._make_token(TokenEnum.Arrow)
            elif ch == '-' and self.src.peek() == '-':
                self.src.pos += 1
                return self._make_token(TokenEnum.Decrement)
            elif ch == '-' and self.src.peek() == '=':
                self.src.pos += 1
                return self._make_token(TokenEnum.AssignSub)
            elif ch == '-':
                return self._make_token(TokenEnum.Subtraction)

            # Asterisk
            elif ch == '*' and self.src.peek() == '=':
                self.src.pos += 1
                return self._make_token(TokenEnum.AssignMul)
            elif ch == '*':
                return self._make_token(TokenEnum.Asterisk)

            # Division
            elif ch == '/' and self.src.peek() == '=':
                self.src.pos += 1
                return self._make_token(TokenEnum.AssignDiv)
            elif ch == '/':
                return self._make_token(TokenEnum.Division)

            # Modulo
            elif ch == '%' and self.src.peek() == '=':
                self.src.pos += 1
                return self._make_token(TokenEnum.AssignMod)
            elif ch == '%':
                return self._make_token(TokenEnum.Modulo)

            # Not 
            elif ch == '~' and self.src.peek() == '=':
                self.src.pos += 1
                return self._make_token(TokenEnum.AssignNot)
            elif ch == '~':
                return self._make_token(TokenEnum.Not)

            # Xor
            elif ch == '^' and self.src.peek() == '=':
                self.src.pos += 1
                return self._make_token(TokenEnum.AssignXor)
            elif ch == '^':
                return self._make_token(TokenEnum.Xor)

            # Ampersand
            elif ch == '&' and self.src.peek() == '=':
                self.src.pos += 1
                return self._make_token(TokenEnum.AssignAnd)
            elif ch == '&':
                return self._make_token(TokenEnum.Ampersand)

            # Pipe
            elif ch == '|' and self.src.peek() == '=':
                self.src.pos += 1
                return self._make_token(TokenEnum.AssignPipe)
            elif ch == '|':
                return self._make_token(TokenEnum.Pipe)
            
            # Equal
            elif ch == '=' and self.src.peek() == '=':
                self.src.pos += 1
                return self._make_token(TokenEnum.AssignPipe)
            elif ch == '!' and self.src.peek() == '=':
                self.src.pos += 1
                return self._make_token(TokenEnum.AssignPipe)

            # Left
            elif ch == '<' and self.src.peek() == '<':
                self.src.pos += 1
                if self.src.peek() == '=':
                    self.src.pos += 1
                    return self._make_token(TokenEnum.AssignShiftLeft);
                else:
                    return self._make_token(TokenEnum.ShiftLeft)
            elif ch == '<' and self.src.peek() == '=':
                self.src.pos += 1
                return self._make_token(TokenEnum.LessThanOrEqual)
            elif ch == '<':
                return self._make_token(TokenEnum.LessThan)

            # Right 
            elif ch == '>' and self.src.peek() == '>':
                self.src.pos += 1
                if self.src.peek() == '=':
                    self.src.pos += 1
                    return self._make_token(TokenEnum.AssignShiftRight);
                else:
                    return self._make_token(TokenEnum.ShiftRight)
            elif ch == '>' and self.src.peek() == '=':
                self.src.pos += 1
                return self._make_token(TokenEnum.GreaterThanOrEqual)
            elif ch == '>':
                return self._make_token(TokenEnum.GreaterThan)

            else:
                return self._make_token(TokenEnum.Invalid)
