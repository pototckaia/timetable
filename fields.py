class Column:
	def __init__(self, name, title, table_name, convert, type='', not_null=False):
		self._name = name
		self._title = title
		self._table_name = table_name
		self._convert = convert
		self.type = type
		self.not_null = not_null

	@property
	def title(self):
		return self._title

	@property
	def name(self):
		return self._name

	def convert(self, value): 
		return self._convert(value)

	@property
	def target(self):
		return {'table': self._table_name, 'column': self.name}

	@property
	def real_name(self):
		return {'table': self._table_name, 'column': self.name}

class Integer(Column):
	def __init__(self, name, title, table_name, not_null=False):
		super().__init__(name, title, table_name, decorator_convert(int, not_null), 'number', not_null)

class String(Column):
	def __init__(self, name, title, table_name, not_null=False):
		super().__init__(name, title, table_name, decorator_convert(str, not_null), 'text', not_null)

class ForeignKey(Column):
	def __init__(self, name, title, table_name, reference_table, reference_field, target_name, not_null=False):
		super().__init__(name, title, table_name, decorator_convert(int, not_null), not_null=not_null)
		self._reference_table = reference_table
		self._reference_field = reference_field
		self._target_name = target_name

	@property
	def title(self):
		return self._reference_table.get_title(self._target_name)

	@property
	def reference(self):
		return {'reference_table': self._reference_table.name, 'table': self._table_name,
				'reference_column': self._reference_field, 'column': self._name}

	@property
	def target(self):
		return {'table': self._reference_table.name, 'column': self._target_name}

	def convert(self, value): ###
		return self._reference_table.get_column(self._target_name).convert(value)
		

def decorator_convert(f, not_null):
	def wrapper(value):
		if value is None or value == '' or (str(value).lower() == str(None).lower()):
			if not_null:
				raise ValueError("Тип not null")
			return None
		return f(value)
	return wrapper 