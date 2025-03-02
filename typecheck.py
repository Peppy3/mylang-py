from tokens import TokenEnum
import ast_ as ast
from symbol_table import SymbolTable

class Type:
    __slots__ = ("token",)
    def __init__(self, token):
        self.token = token

    def __eq__(self, other):
        return isinstance(other, Type) and self.__class__ == other.__class__
    
    __repr__ = lambda self: self.__class__.__name__


class PointerType(Type):
    __slots__ = ("to",)
    def __init__(self, token, to):
        super().__init__(token)
        self.to = to
    __str__ = lambda self: f"*{str(self.to)}"
    __eq__ = lambda self, other: isinstance(other, Pointer) and self.to == other.to

class BlockType(Type):
    __str__ = lambda self: "block"

class TypeType(Type):
    __str__ = lambda self: "type"

class BoolType(Type):
    __str__ = lambda self: "bool"

class VoidType(Type):
    __str__ = lambda self: "void"

class StructType(Type):
    __str__ = lambda self: "struct"

class IntType(Type):
    __slots__ = ("bit_length",)
    def __init__(self, token, bit_length=64):
        super().__init__(token)
        self.bit_length = bit_length
    
    __str__ = lambda self: f"i{self.bit_length}"

    def __eq__(self, other):
        return isinstance(other, IntType) and self.bit_length == other.bit_length

class UintType(Type):
    __slots__ = ("bit_length",)
    def __init__(self, token, bit_length=64):
        super().__init__(token)
        self.bit_length = bit_length
    
    __str__ = lambda self: f"u{self.bit_length}"

    def __eq__(self, other):
        return isinstance(other, UintType) and self.bit_length == other.bit_length

class FloatType(Type):
    __slots__ = ("bit_length",)
    def __init__(self, token, bit_length=64):
        super().__init__(token)
        self.bit_length = bit_length
    
    __str__ = lambda self: f"f{self.bit_length}"

    def __eq__(self, other):
        return isinstance(other, FloatType) and self.bit_length == other.bit_length

class FuncType(Type):
    __slots__ = "ret", "args"
    def __init__(self, ret, args):
        self.ret = ret
        self.args = args

    def __repr__(self):
        gen = (arg.name if isinstance(arg, Block) else str(arg) for arg in self.args)
        return "(" + ", ".join(gen) + f") -> {self.ret}" 

    def __eq__(self, other):
        if not isinstance(other, FuncType) or self.ret != other.ret:
            return False
            
        if len(self.args) != len(other.args):
            return False
        
        for s_arg, o_arg in zip(self.args, other.args):
            if s_arg != o_arg:
                return False
        
        return True

    def append_arg(self, name, typ):
        self.args.append((name, typ))


class SliceType(Type):
    __slots__ = "len", "type"
    def __init__(self, typ, length):
        self.type = typ
        self.len = length

    __str__ = lambda self: f"{str(self.type)}[{self.len}]"


BUILTIN_TYPES: list = [
    ("i8", IntType(None, 8)),
    ("i16", IntType(None, 16)),
    ("i32", IntType(None, 32)),
    ("i64", IntType(None, 64)),
    ("int", IntType(None)),

    ("u8", UintType(None, 8)),
    ("u16", UintType(None, 16)),
    ("u32", UintType(None, 32)),
    ("u64", UintType(None, 64)),
    ("uint", UintType(None)),
]


class Typechecker:
    __slots__ = "symbol_stack", "src", "num_errors"
    def __init__(self, src):
        self.symbol_stack = [SymbolTable(BUILTIN_TYPES)]
        self.src = src
        self.num_errors = 0

        
    def error(self, token, msg):
        self.num_errors += 1
        self.src.error(token, msg)
    

    def lookup(self, name):
        for table in reversed(self.symbol_stack):
            if (symbol := table.get(name)) is not None:
                return symbol
        return None


    def insert(self, name, val):
        self.symbol_stack[-1].insert(name, val)


    def type_expression(self, node):
        if node.isa(ast.Identifier):
            name = self.src.get_token_string(node.token)
            
            typ = self.lookup(name)
            if typ is None:
                self.error(node.token, f"Could not resolve type {name!r}")
                return
            return typ
        elif node.isa(ast.FuncType):
            ret_type = self.type_expression(node.ret)
            func_type = FuncType(ret_type, list())
            
            for arg in node.args:
                name = self.src.get_token_string(arg.name)
                arg_type = self.type_expression(arg.type_expr)
                func_type.append_arg(name, arg_type)

        elif node.isa(ast.UnaryExpr):
            if node.op == TokenEnum.Asterisk:
                typ = self.type_expression(node.expr)
                return PointerType(node.op, typ)
            else:
                self.error(node.op, f"Unary {node.op.type.name} not allowed in type expressions")
        else:
            raise NotImplementedError(node)

    def expression(self, node):
        if node.isa(ast.BinaryExpr):
            lhs = self.expression(node.lhs)
            rhs = self.expression(node.rhs)

            if lhs is None or rhs is None:
                return None

            if isinstance(lhs, PointerType) or isinstance(rhs, PointerType):
                self.error(node.op, f"No pointer arithmatic allowed")
                return None
            elif isinstance(lhs, FuncType) or isinstance(rhs, FuncType):
                self.error(node.op, f"Can not use binary operator on a function")
                return None

            if node.op == TokenEnum.Addition:
                if lhs != rhs:
                    self.error(node.op, f"lhs does not have the same type as rhs")
                    return None
                return lhs
            elif node.op == TokenEnum.Asterisk:
                if lhs != rhs:
                    self.error(node.op, f"lhs does not have the same type as rhs")
                    return None
                return lhs
            else:
                raise NotImplementedError(node.op)
        elif node.isa(ast.Literal):
            if node.token == TokenEnum.IntegerLiteral:
                return IntType(node.token)
            else:
                raise NotImplementedError(node.token)
        else:
            raise NotImplementedError(node)

    def module(self, node):
        for stmt in node.statements:
            if stmt.isa(ast.Declaration):
                name = self.src.get_token_string(stmt.name)
                typ = self.type_expression(stmt.type_expr)
                
                if stmt.expr is None:
                    continue

                self.expression(stmt.expr)

            elif stmt.isa(ast.BinaryExpr):
                self.error(stmt.op, "Module scope can only have declarations")
            else:
                raise NotImplementedError(f"module scope error for {stmt}")


    def typecheck(self, ast):
        
        self.module(ast)

        return self.num_errors



def validate_and_resolve_types(src, ast):
    num_errors = Typechecker(src).typecheck(ast)
    
    return num_errors

