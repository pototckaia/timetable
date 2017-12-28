import fields as f
import condition as c
import sql
from collections import OrderedDict
from math import ceil

import fdb
from flask import g

def get_db():
	if not hasattr(g, "fb_db"):
		g.fb_db = fdb.connect(
			dsn='db/TIMETABLE.fdb',
			user='sysdba',
			password='masterkey',
			charset=u'UTF8'
	)
	return g.fb_db

def commit():
	get_db().commit()

def execute(smth, val=(), fetchall=True):
	print()
	print(smth)
	print(val)
	cur = get_db().cursor()
	cur.execute(smth, val)
	if fetchall: return cur.fetchall()

class BaseTable:
	def __init__(self, table_name, table_caption, **columns):
		self.name = table_name
		self.caption = table_caption
		
		self._columns = OrderedDict()
		for key, value in columns.items():
			self._columns[key] = value

	def get_title(self, field):
		return self._columns.get(field).title

	def get_target(self, field):
		return self._columns.get(field).target

	def get_references(self):
		return tuple(var.reference for var in self.columns() if isinstance(var, f.ForeignKey))

	def columns(self, skipped_field=''):
		return sorted((value for key, value in self._columns.items() if key != skipped_field), key=lambda x: x.title)
	
	def target_columns(self, skipped_field=''):
		return tuple(value.target for value in self.columns(skipped_field))

	def fields_title(self, skipped_field=''):
		return tuple(value.title for value in self.columns(skipped_field))

	def real_columns_name(self, skipped_field=''):
		return tuple({'table': self.name, 'column': value.name} for value in self.columns(skipped_field))

	def get_index_id(self):
		return [value.name for value in self.columns()].index('id')

	@staticmethod
	def tables():
		return sorted(tuple(subclass() for subclass in BaseTable.__subclasses__()), key=lambda x: x.caption)

	def convert_to_columns(self, fields_number):
		columns = self.columns()
		return [columns[i] for i in fields_number]

	def get_count_page(self, conditions=None, page_size=5):
		sel = sql.Select(self)
		sel.add_options(left_joins=self.get_references(), conditions=conditions)
		values = conditions.values if conditions is not None else ()
		count_page = execute(sel.get_count(), values)[0][0]
		return ceil(count_page / page_size)

	def select(self, target_number=[], conditions=None, sorted_fields_number=[], pagination=False):
		sel = sql.Select(self)
		sel.add_options(left_joins=self.get_references(), conditions=conditions)

		sorted_columns =[col.target for col in self.convert_to_columns(sorted_fields_number)]
		target_columns = [col.target for col in self.convert_to_columns(target_number)]
		if not target_number:
			target_columns = self.target_columns()
		sel.add_options(sorted_fields=sorted_columns, fields=target_columns)
		sel.pagination = pagination

		values = conditions.values if conditions is not None else ()
		p = () if not pagination else pagination
		return execute(sel.query(), tuple(p) + tuple(values))

#######

	def get_row_by_id(self, id):
		index_id = self.get_index_id()
		cond = c.Condition(field=self.columns()[index_id].real_name, compare_operator=c.Equality())
		cc = c.Conditions()

		cc.append(cond=cond, val=id)
		current_values = self.select(conditions=cc)

		if not current_values:
			raise Exception("Строка c id " + str(id) + " в таблице " + self.caption + " уже не существует")
		
		current_values = list(current_values[0])
		return current_values

	def get_data_for_edit_card(self):
		data = []
		for val in self.columns():
			tip = {}
			if (isinstance(val, f.ForeignKey)):
				table = val._reference_table
				sel = sql.Select(table)
				sel.append_field(val.target)
				sel.append_field(table.get_target('id'))
				all_key = execute(sel.query())
				if not val.not_null:
					all_key = [(str(None), 'None'), ] + all_key

				tip['type'] = 'select'
				tip['values'] = all_key
			else:
				tip['type'] = val.type
			data.append(tip)
		return data


	def convert_values(self, values, fields_number=()):
		columns = self.convert_to_columns(fields_number) if fields_number else self.columns(skipped_field='id')
		for i, val in enumerate(columns):
			if (isinstance(val, f.ForeignKey)):
				values[i] = val._convert(values[i])
				if values[i] is not None:
					val._reference_table.get_row_by_id(values[i])
			else:
				values[i] = val.convert(values[i])
		return values

	def update_by_id(self, id, values, updated_fields_number=()):
		sel = sql.Update(self)

		updated_fields = [col.real_name for col in self.convert_to_columns(updated_fields_number)]
		if not updated_fields_number:
			updated_fields = self.real_columns_name(skipped_field='id')

		sel.extend_field(fields=updated_fields)
		index_id = self.get_index_id()
		cond = c.Condition(field=self.columns()[index_id].real_name, compare_operator=c.Equality())
		cc = c.Conditions()
		cc.append(cond=cond, val=id)
		sel.add_options(conditions=cc)

		execute(sel.query(), tuple(values + [id]), fetchall=False)
		commit()

	def insert_row(self, values):
		inr = sql.Insert(self)
		inr.extend_field(fields=self.real_columns_name(skipped_field='id'))
		execute(inr.query_values(), values, fetchall=False)
		commit()

	def delete_by_id(self, id):
		d = sql.Delete(self)
		index_id = self.get_index_id()
		cond = c.Condition(field=self.columns()[index_id].target, compare_operator=c.Equality())
		cc = c.Conditions()
		cc.append(cond=cond, val=id)
		d.add_options(conditions=cc)

		execute(d.query(), (id,), fetchall=False)
		commit()

class AudiencesTable(BaseTable):
	def __init__(self):
		super(AudiencesTable, self).__init__(
			'AUDIENCES',
			'Аудитории',
			id = f.Integer('id', 'Идентификатор аудитории', 'AUDIENCES'),
			name = f.String('name', 'Номер аудитории', 'AUDIENCES', not_null=True)
		)

class GroupsTable(BaseTable):
	def __init__(self):
		super(GroupsTable, self).__init__(
			'GROUPS',
			'Группы',
			id = f.Integer('id', 'Идентификатор группы', 'GROUPS'),
			name = f.String('name', 'Название группы', 'GROUPS')
		)

class LessonsTable(BaseTable):
	def __init__(self):
		super(LessonsTable, self).__init__(
			'LESSONS',
			'Пары',
			id = f.Integer('id', 'Идентификатор пары', 'LESSONS'),
			name = f.String('name', 'Название пары', 'LESSONS'),
			order_number = f.Integer('order_number', 'Номер пары', 'LESSONS')
		)

class LessonTypesTable(BaseTable):
	def __init__(self):
		super(LessonTypesTable, self).__init__(
			'LESSON_TYPES',
			'Типы занятия',
			id = f.Integer('id', 'Идентификатор вида предмета', 'LESSON_TYPES'),
			name = f.String('name', 'Тип предмета', 'LESSON_TYPES')
		)

class SubjectsTable(BaseTable):
	def __init__(self):
		super(SubjectsTable, self).__init__(
			'SUBJECTS',
			'Предметы',
			id = f.Integer('id', 'Идентификатор предмета', 'SUBJECTS'),
			name = f.String('name', 'Название предмета', 'SUBJECTS')
		)

class TeachersTable(BaseTable):
	def __init__(self):
		super(TeachersTable, self).__init__(
			'TEACHERS',
			'Преподаватели',
			id = f.Integer('id', 'Идентификатор преподавателя', 'TEACHERS'),
			name = f.String('name', 'ФИО', 'TEACHERS')
		)

class WeekdaysTable(BaseTable):
	def __init__(self):
		super(WeekdaysTable, self).__init__(
			'WEEKDAYS',
			'Дни недели',
			id  = f.Integer('id', 'Идентификатор недели', 'WEEKDAYS'),
			name = f.String('name', 'Название дня недели', 'WEEKDAYS' ,not_null=True),
			order_number = f.Integer('order_number', 'День недели', 'WEEKDAYS' ,not_null=True)
		)

class SchedItemsTable(BaseTable):
	def __init__(self):
		super(SchedItemsTable, self).__init__(
			'SCHED_ITEMS',
			'Расписание',
			id = f.Integer('id', 'Идентификатор расписание', 'SCHED_ITEMS'),
			lesson_id = f.ForeignKey(name='lesson_id', title='Идентификатор предмта', reference_table=LessonsTable(),
				reference_field='id', target_name='name', table_name='SCHED_ITEMS'),
			subject_id = f.ForeignKey(name='subject_id', title='Идентификатор предмета', reference_table=SubjectsTable(),
				reference_field='id', target_name='name', table_name='SCHED_ITEMS'),
			audience_id = f.ForeignKey(name='audience_id',title='Идентификатор аудитории',reference_table=AudiencesTable(),
				reference_field='id', target_name='name', table_name='SCHED_ITEMS'),
			group_id = f.ForeignKey(name='group_id', title='Идентификатор группы', reference_table=GroupsTable(),
				reference_field='id', target_name='name', table_name='SCHED_ITEMS'),
			teacher_id = f.ForeignKey(name='teacher_id', title='Идентификатор преподавателя', reference_table=TeachersTable(),
				reference_field='id', target_name='name', table_name='SCHED_ITEMS'),
			type_id = f.ForeignKey(name='type_id',title='Идентификатор типы предмета',reference_table=LessonTypesTable(),
				reference_field='id', target_name='name', table_name='SCHED_ITEMS'),
			weekday_id = f.ForeignKey(name='weekday_id', title='Идентификатор дня недели', reference_table=WeekdaysTable(),
				reference_field='id', target_name='name', table_name='SCHED_ITEMS')
		)

class SubjectGroupTable(BaseTable):
	def __init__(self):
		super(SubjectGroupTable, self).__init__(
			'SUBJECT_GROUP',
			'Предмет-Группа',
			id = f.Integer(name='id', title="Идентификатор отношения предмет-группа", table_name='SUBJECT_GROUP'),
			subject_id = f.ForeignKey(name='subject_id', title='Идентификатор предмета', reference_table=SubjectsTable(),
				reference_field='id', target_name='name', table_name='SUBJECT_GROUP', not_null=True),
			group_id = f.ForeignKey(name='group_id', title='Идентификатор группы', reference_table=GroupsTable(),
				reference_field='id', target_name='name', table_name='SUBJECT_GROUP', not_null=True)
		)

class SubjectTeacherTable(BaseTable):
	def __init__(self):
		super(SubjectTeacherTable, self).__init__(
			'SUBJECT_TEACHER',
			'Предмет-Учитель',
			id = f.Integer(name='id', title="Идентификатор отношения предмет-преподаватель", table_name='SUBJECT_TEACHER'),
			subject_id = f.ForeignKey(name='subject_id', title='Идентификатор предмета', reference_table=SubjectsTable(),
				reference_field='id', target_name='name' , table_name='SUBJECT_TEACHER', not_null=True),
			teacher_id = f.ForeignKey(name='teacher_id', title='Идентификатор учителя', reference_table=TeachersTable(),
				reference_field='id', target_name='name', table_name='SUBJECT_TEACHER', not_null=True),
		)

