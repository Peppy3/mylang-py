from tokens import Token, TokenEnum
from parser_file import ParserFile
from lexer import Lexer

import ast_ as ast

TABSPACE: int = 4

PARSER_DEBUG: bool = True
parser_debug_uid: int = 0

def parser_func(func):
    if PARSER_DEBUG:
        def f(*args):
            global parser_debug_uid
            uid = parser_debug_uid
            parser_debug_uid += 1
            print(f"parser START: {func.__name__}", uid)
            ret = func(*args)
            print(f"parser END: {func.__name__}", uid)
            return ret
        return f
    return func

class Parser:
    __slots__ = "src", "errors", "lexer", "current", "lookahead"
    def __init__(self, filename, src):
        self.src = src
        self.errors = 0

        self.lexer = Lexer(self.src)

        self.current = self.lexer.next()
        self.lookahead = self.lexer.next()

    def _error(self, msg):
        self.errors += 1

        if self.current == TokenEnum.Newline and len(self.src.get_line(self.current)) != 0:
            # a bit of a hack
            self.current = Token(TokenEnum.Newline, self.current.pos - 1, self.current.length)

        line_pos, col_pos = self.src.get_tok_human_pos(self.current)
        line_str = self.src.get_line(self.current)
        
        print(f"{self.src.filename}: {line_pos}:{col_pos} {msg}")
        if line_str is None:
            print("EOF")
            return

        print(line_str.expandtabs(TABSPACE))
        for i in range(col_pos - 1):
            if line_str[i] == '\t':
                print(" ", end="")
            else:
                print(" ", end="")
        print("^" if self.current != TokenEnum.Newline else " ^")

    def next(self):
        tok = self.current
        self.current = self.lookahead
        self.lookahead = self.lexer.next()
        return tok

    def expect(self, *types):
        if self.current.type not in types:
            self._error(f"Expected {' or '.join(typ.name for typ in types)} but got {self.current.type.name}")
            self.next()
            return None
        else:
            return self.next()

    @parser_func
    def primary_expr(self):
        if self.current.type == TokenEnum.Identifier:
            return ast.Literal(self.next())
        if self.current.type == TokenEnum.IntegerLiteral:
            return ast.Literal(self.next())
        elif self.current.type == TokenEnum.IntegerLiteral:
            return ast.Literal(self.next())
        elif self.current.type == TokenEnum.HexLiteral:
            return ast.Literal(self.next())
        elif self.current.type == TokenEnum.FloatLiteral:
            return ast.Literal(self.next())
        elif self.current.type == TokenEnum.CharLiteral:
            return ast.Literal(self.next())
        elif self.current.type == TokenEnum.StringLiteral:
            return ast.Literal(self.next())
        elif self.current.type == TokenEnum.LeftParen:
            self.expect(TokenEnum.LeftParen)
            expr = self.expression()
            self.expect(TokenEnum.RightParen)
            return expr
        else:
            self._error(f"Expected literal or expression but got {self.current.type.name}")
            self.next()
            return None

    @parser_func
    def argument_expression_list(self):
        args = list()

        while self.current != TokenEnum.RightParen and self.current != TokenEnum.Eof:
            args.append(self.expression())

            if self.current != TokenEnum.Comma:
                break

            self.expect(TokenEnum.Comma)

        return args
    
    @parser_func
    def postfix_expression(self, primary=None):
        if primary is None:
            primary = self.primary_expr()

        if self.current.type == TokenEnum.Increment:
            return ast.PostfixExpr(self.next(), primary)
        elif self.current.type == TokenEnum.Decrement:
            return ast.PostfixExpr(self.next(), primary)
        elif self.current.type == TokenEnum.LeftParen:
            self.next()
            args = self.argument_expression_list()
            self.expect(TokenEnum.RightParen)
            return ast.CallExpr(primary, args)
        else:
            return primary

    @parser_func
    def unary_expression(self):
        if not self.current.is_unary():
            return self.postfix_expression()
        else:
            op = self.next()
            return ast.UnaryExpr(op, self.unary_expression())

    @parser_func
    def binary_expression(self, lhs=None, min_precedence=0):
        if lhs is None:
            lhs = self.unary_expression()

        while True:
            op_prec = self.current.precedence()

            if op_prec < 1:
                return lhs

            op = self.next()
            rhs = self.binary_expression(None, op_prec + 1)
            
            tmp = ast.BinaryExpr(op, lhs, rhs)
            lhs = tmp

    type_expression = binary_expression
    
    @parser_func
    def assignment_expression(self):
        lhs = self.binary_expression()

        if TokenEnum.ASSIGNMENT_START > self.current.type or self.current.type > TokenEnum.ASSIGNMENT_END:
            return lhs

        op = self.next()
        rhs = self.binary_expression()
        return ast.BinaryExpr(op, lhs, rhs)

    expression = assignment_expression

    @parser_func
    def expression_statement(self):
        expr = self.expression()
        self.expect(TokenEnum.Newline, TokenEnum.Semicolon)
        return expr

    @parser_func
    def function_type(self):
        # (x: int, y:int) ->int
        self.expect(TokenEnum.LeftParen)
        args = self.declaration_list()
        self.expect(TokenEnum.RightParen)
        self.expect(TokenEnum.Arrow)
        ret = self.type_expression()
        return ast.FuncType(args, ret)
        
    @parser_func
    def declaration_list(self):
        decls = list()
        while True:
            if self.current.type == TokenEnum.RightParen:
                return decls
            
            decls.append(self.declaration())

            if self.current.type != TokenEnum.Comma:
                return decls
            self.next()

    
    @parser_func
    def declaration(self):
        name = self.expect(TokenEnum.Identifier)
        self.expect(TokenEnum.Colon)
        
        type_expr = None
        if self.current.type == TokenEnum.LeftParen:
            type_expr = self.function_type()
        else:
            type_expr = self.type_expression()

        return ast.Declaration(name, type_expr, None, pub, const, macro)

    @parser_func
    def declaration_statement(self):
        pub = self.next() if self.current == TokenEnum.Pub else None
        const = self.next() if self.current == TokenEnum.Const else None
        macro = self.next() if self.current == TokenEnum.Macro else None
        
        decl = self.declaration()

        if self.current.type == TokenEnum.Assignment:
            self.next()
            decl.expr = self.expression_statement()
        elif self.current.type == TokenEnum.LeftCurly:
            decl.expr = self.compound_statement()
        else:
            self.expect(TokenEnum.Newline, TokenEnum.Semicolon)

        return decl

    @parser_func
    def return_statement(self):
        self.expect(TokenEnum.Return)
        expr = self.expression()
        self.expect(TokenEnum.Newline, TokenEnum.Semicolon)
        return ast.ReturnStmt(expr)

    @parser_func
    def statement(self):
        if self.current.type == TokenEnum.Identifier and self.lookahead.type == TokenEnum.Colon:
            return self.declaration_statement()
        elif self.current == TokenEnum.Newline:
            self.next()
            return None
        elif self.current.type == TokenEnum.Return:
            return self.return_statement()
        else:
            return self.expression_statement()

    @parser_func
    def statement_list(self):
        statements = list()
        while self.current.type != TokenEnum.RightCurly and self.current.type != TokenEnum.Eof:
            stmt = self.statement()
            if stmt is not None:
                statements.append(stmt)

        return statements

    @parser_func
    def compound_statement(self):
        self.expect(TokenEnum.LeftCurly)
        statements = self.statement_list()
        self.expect(TokenEnum.RightCurly)
        return statements

    @parser_func
    def module(self):

        if self.current.type != TokenEnum.Module:
            self._error("No module statement at the start of file")
            return None

        module = self.next()

        name = self.expect(TokenEnum.Identifier)
        if name is None: return None

        semi = self.expect(TokenEnum.Newline, TokenEnum.Semicolon)
        if semi is None: return None

        statements = None
        if self.current.type == TokenEnum.Eof:
            statements = [ast.Literal(self.next())]
        else:
            statements = self.statement_list()

        return ast.Module(name, statements)

def parse(filename, src):
    parser = Parser(filename, src)
    ast = parser.module()

    return parser.errors, ast

