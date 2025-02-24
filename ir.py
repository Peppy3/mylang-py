from parser_file import ParserFile
import ast

class Module(ast.AstVisitor):
	def __init__(self, name):
		self.name = name
		self.values = dict()
	
	def get_value(self, name):
		return self.value[name]

	def set_value(self, name):
		if self.values.get(name) is not None:
			raise ValueError(name)

	def visit(self, node):
		raise NotImplemented

class Generator(ast.AstVisitor):
	def __init__(self, src):
		self.src = src
		self.modules = dict()

	def visit(self, node):
		raise NotImplemented


