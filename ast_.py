from abc import ABC, abstractmethod
from dataclasses import dataclass

from tokens import Token

def walk_func(func):
    def f(self, visitor):
        visitor = visitor.visit(self)
        if visitor is None: 
            return None
        func(self, visitor)
        visitor.visit(None)

    return f

def walk_list(l, visitor):
    for node in l:
        visitor.visit(node)

class Node(ABC):
    @abstractmethod
    def walk(self, visitor):
        pass
    
    def __str__(self):
        return f"ast.{self.__class__.__name__}"

    def isa(self, cls):
        return isinstance(self, cls)


@dataclass(slots=True, repr=True)
class Identifier(Node):
    token: Token

    @walk_func
    def walk(self, visitor):
        pass

@dataclass(slots=True, repr=True)
class Literal(Node):
    token: Token

    @walk_func
    def walk(self, visitor):
        pass

@dataclass(slots=True, repr=True)
class CallExpr(Node):
    name: Token
    args: list
    
    @walk_func
    def walk(self, visitor):
        for arg in args: arg.val.walk(visitor)

@dataclass(slots=True, repr=True)
class PostfixExpr(Node):
    op: Token
    expr: Node
    
    @walk_func
    def walk(self, visitor):
        if self.val is not None: self.val.walk(visitor)

@dataclass(slots=True, repr=True)
class UnaryExpr(Node):
    op: Token
    expr: Node

    @walk_func
    def walk(self, visitor):
        if self.expr is not None: self.expr.walk(visitor)


@dataclass(slots=True, repr=True)
class BinaryExpr(Node):
    op: Token
    lhs: Node
    rhs: Node
    
    @walk_func
    def walk(self, visitor):
        if self.lhs is not None: self.lhs.walk(visitor)
        if self.rhs is not None: self.rhs.walk(visitor)


@dataclass(slots=True, repr=True)
class FuncType(Node):
    args: list
    ret: Node

    @walk_func
    def walk(self, visitor):
        for arg in self.args: visitor.visit(arg)
        
        visitor.visitor(self.ret)

@dataclass(slots=True, repr=True)
class ReturnStmt(Node):
    expr: Node | None

    @walk_func
    def walk(self, visitor):
        if self.expr is not None: self.expr.walk(visitor)

@dataclass(slots=True, repr=True)
class Declaration(Node):
    name: Token
    type_expr: Node
    expr: Node | None = None

    @walk_func
    def walk(self, visitor):
        if self.type_expr is not None: self.type_expr.walk(visitor)
        if self.expr is not None: self.expr.walk(visitor)

@dataclass(slots=True, repr=True)
class Module(Node):
    name: Token 
    statements: list
    
    @walk_func
    def walk(self, visitor):
        for stmt in self.statements: visitor.visit(self)
