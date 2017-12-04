class LogicalOperator:
	def __init__(self, operation, caption):
		self._operation = operation
		self._caption = caption

	@staticmethod
	def logical_operations():
		return sorted(tuple(subclass() for subclass in LogicalOperator.__subclasses__()), 
			key=lambda x: x.caption)

	@property
	def caption(self):
		return self._caption

	def operation(self):
		return ' ' + self._operation + ' '

class LogicalAnd(LogicalOperator):
	def __init__(self):
		super().__init__('and', 'И')

class LogicalOr(LogicalOperator):
	def __init__(self):
		super().__init__('or', 'Или')

class Compare:
	def __init__(self, operator, caption):
		self._operator = operator
		self._caption = caption

	@staticmethod
	def comparison_operators():
		return sorted(tuple(subclass() for subclass in Compare.__subclasses__()), 
			key=lambda x: x.caption)

	@property
	def caption(self):
		return self._caption

	def operator(self):
		return ' ' + self._operator + ' ? '

class Equality(Compare):
	def __init__(self):
		super().__init__('=', 'Равно')

class More(Compare):
	def __init__(self):
		super().__init__('>', 'Больше')

class Less(Compare):
	def __init__(self):
		super().__init__('<', 'Меньше')

class Like(Compare):
	def __init__(self):
		super().__init__('like', 'Похоже на')

	def operator(self):
		return " " + self._operator + "'%' || ? ||  '%'"

class Condition:
	def __init__(self, field, compare_operator):
		self.field = field
		self.compare_operator = compare_operator

	def get_str(self):
		return ' {0}.{1} '.format(self.field['table'], self.field['column']) + self.compare_operator.operator()
