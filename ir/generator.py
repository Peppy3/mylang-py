from pprint import pprint
import ir.core as ir

from tokens import TokenEnum
import ast_ as ast

BUILTIN_TYPES: dict = {
    "i8": ir.IntType(None, 8),
    "i16": ir.IntType(None, 16),
    "i32": ir.IntType(None, 32),
    "i64": ir.IntType(None, 64),

    "u8": ir.UintType(None, 8),
    "u16": ir.UintType(None, 16),
    "u32": ir.UintType(None, 32),
    "u64": ir.UintType(None, 64),

    "f16": ir.FloatType(None, 16),
    "f32": ir.FloatType(None, 32),
    "f64": ir.FloatType(None, 64),

    "int": ir.IntType(None, 64),
    "uint": ir.IntType(None, 64),
    "bool": ir.BoolType(None),
    "void": ir.VoidType(None),
    "type": ir.TypeType(None),

    "struct": ir.StructType(None),
}

class IrGenerator:
    __slots__ = "src", "blocks", "num_errors"
    def __init__(self, src):
        self.src = src
        self.blocks = list()
        self.num_errors = 0

    def error(self, token, msg):
        self.num_errors += 1
        self.src.error(token, msg)

    def lookup(self, name):
        return self.blocks[-1].lookup(name)

    def type_expression(self, node):
        if node.isa(ast.Literal) and node.token == TokenEnum.Identifier:
            typename = self.src.get_token_string(node.token)
            
            if (typ := BUILTIN_TYPES.get(typename)) is not None:
                return typ

            typ = self.lookup(typename)

            if typ is None:
                self.error(node.token, f"type {typename!r} is not found")
            
            if not isinstance(typ.type, (ir.StructType, ir.SliceType)):
                print(typ.__class__.__name__)
                self.error(node.token, f"type {typename!r} is not a type")

            return typ
        elif node.isa(ast.UnaryExpr):
            if node.op != TokenEnum.Asterisk:
                return self.error(node.op, 
                    f"Can not have unary {node.op.type.name} in type expression")
            expr = self.type_expression(node.expr)
            return ir.PointerType(node.op, expr)
        elif node.isa(ast.FuncType):
            func = ir.FuncType(None, list())
            
            for arg in node.args:
                name = self.src.get_token_string(arg.name)
                typ = self.type_expression(arg.type_expr)
                func.args.append((typ, name))

            func.ret = self.type_expression(node.ret)
            return func
        elif node.isa(ast.PostfixExpr):
            return self.error(node.op, f"Can not have postfix operation in type expression")
        elif node.isa(ast.BinaryExpr):
            return self.error(node.op, f"Can not have binary operation in type expression")
        elif node.isa(ast.Literal):
            return self.error(node.op, f"Can not have a literal in type expression")
        else:
            raise NotImplementedError(type(node))

    def unary_expression(self, node):
        raise NotImplementedError(type(node.op))

    def binary_expression(self, node):
        lhs: ir.Value = self.expression(node.lhs)
        rhs: ir.Value = self.expression(node.rhs)

        if node.op == TokenEnum.Period:
            struct = self.blocks[-1].lookup(lhs)
            print(lhs.type, rhs.type)
            
            if isinstance(struct.type, (ir.StructType, ir.SliceType)):
                self.error(node.lhs.token, f"{lhs} is not a struct or a slice")

            return self.blocks[-1].build_member_access(rhs.type, lhs, rhs)
        
        if lhs.type != rhs.type:
            self.error(node.op, f"{lhs} does not have the same type as {rhs}")

        if node.op.type == TokenEnum.Addition:
            return self.blocks[-1].build_add(lhs.type, lhs, rhs)
        elif node.op.type == TokenEnum.Asterisk:
            return self.blocks[-1].build_mul(lhs.type, lhs, rhs)
        else:
            raise NotImplementedError(node.op.type.name)
    
    def expression(self, node):
        if node.isa(ast.Literal):
            if node.token == TokenEnum.Identifier:
                name = self.src.get_token_string(node.token)

                if name == "true":
                    return ir.Constant(node.token, ir.BoolType(None), True)
                elif name == "false":
                    return ir.Constant(node.token, ir.BoolType(None), False)
                elif name == "null":
                    return ir.Constant(node.token, ir.PointerType(None, VoidType(None)), 0)

                val = self.lookup(name)

                if val is None:
                    self.error(node.token, f"{name!r} is not defined")
                    return None
                else:
                    return val
            elif node.token == TokenEnum.IntegerLiteral:
                integer = self.src.get_token_string(node.token)
                return ir.Constant(node.token, ir.IntType(node.token), int(integer, 10))
            elif node.token == TokenEnum.FloatLiteral:
                f = self.src.get_token_string(node.token)
                return ir.Constant(node.token, ir.FloatType(node.token), float(f))
            elif node.token == TokenEnum.StringLiteral:
                s = self.src.get_token_string(node.token)
                raw_str = bytearray(s[1:-1], "utf-8")
                raw_str.append(0) # append null char
                str_slice = ir.SliceType(node.token, ir.UintType(None, 8), len(raw_str))
                return ir.Constant(node.token, str_slice, raw_str)

        elif node.isa(ast.BinaryExpr):
            return self.binary_expression(node)

        elif node.isa(ast.CallExpr):
            func_name = self.src.get_token_string(node.name.token)
            arg_exprs = list()

            func_val = self.blocks[-1].lookup(func_name)
            if func_val is None:
                self.error(node.name.token, f"{func_name!r} is not defined")
            
            func_val_arglen = len(func_val.type.args)
            args_len = len(node.args)
            if func_val_arglen != args_len:
                if func_val_arglen > args_len:
                    self.error(node.name.token,
                        f"Too few aruments to funciton call. Expected {func_val_arglen}")
                else:
                    self.error(node.name.token,
                        f"Too many arguments passed to funcion call. Expected {func_val_arglen}")

            for func_val_arg, arg in zip(func_val.type.args, node.args):
                expr = self.expression(arg)
                if func_val_arg[0] != expr.type:
                    self.error(node.name.token, 
                        f"{expr.type} is not of type {func_val_arg[0]}")
                arg_exprs.append(expr)

            ret = self.blocks[-1].build_call(func_val.type.ret, func_name, arg_exprs)
            return ret

        raise NotImplementedError(type(node))

    def declaration(self, node):
        name = self.src.get_token_string(node.name)
        typ = self.type_expression(node.type_expr)
        
        val = self.blocks[-1].value(node.name, typ, name)

        if node.expr is None:
            return 

        if node.type_expr.isa(ast.FuncType):
            block = self.blocks[-1].block(typ, name)
            self.blocks.append(block)
            
            for arg in typ.args:
                self.blocks[-1].value(None, *arg)

            for stmt in node.expr:
                self.statement(stmt)

            block = self.blocks.pop()
            self.blocks[-1].build_move(typ, val, block)
        
        elif isinstance(node.expr, list):
            block = self.blocks[-1].block(typ, name)
            
            self.blocks[-1].build_move(typ, val, block)

            self.blocks.append(block)

            for stmt in node.expr:
                self.statement(stmt)

            block = self.blocks.pop()
        else:
            expr = self.expression(node.expr)
            self.blocks[-1].build_move(typ, val, expr)

    def statement(self, node):
        if node.isa(ast.Declaration):
            self.declaration(node)
            return 
        elif node.isa(ast.ReturnStmt):
            expr = self.expression(node.expr)
            self.blocks[-1].build_ret(expr.type, expr)
            return 
        else:
            self.expression(node)

    def module(self, node):
        name = self.src.get_token_string(node.name)
        mod = ir.Block(ir.ModuleType(node.name), None, name)
        self.blocks.append(mod)
        
        for stmt in node.statements:
            self.statement(stmt)

        self.blocks.pop()
        return mod
    

    def generate(self, node):
        mod = self.module(node)
        return mod


def generate(src, ast):

    generator = IrGenerator(src)
    
    rep = generator.generate(ast)
    assert len(generator.blocks) == 0
    print(rep.dissasemble())

    return generator.num_errors, rep


