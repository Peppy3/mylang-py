from pprint import pprint
import ir.core as ir
from ir.core import OpEnum

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
}

class IrGenerator:
    __slots__ = "src", "blocks", "next_uid", "num_errors"
    def __init__(self, src):
        self.src = src
        self.blocks = list()
        self.next_uid = 0
        self.num_errors = 0


    def error(self, token, msg):
        self.num_errors += 1
        self.src.error(token, msg)

    
    def append(self, instr):
        self.blocks[-1].append(instr)


    # don't bother converting to a str as int is hashable
    def gen_uid(self):
        uid = self.next_uid
        self.next_uid += 1
        return uid


    def unary_expression(self, node, is_type_expr):
        expr = self.generate(node.expr, is_type_expr)
        
        ret = self.gen_uid()

        if is_type_expr:
            if node.op == TokenEnum.Asterisk:
                self.append(ir.Instr(OpEnum.POINTER_TYPE, node, True, ret, expr))
                return ret
            else:
                self.error(node.op, f"Unary '*' and macro calls are allowed in type expressions")

        raise NotImplementedError(node.op)

        
    def binary_expression(self, node, is_type_expr=False):
        lhs = self.generate(node.lhs, is_type_expr)
        rhs = self.generate(node.rhs, is_type_expr)
        
        ret = self.gen_uid()

        if node.op == TokenEnum.Addition:
            self.append(ir.Instr(OpEnum.BIN_ADD, node, is_type_expr, ret, lhs, rhs))
            return ret
        elif node.op == TokenEnum.Asterisk:
            self.append(ir.Instr(OpEnum.BIN_MUL, node, is_type_expr, ret, lhs, rhs))
            return ret
        elif node.op == TokenEnum.Period:
            self.append(ir.Instr(OpEnum.MEMBER_ACCESS, node, is_type_expr, ret, lhs, rhs))
        else:
            raise NotImplementedError(node.op)

    def generate(self, node, is_type_expr=False):
        match node:
            case ast.Module(name, statements):
                self.blocks.append(list())

                self.append(ir.Instr(OpEnum.MODULE, node, is_type_expr, name))
                
                for stmt in statements:
                    self.generate(stmt)
                
                return self.blocks.pop()

            case ast.CompoundType(which, name, statements):
                self.blocks.append(list())

                for stmt in statements:
                    self.generate(stmt)
                
                block = self.blocks.pop()
                self.append(ir.Instr(OpEnum.COMPOUND_TYPE, node, is_type_expr, which, name, block))

            case ast.Declaration(name, type_expr=ast.FuncType(), expr=ast.CodeBlock() | None):
                
                arg_list = list()
                for arg in node.type_expr.args:
                    if not arg.isa(ast.Declaration):
                        self.error(arg, "Function argument declaration is not an argument")
                    elif arg.expr is not None:
                        self.error(arg, 
                            "Function argument can not have a default argument as of right now")
                    else:
                        arg_type = self.generate(arg, True)
                        arg_list.append((name, arg_type))

                return_val = self.generate(node.type_expr.ret, True)
                
                block = None
                if node.expr is not None:
                    self.blocks.append(list())

                    for stmt in node.expr:
                        self.generate(stmt)
                    
                    block = self.blocks.pop()
                
                self.append(
                    ir.Instr(OpEnum.FUNC_DECL, node, is_type_expr, 
                        name, return_val, arg_list, block
                    )
                )
        
            case ast.Declaration(name, type_expr, expr):
                # var decl
                typ = self.generate(type_expr, True)
                val = None
                if expr is not None:
                    val = self.generate(expr)

                self.append(ir.Instr(OpEnum.VAR_DECL, node, is_type_expr, name, typ, val))
                
            case ast.Identifier(name):
                return name

            case ast.Literal(val):
                return val

            case ast.BinaryExpr():
                return self.binary_expression(node, is_type_expr)

            case ast.UnaryExpr():
                return self.unary_expression(node, is_type_expr)

            case ast.CallExpr():
                func = self.generate(node.func)

                arg_list = list()
                for arg in node.args:
                    arg_list.append(self.generate(arg))

                ret = self.gen_uid()

                self.append(ir.Instr(OpEnum.FUNC_CALL, node, is_type_expr, ret, arg_list))

                return ret

            case ast.Slice() if is_type_expr:
                typ = self.generate(node.expr, True)
                subscript = None
                if node.subscript is not None:
                    self.generate(node.subscript)

                ret = self.gen_uid()
                self.append(ir.Instr(OpEnum.SLICE_TYPE, node, is_type_expr, True, subscript))

            case ast.Slice():
                expr = self.generate(node.expr)
                if node.subscript is None:
                    self.error(node.subscript, "Empty subscript in slice expression")
                    return None
                else:
                    subscript = self.generate(node.subscript)
                    self.append(ir.Instr(OpEnum.SLICE_INDEXING, node, is_type_expr, subscript))

            case ast.ReturnStmt(ret, expr):
                if expr is not None:
                    expr = self.generate(expr)

                self.append(ir.Instr(OpEnum.RETURN_STMT, node, is_type_expr, expr))
                
            case _:
                raise NotImplementedError(node)

        

def generate(src, ast):

    generator = IrGenerator(src)
    
    rep = generator.generate(ast)
    #assert len(generator.symbol_stack) == 0
    #pprint(rep, depth=2)

    return generator.num_errors, rep


