from pprint import pprint
from dataclasses import dataclass
from tokens import Token, TokenEnum
from parser_file import ParserFile
import ast_ as ast

VALIDATOR_DEBUG: bool = False
validator_debug_uid: int = 0

def validate_func(func):
    if VALIDATOR_DEBUG:
        def f(*args):
            global validator_debug_uid
            uid = validator_debug_uid
            validator_debug_uid += 1
            arg_names = ', '.join(arg.__class__.__name__ for arg in args)
            print(f"validator START: {func.__name__}({arg_names})", uid)
            ret = func(*args)
            print(f"validator END: {func.__name__}", uid)
            return ret
        return f
    return func


class Validator:
    __slots__ = "src", "errors", "scopes"
    def __init__(self, src):
        self.src = src
        self.errors = 0
        self.scopes= list()
    
    validate = lambda self, ast: self.module(ast)

    def _error(self, token, msg):
        self.errors += 1

        line_pos, col_pos = self.src.get_tok_human_pos(token)
        line_str = self.src.get_line(token)
        
        print(f"{self.src.filename}: {line_pos}:{col_pos} {msg}")
        if line_str is None:
            print("EOF")
            return

        print(line_str.expandtabs(4))
        for i in range(col_pos - 1):
            if line_str[i] == '\t':
                print("\t", end="")
            else:
                print(" ", end="")
        print("^")
        return True

    @validate_func
    def type_expr(self, node: ast.Node) -> bool:

        if node.isa(ast.Literal) and node.token.type == TokenEnum.Identifier:
            return False
        elif node.isa(ast.CallExpr):
            error = False
            for arg in node.args:
                error |= self.expression(arg)
            return error
        elif node.isa(ast.FuncType):
            error = False
            for arg in node.args:
                error |= self.declaration(arg)
            if not error:
                return error
            return self.type_expr(node.ret)
        elif node.isa(ast.UnaryExpr):
            if node.op != TokenEnum.Asterisk:
                return self._error(node.op, 
                    f"Can not have unary {node.op.type.name} in type expression")
            return self.type_expr(node.expr)
        elif node.isa(ast.PostfixExpr):
            return self._error(node.op, f"Can not have postfix operation in type expression")
        elif node.isa(ast.BinaryExpr):
            return False
        else:
            raise NotImplementedError(node.__class__.__name__)

    @validate_func
    def expression(self, node: ast.Node | list[ast.Node]) -> bool:
        if isinstance(node, list): # block statement
            error = False
            for stmt in node:
                error |= self.statement(stmt)
            return error
        elif node.isa(ast.Literal):
            return False 
        elif node.isa(ast.BinaryExpr):
            return self.expression(node.lhs) or self.expression(node.rhs)
        elif node.isa(ast.PostfixExpr):
            return self.expression(node.expr)
        elif node.isa(ast.UnaryExpr):
            return self.expression(node.expr)
        elif node.isa(ast.CallExpr):
            error = False
            for arg in node.args:
                error |= self.expression(arg)
            return error
            
        raise NotImplementedError(node.__class__.__name__)

    @validate_func
    def declaration(self, node: ast.Node) -> bool:
        if self.type_expr(node.type_expr):
            return True

        if node.expr is None:
            return False

        return self.expression(node.expr)

    @validate_func
    def statement(self, node: ast.Node) -> bool:
        
        if node.isa(ast.Declaration):
            return self.declaration(node)
        elif node.isa(ast.BinaryExpr):
            return self.expression(node)
        elif node.isa(ast.PostfixExpr):
            return self.expression(node)
        elif node.isa(ast.UnaryExpr):
            return self.expression(node)
        elif node.isa(ast.CallExpr):
            return self.expression(node)
        elif node.isa(ast.ReturnStmt):
            return self.expression(node.expr)

        raise NotImplementedError(node.__class__.__name__)

    @validate_func
    def module(self, node: ast.Node) -> bool:
        self.scopes.append("module")
        error = False
        for stmt in node.statements:
            error |= self.statement(stmt)
        self.scopes.pop()
        return error

def validate(src: ParserFile, ast: ast.Node):
    validator = Validator(src)
    validator.validate(ast)
    return validator.errors


