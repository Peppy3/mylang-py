from tokens import Token, TokenEnum

TABSPACE: int = "    "

class ParserFile:
    __slots__ = "filename", "src", "pos"
    def __init__(self, filename):
        self.filename = filename
        with open(filename, "r") as fp:
            self.src = fp.read()

        self.pos = 0

    def is_eof(self):
        return self.pos >= len(self.src)
    
    def getc(self):
        ch = self.src[self.pos]
        self.pos += 1
        return ch

    def peek(self):
        return self.src[self.pos]

    def error(self, tok, msg, end_msg=None):
        if tok == TokenEnum.Newline and len(self.get_line(tok)) != 0:
            # a bit of a hack
            tok = Token(TokenEnum.Newline, tok.pos - 1, tok.length)

        line_pos, col_pos = self.get_tok_human_pos(tok)
        line_str = self.get_line(tok)
        
        print(f"{self.filename}:{line_pos}:{col_pos}: ERROR: {msg}")
        if line_str is None:
            print("EOF")
            return

        print(line_str.expandtabs(len(TABSPACE)))
        print("".join(TABSPACE if line_str[i] == '\t' else " " for i in range(col_pos - 1)) + '^' * tok.length)
        if end_msg is not None: print(end_msg)
    
    def get_token_string(self, tok):
        if tok.pos == len(self.src):
            return "EOF"
        return self.src[tok.pos : tok.pos + tok.length]

    def get_tok_human_pos(self, tok):
        line = 1
        col = 0
        
        pos = 0
        for ch in self.src:
            col += 1
            if ch == '\n':
                line += 1
                col = 0
            if pos >= tok.pos:
                break
            pos += 1

        return (line, col)

    def get_line(self, tok):
        
        pos = 0
        for line in self.src.splitlines():
            new_pos = pos + len(line) + 1

            if new_pos > tok.pos:
                return line

            pos = new_pos
        
        return None
