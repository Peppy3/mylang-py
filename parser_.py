from tokens import Token, TokenEnum
from parser_file import ParserFile
from lexer import Lexer

import ast_ as ast

PARSER_DEBUG: bool = 0 # note: bool is a subclass of int
parser_debug_uid: int = 0

def parser_func(func):
    if PARSER_DEBUG:
        def f(*args):
            global parser_debug_uid
            uid = parser_debug_uid
            parser_debug_uid += 1
            print(f"parser START: {func.__name__}", uid)
            print(*args)
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
        self.src.error(self.current, msg)

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

    def optional(self, typ):
        if self.current != typ:
            return None
        else:
            return self.next() 


    @parser_func
    def primary_expr(self):
        if self.current.type == TokenEnum.Identifier:
            return ast.Identifier(self.next())
        elif self.current.is_literal():
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
        elif self.current == TokenEnum.Period:
            op = self.next()
            if self.current != TokenEnum.Identifier:
                self._error(f"Expected identifier but got {self.current.type.name}")
                return None
            member = ast.Identifier(self.expect(TokenEnum.Identifier))
            return ast.BinaryExpr(op, primary, member)

        elif self.current.type == TokenEnum.LeftParen:
            lp = self.next()
            args = self.argument_expression_list()
            rp = self.expect(TokenEnum.RightParen)
            return ast.CallExpr(primary, lp, args, rp)
        elif self.current == TokenEnum.LeftSquare:
            ls = self.next()
            subscript = None
            if self.current != TokenEnum.RightSquare:
                subscript = self.assignment_expression()
            rs = self.expect(TokenEnum.RightSquare)
            return ast.Slice(primary, ls, subscript, rs)
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
    def binary_expression(self, lhs=None, min_precedence=1):
        if lhs is None:
            lhs = self.unary_expression()
        
        prec = self.current.precedence()

        while prec >= min_precedence:
            op = self.next()
            rhs = self.unary_expression()

            prec = self.current.precedence()

            while prec > op.precedence():
                op_prec = op.precedence()
                rhs = self.binary_expression(rhs, op_prec + (prec > op_prec))
                prec = self.current.precedence()

            lhs = ast.BinaryExpr(op, lhs, rhs)

        return lhs

    type_expression = lambda self: self.binary_expression()
    
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
        lp = self.expect(TokenEnum.LeftParen)
        args = self.declaration_list()
        rp = self.expect(TokenEnum.RightParen)
        arrow = self.expect(TokenEnum.Arrow)
        ret = self.type_expression()
        return ast.FuncType(lp, args, rp, arrow, ret)
        
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
        if self.current == TokenEnum.LeftParen:
            type_expr = self.function_type()
        else:
            type_expr = self.type_expression()

        return ast.Declaration(name, type_expr)

    @parser_func
    def declaration_statement(self):
        #pub = self.next() if self.current == TokenEnum.Pub else None
        #const = self.next() if self.current == TokenEnum.Const else None
        #macro = self.next() if self.current == TokenEnum.Macro else None
        
        decl = self.declaration()

        if self.current.type == TokenEnum.Assignment:
            self.next()
            decl.expr = self.expression_statement()
        elif self.current.type == TokenEnum.LeftCurly:
            decl.expr = self.code_block()
        else:
            self.expect(TokenEnum.Newline, TokenEnum.Semicolon)

        return decl

    @parser_func
    def compound_type(self):
        which = self.next()
        name = self.optional(TokenEnum.Identifier)
        members = self.code_block()
        return ast.CompoundType(which, name, members)

    @parser_func
    def return_statement(self):
        ret = self.expect(TokenEnum.Return)
        expr = self.expression()
        self.expect(TokenEnum.Newline, TokenEnum.Semicolon)
        return ast.ReturnStmt(ret, expr)

    @parser_func
    def statement(self):
        if self.current.type == TokenEnum.Identifier and self.lookahead.type == TokenEnum.Colon:
            return self.declaration_statement()
        elif self.current == TokenEnum.Newline:
            self.next()
            return None
        elif self.current == TokenEnum.Struct:
            return self.compound_type()
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
    def code_block(self):
        lc = self.expect(TokenEnum.LeftCurly)
        statements = self.statement_list()
        rc = self.expect(TokenEnum.RightCurly)
        return ast.CodeBlock(lc, statements, rc)

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

    return ast, parser.errors

