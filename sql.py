#!/usr/bin/env python
# -*- coding: utf-8 -*-

class SqlBuilding:

	def __init__(self, operation, table):
		self._operation = operation
		self.fields = []
		self.table = table

	def extend_field(self, fields):
		self.fields.extend(fields)

	def append_field(self, field):
		self.fields.append(field)

	def query(self):
		return self._operation + ' '

class BaseQuery(SqlBuilding):
	def __init__(self, operation, table):
		super().__init__(operation, table)
		self.conditions = []
		self.sorted_fields = []

	def append_condition(self, cond):
		self.conditions.append(cond)
	
	def append_sort(self, sort):
		self.sorted_fields.append(sort)

	def clear_param(self):
		self.fields = []
		self.conditions = []
		self.sorted_fields = []
		self.logical = None

	def get_table(self):
		return self.table.name


	def add_options(self, fields=[], conditions=[], sorted_fields=[], logical=None):
		if logical is not None:
			self.logical = logical
		for c in conditions:
			self.conditions.append(c)
		for f in fields:
			self.fields.append(f)
		for s in sorted_fields:
			self.sorted_fields.append(s)
		
	def get_order_sql(self):
		if not self.sorted_fields:
			return ''
		target = ','.join([' {0}.{1} '.format(field['table'], field['column'])
						   for field in self.sorted_fields])
		return ' order by ' + target

	def get_where_conditions(self):
		if self.conditions:
			if hasattr(self, 'logical') and self.logical is not None:
				where = 'where ' + self.logical.operation().join([x.get_str() for x in self.conditions])
			else:
				where = 'where ' + self.conditions[0].get_str()
		else:
			where = ''
		return where

####

class Select(BaseQuery):
	def __init__(self, table):
		super().__init__('select', table)
		self.left_joins = []
		self.pagination = False

	def get_left_join_sql(self):
		return ' '.join([
				' left join {0} on {0}.{1} = {2}.{3} '.format(
				left_join['reference_table'], left_join['reference_column'],	
				self.table.name, left_join['column'
			]) for left_join in self.left_joins])

	def get_pagination(self):
		if self.pagination:
			return ' first ? skip ? '
		else:
			return ' '

	def clear_param(self):
		super().clear_param()
		self.left_join = []

	def append_left_join(self, left_join):
		self.left_joins.append(left_join)

	def add_options(self, fields=[], conditions=[], sorted_fields=[], logical=None, left_joins=[], pagination=False):
		super().add_options(fields=fields, conditions=conditions, sorted_fields=sorted_fields, logical=logical)
		for l in left_joins:
			self.left_joins.append(l)
		self.pagination = pagination

	def get_column_list(self):
		return ','.join([
			' {0}.{1} as a{2} '.format(
				field['table'], field['column'], str(i)) 
				for i, field in enumerate(self.fields)])
		
	def get_table(self):
		return ' from {0} '.format(self.table.name)

	def query(self):
		target = self.get_column_list()
		pagination = self.get_pagination()
		table_from = self.get_table()
		left_join = self.get_left_join_sql()
		where = self.get_where_conditions()
		sort = self.get_order_sql()
		return super().query() + pagination + target + table_from + left_join + where + sort 

	def get_count(self):
		target = ' count(*) '
		table_from = self.get_table()
		left_join = self.get_left_join_sql()
		where = self.get_where_conditions()
		sort = self.get_order_sql()
		return super().query() + target + table_from + left_join + where + sort

####

class Update(BaseQuery):
	def __init__(self, table):
		super().__init__('update', table)

	def get_column_list(self):
		col = ','.join([field['column'] + ' = ? ' for field in self.fields])
		return ' set ' + col

	def query(self):
		target = self.get_column_list()
		table_from = self.get_table()
		where = self.get_where_conditions()
		sort = self.get_order_sql()
		return super().query() + table_from + target  + where + sort 

###

class Delete(BaseQuery):
	def __init__(self, table):
		super().__init__('delete', table)

	def get_table(self):
		return ' from {0} '.format(self.table.name)

	def query(self):
		table_from = self.get_table()
		where = self.get_where_conditions()
		sort = self.get_order_sql()
		return super().query() + table_from  + where + sort 


###
class Insert(SqlBuilding):
	def __init__(self, table):
		super().__init__('insert', table)

	def get_column_list(self):
		return ' (' + ' , '.join([field['column'] for field in self.fields]) + ') '

	def get_table(self):
		return ' into ' + self.table.name

	def query_values(self):
		sql =  super().query() + self.get_table() + self.get_column_list() 
		sql += ' values (' + ','.join(['? ' for f in self.fields]) + ') '
		return sql

	def query_select(self, select_statment):
		sql = super().query() + self.get_table() + self.get_column_list() + select_statment	
		return sql
