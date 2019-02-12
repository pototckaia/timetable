class LogicalOperator:
	def __init__(self, operation, caption):
		self._operation = operation
		self._caption = caption

	@staticmethod
	def logical_operations():
		return sorted((subclass() for subclass in LogicalOperator.__subclasses__()), key=lambda x: x.caption)

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
		return sorted(tuple(subclass() for subclass in Compare.__subclasses__()), key=lambda x: x.caption)

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
		super().__init__('like', 'Подстрока')

	def operator(self):
		return " " + self._operator + "'%' || ? ||  '%'"

class Condition:
	def __init__(self, field, compare_operator):
		self.field = field
		self.compare_operator = compare_operator

	def get_str(self):
		return ' {0}.{1} '.format(self.field['table'], self.field['column']) + self.compare_operator.operator()

class Conditions:
	def __init__(self, columns=[], comparison_number=[], values=[], logical_number=None):
		list_logical_operators = LogicalOperator.logical_operations()
		self.logical_operator = list_logical_operators[logical_number] if logical_number is not None else None

		list_comparison_operators = Compare.comparison_operators()
		comparison_operators = [list_comparison_operators[i] for i in comparison_number]

		self.conditions = []
		self.values = []

		for i in range(0, len(columns)):
			self.values.append(columns[i].convert(values[i])) ####
			self.conditions.append(Condition(columns[i].target, comparison_operators[i]))


	def get_query(self):
		where = ''
		if self.conditions:
			if self.logical_operator is not None:
				where = 'where ' + self.logical_operator.operation().join([x.get_str() for x in self.conditions])
			else:
				where = 'where ' + self.conditions[0].get_str()
		return where

	def append(self, cond, val):
		self.conditions.append(cond)
		self.values.append(val)