class SqlBuilding:
	def __init__(self, operation=''):
		self._operation = operation
		self.fields = []

	def append_field(self, field):
		self.fields.append(field)

	def query(self):
		return self._operation + ' '

class Select(SqlBuilding):
	def __init__(self, table):
		super().__init__('select')
		self.table = table

		self.left_joins = []
		self.conditions = []
		self.sorted_fields = []

	def add_param(self, fields=[], left_joins=[], conditions=[], sorted_fields=[], logical=None):
		if logical is not None:
			self.logical = logical
		for c in conditions:
			self.conditions.append(c)
		for f in fields:
			self.fields.append(f)
		for l in left_joins:
			self.left_joins.append(l)
		for s in sorted_fields:
			self.sorted_fields.append(s)

	def get_target_field(self, field, i):
		return ' {0}.{1} as a{2} '.format(field['table'], field['column'], str(i))

	def get_left_join_sql(self, left_join):
		return ' left join {0} on {0}.{1} = {2}.{3} '.format(
				left_join['reference_table'], left_join['reference_column'],	
				self.table.name, left_join['column'])

	def get_order_sql(self):
		if not self.sorted_fields:
			return ''
		target = ','.join([' {0}.{1} '.format(self.fields[i]['table'], self.fields[i]['column'])
						   for i in self.sorted_fields])
		return ' order by ' + target

	def query(self):
		target = ','.join([self.get_target_field(field, i) for i, field in enumerate(self.fields)])
		table_from = ' from {0} '.format(self.table.name)
		left_join = ' '.join([self.get_left_join_sql(left_join) for left_join in self.left_joins])
		if self.conditions:
			if hasattr(self, 'logical'):
				where = 'where ' + self.logical.operation().join([x.get_str() for x in self.conditions])
			else:
				where = 'where ' + self.conditions[0].get_str()
		else:
			where = ''
		sort = self.get_order_sql()
		return super().query() + target+ table_from + left_join + where + sort 

	def first_skip(self):
		if self.pagination is None:
			return ''
		else:
			return ''

	def get_count(self, from_table=''):
		if not from_table:
			return "select count(*) from ({0}) ".format(self.query())
		else:
			return "select count(*) from ({0}) ".format(from_table)