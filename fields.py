
class Column:
	def __init__(self, name, title, convert=None):
		self._name = name
		self._title = title
		self._convert = convert

	@property
	def title(self):
		return self._title

	@property
	def name(self):
		return self._name

	def convert(self, value):
		return self._convert(value)

	def check_type(self, value):
		try:
			value = self.convert(value)
		except ValueError:
			value = None
		return isinstance(value, self._convert)
		

class Integer(Column):
	def __init__(self, name, title):
		super().__init__(name, title, int)

class String(Column):
	def __init__(self, name, title):
		super().__init__(name, title, str)

class ForeignKey(Column):
	def __init__(self, name, title, reference_table, reference_field, target_name):
		super().__init__(name, title)
		self._reference_table = reference_table
		self._reference_field = reference_field
		self._target_name = target_name

	@property
	def title(self):
		return self._reference_table.get_title(self._target_name)

	@property
	def reference(self):
		return {'reference_table': self._reference_table.name, 'reference_column': self._reference_field, 
			'column': self._name}

	@property
	def target(self):
		return {'table': self._reference_table.name, 'column': self._target_name}

	def check_type(self, value):
		return self._reference_table.get_column(self._target_name).check_type(value) 

	def convert(self, value):
		return self._reference_table.get_column(self._target_name).convert(value)
