import fields as f
import condition as c
import sql
from collections import OrderedDict
from math import ceil

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

	@property
	def columns(self):
		return tuple(value for key, value in self._columns.items())
	
	@property
	def targe_columns(self):
		return tuple(self.get_target(key) for key, value in self._columns.items())

	@property
	def fields_title(self):
		return tuple(value.title for key, value in self._columns.items())

	@staticmethod
	def tables():
		return sorted(tuple(subclass() for subclass in 
			BaseTable.__subclasses__()), key=lambda x: x.caption)

	def get_count_pages(self, sql_from, value, page_size, execute):
		count = execute(sql.Select(self).get_count(sql_from), value)[0][0]
		print(page_size)
		print(ceil(count/page_size))

	def select_all(self, **kwargs):
		sel = sql.Select(self)
		sel.add_param(self.targe_columns, self.get_references())
		if not kwargs:
			return sel.query()
		else:
			index_fields = kwargs['index_fields']
			index_comps = kwargs['index_comps']
			values = kwargs['values']
			index_sorted = kwargs['index_sorted']
			logical_operator = kwargs['logical_operator']
			conditions = []
			for i in range(0, len(index_fields)):
				conditions.append(c.Condition(self.targe_columns[index_fields[i]], index_comps[i]))
				column = self.columns[index_fields[i]]
				if not column.check_type(values[i]):
					raise ValueError('Несоотвествие типов', values[i], column._convert, column)
				values[i] = column.convert(values[i])
			sel.add_param(conditions=conditions, sorted_fields=index_sorted, logical=logical_operator)
			return sel.query(), tuple(values)


class AudiencesTable(BaseTable):

	def __init__(self):
		super(AudiencesTable, self).__init__(
			'AUDIENCES',
			'Аудитории',
			id = f.Integer('id', 'Идентификатор'),
			name = f.String('name', 'Номер аудитории')
		)

class GroupsTable(BaseTable):
	
	def __init__(self):
		super(GroupsTable, self).__init__(
			'GROUPS',
			'Группы',
			id = f.Integer('id', 'Идентификатор'),
			name = f.String('name', 'Название группы')
		)

class LessonsTable(BaseTable):

	def __init__(self):
		super(LessonsTable, self).__init__(
			'LESSONS',
			'Пары',
			id = f.Integer('id', 'Идентификатор'),
			name = f.String('name', 'Название пары'),
			order_number = f.Integer('order_number', 'Номер пары')
		)

class LessonTypesTable(BaseTable):
	
	def __init__(self):
		super(LessonTypesTable, self).__init__(
			'LESSON_TYPES',
			'Типы занятия',
			id = f.Integer('id', 'Идентификатор'),
			name = f.String('name', 'Тип предмета')
		)

class SubjectsTable(BaseTable):

	def __init__(self):
		super(SubjectsTable, self).__init__(
			'SUBJECTS', 
			'Предметы',
			id = f.Integer('id', 'Идентификатор'), 
			name = f.String('name', 'Название предмета')
		)

class TeachersTable(BaseTable):
	
	def __init__(self):
		super(TeachersTable, self).__init__(
			'TEACHERS',
			'Преподаватели',
			id = f.Integer('id', 'Идентификатор'),
			name = f.String('name', 'ФИО')
		)

class WeekdaysTable(BaseTable):

	def __init__(self):
		super(WeekdaysTable, self).__init__(
			'WEEKDAYS',
			'Дни недели',
			id  = f.Integer('id', 'Идентификатор'), 
			name = f.String('name', 'Название дня нелели'),
			order_number = f.Integer('order_number', 'День недели')
		) 

class SchedItemsTable(BaseTable):

	def __init__(self):
		super(SchedItemsTable, self).__init__(
			'SCHED_ITEMS',
			'Расписание',
			id = f.Integer('id', 'Идентификатор'),
			lesson_id = f.ForeignKey(name='lesson_id', title='Идентификатор предмта', reference_table=LessonsTable(),
									 reference_field='id', target_name='name'),
			subject_id = f.ForeignKey(name='subject_id', title='Идентификатор предмета', reference_table=SubjectsTable(),
									  reference_field='id', target_name='name'),
			audience_id = f.ForeignKey(name='audience_id',title='Идентификатор аудитории',reference_table=AudiencesTable(),
									   reference_field='id', target_name='name'),
			group_id = f.ForeignKey(name='group_id', title='Идентификатор группы', reference_table=GroupsTable(),
									reference_field='id', target_name='name'),
			teacher_id = f.ForeignKey(name='teacher_id', title='Идентификатор учителя', reference_table=TeachersTable(),
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
			id = f.Integer(name='id', title="Идентификатор"),
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
			id = f.Integer(name='id', title="Идентификатор"),
			subject_id = f.ForeignKey(name='subject_id', title='Идентификатор предмета', reference_table=SubjectsTable(),
									  reference_field='id', target_name='name'),
			teacher_id = f.ForeignKey(name='teacher_id', title='Идентификатор учителя', reference_table=TeachersTable(),
									  reference_field='id', target_name='name'),
		)



