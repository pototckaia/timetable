#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fields as f
import condition as c
import sql
from collections import OrderedDict

class BaseTable:
	def __init__(self, table_name, table_caption,**columns):
		self._name = table_name
		self._caption = table_caption
		
		self._columns = OrderedDict()
		for key, value in columns.items():
			self._columns[key] = value

	def get_title(self, field):
		return self.get_column(field).title

	def get_column(self, field):
		return self._columns[field]

	def get_target(self, field):
		column = self.get_column(field)
		if (isinstance(column, f.ForeignKey)):
			return self.get_column(field).target
		else:
			return {'table': self.name, 'column': field}

	def get_references(self):
		reference = []
		for key, var in self._columns.items():
			if (isinstance(var, f.ForeignKey)):
				reference.append(var.reference)
		return reference

	@property
	def name(self):
		return self._name

	@property
	def caption(self):
		return self._caption

	def columns(self, skipped_field=''):
		return sorted(tuple(value for key, value in self._columns.items() if value.name != skipped_field), key=lambda x: x.title)
	
	def targe_columns(self, skipped_field=''):
		return tuple(self.get_target(value.name) for value in self.columns(skipped_field))

	def fields_title(self, skipped_field=''):
		return tuple(value.title for  value in self.columns(skipped_field))

	def real_columns_name(self, skipped_field=''):
		return tuple({'table': self.name, 'column': value.name} for value in self.columns(skipped_field))

	def get_column_number(self, name):
		return self.columns().index(self.get_column(name))

	@staticmethod
	def tables():
		return sorted(tuple(subclass() for subclass in 
			BaseTable.__subclasses__()), key=lambda x: x.caption)

	def get_count(self, fields_number=[], comparison_operators=[], logical_operator=None):
		sel = sql.Select(self)
		sel.add_options(fields=self.targe_columns(), left_joins=self.get_references())

		for i in range(0, len(fields_number)):
			sel.append_condition(c.Condition(self.targe_columns()[fields_number[i]], comparison_operators[i]))
		
		sel.add_options(logical=logical_operator)
		return sel.get_count()

	def convert_values(self, fields_number, values):		
		for i in range(len(fields_number)):	
			column = self.columns()[fields_number[i]]
			values[i] = column.convert(values[i])
		return tuple(values)

	def get_index_id(self):
		return list([value.name for value in self.columns()]).index('id')

	def select(self, target_number=[], fields_number=[], comparison_operators=[], logical_operator=None, sorted_fields_number=[], pagination=False):
		sel = sql.Select(self)
		sel.add_options(left_joins=self.get_references())

		if not target_number:
			sel.add_options(fields=self.targe_columns())
		else:
			for i in target_number:	
				sel.append_field(self.get_target(self.columns()[i].name))

		for i in range(0, len(fields_number)):
			sel.append_condition(c.Condition(self.targe_columns()[fields_number[i]], comparison_operators[i]))

		for i in sorted_fields_number:
			sel.append_sort(self.get_target(self.columns()[i].name))
		
		sel.add_options(logical=logical_operator)
		sel.pagination =  pagination
		return sel.query()

	#######

	def get_row(self, id, execute):
		index_id = list([value.name for value in self.columns()]).index('id')
		field = [index_id] 
		compare = []
		compare.append(c.Equality())

		current_values = execute(self.select(fields_number=field, comparison_operators=compare), (id, ))

		if not current_values:
			raise Exception("Строка c id " + str(id) + " в таблицы " + self.caption + " уже не существует") 
		
		current_values = list(current_values[0])
		current_id = current_values[index_id]
		del current_values[index_id]

		return current_values

	def get_output_values(self, execute):
		output_values = []
		for val in self.columns(skipped_field='id'):
			if (isinstance(val, f.ForeignKey)):
				table = val._reference_table
				field = val._target_name
				sel  = sql.Select(table)
				sel.append_field(table.get_target(field))
				sel.append_field(table.get_target('id'))
				all_key = execute(sel.query())
								
				tip = {}
				tip["type"] = 'select'
				tip["values"] = all_key

			else:
				tip = {}
				tip["type"] = val.type

			output_values.append(tip)
		return output_values

	def convert_all_values(self, values):
		for i, val in enumerate(self.columns(skipped_field='id')):
			if (isinstance(val, f.ForeignKey)):
				values[i] = int(values[i])
			else:
				values[i] = val.convert(values[i])
		return values

	def check_for_existence(self, values, execute):
		for i, val in enumerate(self.columns(skipped_field='id')):
			if (isinstance(val, f.ForeignKey)):
				buf = val._reference_table.get_row(values[i], execute)
		return 	

	def update_by_id(self):
		sel = sql.Update(self)
		sel.extend_field(fields=self.real_columns_name(skipped_field='id'))
		sel.append_condition(c.Condition({'table': self.name, 'column': 'id'}, c.Equality()))
		return sel.query()

	def insert(self):
		inr = sql.Insert(self)
		inr.extend_field(fields=self.real_columns_name(skipped_field='id'))
		return inr.query_values()

	def delete_by_id(self):
		d = sql.Delete(self)
		d.append_condition(c.Condition({'table': self.name, 'column': 'id'}, c.Equality()))
		return d.query()

#####

class AudiencesTable(BaseTable):
	def __init__(self):
		super(AudiencesTable, self).__init__(
			'AUDIENCES',
			'Аудитории',
			id = f.Integer('id', 'Идентификатор аудитории'),
			name = f.String('name', 'Номер аудитории', not_null=True)
		)

class GroupsTable(BaseTable):
	def __init__(self):
		super(GroupsTable, self).__init__(
			'GROUPS',
			'Группы',
			id = f.Integer('id', 'Идентификатор группы'),
			name = f.String('name', 'Название группы')
		)

class LessonsTable(BaseTable):
	def __init__(self):
		super(LessonsTable, self).__init__(
			'LESSONS',
			'Пары',
			id = f.Integer('id', 'Идентификатор пары'),
			name = f.String('name', 'Название пары'),
			order_number = f.Integer('order_number', 'Номер пары')
		)

class LessonTypesTable(BaseTable):
	def __init__(self):
		super(LessonTypesTable, self).__init__(
			'LESSON_TYPES',
			'Типы занятия',
			id = f.Integer('id', 'Идентификатор вида предмета'),
			name = f.String('name', 'Тип предмета')
		)

class SubjectsTable(BaseTable):
	def __init__(self):
		super(SubjectsTable, self).__init__(
			'SUBJECTS', 
			'Предметы',
			id = f.Integer('id', 'Идентификатор предмета'), 
			name = f.String('name', 'Название предмета')
		)

class TeachersTable(BaseTable):
	def __init__(self):
		super(TeachersTable, self).__init__(
			'TEACHERS',
			'Преподаватели',
			id = f.Integer('id', 'Идентификатор преподавателя'),
			name = f.String('name', 'ФИО')
		)

class WeekdaysTable(BaseTable):
	def __init__(self):
		super(WeekdaysTable, self).__init__(
			'WEEKDAYS',
			'Дни недели',
			id  = f.Integer('id', 'Идентификатор недели'), 
			name = f.String('name', 'Название дня недели', not_null=True),
			order_number = f.Integer('order_number', 'День недели', not_null=True)
		) 

class SchedItemsTable(BaseTable):
	def __init__(self):
		super(SchedItemsTable, self).__init__(
			'SCHED_ITEMS',
			'Расписание',
			id = f.Integer('id', 'Идентификатор расписание'),
			lesson_id = f.ForeignKey(name='lesson_id', title='Идентификатор предмта', reference_table=LessonsTable(),
									 reference_field='id', target_name='name'),
			subject_id = f.ForeignKey(name='subject_id', title='Идентификатор предмета', reference_table=SubjectsTable(),
									  reference_field='id', target_name='name'),
			audience_id = f.ForeignKey(name='audience_id',title='Идентификатор аудитории',reference_table=AudiencesTable(),
									   reference_field='id', target_name='name'),
			group_id = f.ForeignKey(name='group_id', title='Идентификатор группы', reference_table=GroupsTable(),
									reference_field='id', target_name='name'),
			teacher_id = f.ForeignKey(name='teacher_id', title='Идентификатор преподавателя', reference_table=TeachersTable(),
									  reference_field='id', target_name='name'),
			type_id = f.ForeignKey(name='type_id',title='Идентификатор типы предмета',reference_table=LessonTypesTable(),
								   reference_field='id', target_name='name'),
			weekday_id = f.ForeignKey(name='weekday_id', title='Идентификатор дня недели', reference_table=WeekdaysTable(),
									  reference_field='id', target_name='name')
		)

class SubjectGroupTable(BaseTable):
	def __init__(self):
		super(SubjectGroupTable, self).__init__(
			'SUBJECT_GROUP',
			'Предмет-Группа',
			id = f.Integer(name='id', title="Идентификатор отношения предмет-группа"),
			subject_id = f.ForeignKey(name='subject_id', title='Идентификатор предмета', reference_table=SubjectsTable(),
									  reference_field='id', target_name='name'),
			group_id = f.ForeignKey(name='group_id', title='Идентификатор группы', reference_table=GroupsTable(),
									reference_field='id', target_name='name')
		)

class SubjectTeacherTable(BaseTable):
	def __init__(self):
		super(SubjectTeacherTable, self).__init__(
			'SUBJECT_TEACHER',
			'Предмет-Учитель',
			id = f.Integer(name='id', title="Идентификатор отношения предмет-преподаватель"),
			subject_id = f.ForeignKey(name='subject_id', title='Идентификатор предмета', reference_table=SubjectsTable(),
									  reference_field='id', target_name='name'),
			teacher_id = f.ForeignKey(name='teacher_id', title='Идентификатор учителя', reference_table=TeachersTable(),
									  reference_field='id', target_name='name'),
		)

