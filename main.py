#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, request, render_template, g, jsonify
import condition
from tables import BaseTable
import fdb
from math import ceil
from collections import OrderedDict


app = Flask(__name__)


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

def execute_edit(smth, val=()):
	print()
	print(smth)
	print(val)
	cur = get_db().cursor()
	cur.execute(smth, val)

def execute(smth, val=()):
	print()
	print(smth)
	print(val)
	cur = get_db().cursor()
	cur.execute(smth, val)
	return cur.fetchall()

@app.teardown_appcontext
def close_db(error):
	if hasattr(g, "man"):
		g.fb_db.close()


@app.route("/", methods=['GET'])
def get_meta_data():
	data = {}
	list_tables = BaseTable.tables()
	list_logical_operators = condition.LogicalOperator.logical_operations()
	list_comparison_operators = condition.Compare.comparison_operators()

	data['tables'] = [x.caption for x in list_tables]
	data['comparison_operators'] = [x.caption for x in list_comparison_operators]
	data['logical_operations'] = [x.caption for x in list_logical_operators]
	data['page_sizes'] = [5, 10, 15, 25]
	data['page_size'] = 5
	data['count_page'] = 0
	data['page_number'] = 0
	data['table_number'] = -1

	return render_template("table.html", **data)

@app.route("/<int:table>", methods=['GET'])
def get_table(table):
	data = {}

	list_tables = BaseTable.tables()
	list_logical_operators = condition.LogicalOperator.logical_operations()
	list_comparison_operators = condition.Compare.comparison_operators()

	data['tables'] = [x.caption for x in list_tables]
	data['comparison_operators'] = [x.caption for x in list_comparison_operators]
	data['logical_operations'] = [x.caption for x in list_logical_operators]
	data['page_sizes'] = [5, 10, 15, 25]
	data['table_number'] = -1

	if 0 <= table < len(list_tables):
		current_table = list_tables[table]

		data['title'] = current_table.fields_title()
		data['table_number'] = table
		data['index_id'] = current_table.get_index_id()

		is_update_table = request.args.get('is_update_table', type=int)
		if is_update_table is None:
			page_number = 0
			page_size = 5
			count_page = execute(current_table.get_count())[0][0]
			count_page = ceil(count_page / page_size)

			data['page_size'] = page_size
			data['count_page'] = count_page
			data['page_number'] = page_number

			data['entries'] = execute(current_table.select(pagination=True), (page_size, page_size * page_number))
			return render_template("table.html", **data)

		fields_number = request.args.getlist("fields_number[]", type=int)
		compare_number = request.args.getlist("comparison_operators[]", type=int)
		values = request.args.getlist("values[]")
		logical_number = request.args.get("logical_operation", type=int)
		sorted_fields_number = request.args.getlist("sorted_fields_number[]", type=int)

		page_size = request.args.get("page_size", type=int)
		page_number = request.args.get("page_number", type=int)
		count_page = request.args.get("count_page", type=int)

		logical_operator = list_logical_operators[logical_number] if logical_number is not None else None
		comparison_operators = [list_comparison_operators[i] for i in compare_number] if compare_number else []

		data['page_size'] = page_size
		data['count_page'] = count_page
		data['page_number'] = page_number

		try:
			values = current_table.convert_values(fields_number=fields_number, values=values)
			count_page = execute(current_table.get_count(fields_number=fields_number, comparison_operators=comparison_operators,
				logical_operator=logical_operator), values)[0][0]
			sql = current_table.select(fields_number=fields_number, comparison_operators=comparison_operators,
				logical_operator=logical_operator, sorted_fields_number=sorted_fields_number, pagination=True)

			data['entries'] = execute(sql, (page_size, page_size * page_number) + values)
			data['count_page'] = ceil(count_page / page_size)

			data['error'] = 0
		except ValueError:
			data['error'] = 1

		return jsonify(data)

###

@app.route("/update/<int:table>", methods=['GET', 'POST'])
@app.route("/update/<int:table>/<int:id_row>", methods=['GET', 'POST'])
def window_editor(table=None, id_row=None):
	list_tables = BaseTable.tables()
	if table < 0 or table >= len(list_tables):
		return

	current_table = list_tables[table]
	data = {}
	data['legend'] = 'Обновление записи с идентификатор ' + str(id_row)
	data['table'] = table
	data['id_row'] = id_row
	data['title_columns'] = current_table.fields_title(skipped_field='id')

	current_row = current_table.get_row(id_row, execute)
	out_val = current_table.get_output_values(execute)

	data['output_values'] = out_val
	data['cur_id'] = id_row
	data['current_row'] = current_row


	if request.method == 'POST':
		values = [request.form.get(str(i), None) for i in range(0, len(out_val))]
		#row = request.form.getlist('current_row[]')
		#print('row', row)

		try:
			values = current_table.convert_all_values(values)
			current_table.check_for_existence(values, execute)

			execute_edit(current_table.update_by_id(), tuple(values + [id_row]))
			commit()

			data['current_row'] = current_table.get_row(id_row, execute)
			data['error'] = 0
		except ValueError:
			data['current_row'] = current_table.get_row(id_row, execute)
			data['error'] = 1

	return render_template("update.html", **data)


@app.route("/insert/<int:table>", methods=['GET', 'POST'])
def window_insert(table):
	list_tables = BaseTable.tables()
	if table < 0 or table >= len(list_tables):
		return

	current_table = list_tables[table]

	data = {}
	data['legend'] = 'Вставить новую запись в таблицу ' + current_table.caption
	data['title_columns'] = current_table.fields_title(skipped_field='id')

	out_val = current_table.get_output_values(execute)
	data['output_values'] = out_val


	if request.method == 'POST':
		values = [request.form.get(str(i), None) for i in range(0, len(out_val))]
		try:
			values = current_table.convert_all_values(values)
			current_table.check_for_existence(values, execute)

			execute_edit(current_table.insert(), tuple(values))
			commit()
			data['window_close'] = True
		except ValueError:
			data['error'] = 1

	return render_template("insert.html", **data)

@app.route("/delete/<int:table>/<int:id_row>", methods=['POST'])
def delete_row(table, id_row):
	list_table = BaseTable.tables()
	if table < 0 or table >= len(list_table):
		return

	current_table = list_table[table]
	test = current_table.get_row(id_row, execute)
	execute_edit(current_table.delete_by_id(), (id_row, ))
	commit()
	data = {}
	return jsonify(data)


@app.route("/analytics/")
def analytics():
	data = {}
	list_tables = BaseTable.tables()
	list_logical_operators = condition.LogicalOperator.logical_operations()
	list_comparison_operators = condition.Compare.comparison_operators()
	current_table = BaseTable.tables()[8]
	data['tables'] = [x.caption for x in list_tables]
	data['title'] = current_table.fields_title()
	data['comparison_operators'] = [x.caption for x in list_comparison_operators]
	data['logical_operations'] = [x.caption for x in list_logical_operators]
	return render_template("analytics.html", **data)
 
@app.route("/analytics/<int:x>/<int:y>", methods=['GET'])
def build_table(x, y):

	list_logical_operators = condition.LogicalOperator.logical_operations()
	list_comparison_operators = condition.Compare.comparison_operators()

	fields_number = request.args.getlist("fields_number[]", type=int)
	compare_number = request.args.getlist("comparison_operators[]", type=int)
	values = request.args.getlist("values[]")
	logical_number = request.args.get("logical_operation", type=int)
	target_table = request.args.getlist("target_table[]", type=int)
	sorted_fields_number = request.args.getlist("sorted_fields_number[]", type=int)
	current_table = BaseTable.tables()[8]
	
	logical_operator = list_logical_operators[logical_number] if logical_number is not None else None
	comparison_operators = [list_comparison_operators[i] for i in compare_number] if compare_number else []
	try:
		values = current_table.convert_values(fields_number=fields_number, values=values)
		sql = current_table.select(target_number= [x]+[y]+target_table, fields_number=fields_number,
								   comparison_operators=comparison_operators, logical_operator=logical_operator,
								   sorted_fields_number=sorted_fields_number)

		entries = execute(sql, values)
	except ValueError:
		data = {}
		data['error'] = 1
		return jsonify(data)

	tables = dict()
	x_fields = OrderedDict()
	y_fields = OrderedDict()

	print(entries)

	for entry in entries:
		e_x = str(entry[0])
		e_y = str(entry[1])
		if not e_x in tables:
			tables[e_x] = dict()
			tables[e_x][e_y] = list()
		if not e_y in tables[e_x]:
			tables[e_x][e_y] = list()
		tables[e_x][e_y].append(entry[2::])
		x_fields[e_x] = 1
		y_fields[e_y] = 1
	
	data = {}
	data['error'] = 0
	data['x_fields'] = list(x_fields.keys())
	data['y_fields'] = list(y_fields.keys())
	data['tables'] = tables
	
	print(data['x_fields'], data['y_fields'] )
	print(data['tables'])
	print('KeK')

	return jsonify(data)

	


if __name__ == "__main__":
	app.run(debug=True)
