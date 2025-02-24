from abc import ABC, abstractmethod
from dataclasses import dataclass

from tokens import Token

def tab(num):
	return "  " * num

class AstVisitor(ABC):
	@abstractmethod
	def visit(self, node):
		raise NotImplemented

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

class AstNode(ABC):
	@abstractmethod
	def walk(self, visitor):
		raise NotImplemented
	
	def isa(self, cls):
		return isinstance(self, cls)

@dataclass
class Literal(AstNode):
	tok: Token

	@walk_func
	def walk(self, visitor):
		pass


@dataclass
class CallExpr(AstNode):
	func: Token
	args: list
	
	@walk_func
	def walk(self, visitor):
		for arg in args: arg.val.walk(visitor)

@dataclass
class PostfixExpr(AstNode):
	op: Token
	val: AstNode
	
	@walk_func
	def walk(self, visitor):
		if self.val is not None: self.val.walk(visitor)

@dataclass
class UnaryExpr(AstNode):
	op: Token
	val: AstNode

	@walk_func
	def walk(self, visitor):
		if self.val is not None: self.val.walk(visitor)


@dataclass
class BinaryExpr(AstNode):
	op: Token
	lhs: AstNode
	rhs: AstNode
	
	@walk_func
	def walk(self, visitor):
		if self.lhs is not None: self.lhs.walk(visitor)
		if self.rhs is not None: self.rhs.walk(visitor)

@dataclass
class FuncType(AstNode):
	args: list
	ret: AstNode

	@walk_func
	def walk(self, visitor):
		for arg in self.args: visitor.visit(arg)
		
		visitor.visitor(self.ret)


@dataclass
class Declaration(AstNode):
	name: Token
	type: AstNode
	expr: AstNode | None

	@walk_func
	def walk(self, visitor):
		if self.type is not None: self.type.walk(visitor)
		if self.expr is not None: self.expr.walk(visitor)

@dataclass
class Module(AstNode):
	name: Token 
	statements: list
	
	@walk_func
	def walk(self, visitor):
		for stmt in self.statements: visitor.visit(self)


