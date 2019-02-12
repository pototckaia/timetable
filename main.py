from flask import Flask, request, render_template, g, jsonify
import condition as cond
from tables import BaseTable, TypeConflict

from collections import OrderedDict


app = Flask(__name__)

@app.teardown_appcontext
def close_db(error):
	if hasattr(g, 'fb_db'):
		g.fb_db.close()

def get_metadate():
	data = {}
	data['tables'] = [x.caption for x in BaseTable.tables()]
	data['comparison_operators'] = [x.caption for x in cond.Compare.comparison_operators()]
	data['logical_operations'] = [x.caption for x in cond.LogicalOperator.logical_operations()]
	data['page_sizes'] = [5, 10, 15, 25]
	data['table_number'] = -1
	return data

def get_current_table(index):
	return BaseTable.tables()[index]

@app.route('/', methods=['GET'])
def home():
	data = get_metadate()
	return render_template("base.html", **data)

@app.route("/select", methods=['GET'])
def select_table():
	data = get_metadate()
	data['url'] = 'get_table'
	return render_template("navigation.html", **data)

@app.route("/select/<int:table>", methods=['GET'])
def get_table(table):
	data = get_metadate()
	if table < 0 or table >= len(data['tables']): return

	current_table = get_current_table(table)
	data['url'] = 'get_table'
	data['title_columns'] = current_table.fields_title()
	data['table_number'] = table
	data['index_id'] = current_table.get_index_id()
	is_update_table = request.args.get('is_update_table', type=int)

	if is_update_table is None:
		data['page_size'] = 5
		data['count_page'] = current_table.get_count_page(page_size=data['page_size'])
		data['page_number'] = 0
		data['entries'] = current_table.select(pagination=(data['page_size'], data['page_size'] * data['page_number']))
		return render_template('table.html', **data)

	fields_number = request.args.getlist('fields_number[]', type=int)
	compare_number = request.args.getlist('comparison_operators[]', type=int)
	values = request.args.getlist('values[]')
	logical_number = request.args.get('logical_operation', type=int)
	sorted_fields_number = request.args.getlist('sorted_fields_number[]', type=int)

	data['page_size'] = request.args.get('page_size', type=int)
	data['count_page'] = request.args.get('count_page', type=int)
	data['page_number'] = request.args.get('page_number', type=int)

	try:
		conditions = cond.Conditions(columns=current_table.convert_to_columns(fields_number),
									 comparison_number=compare_number,
									 logical_number=logical_number,
									 values=values)
		data['count_page'] = current_table.get_count_page(conditions=conditions, page_size=data['page_size'])
		data['page_number'] = 0 if data['count_page'] - 1 < data['page_number'] else data['page_number']
		data['entries'] = current_table.select(conditions=conditions,
											   sorted_fields_number=sorted_fields_number,
											   pagination=(data['page_size'], data['page_size'] * data['page_number']))
		data['error'] = 0
	except ValueError:
		data['error'] = 1

	return jsonify(data)

@app.route('/analytics')
def analytics():
	data = get_metadate()
	data['url'] = 'analytics_metadate'
	return render_template('navigation.html', **data)

@app.route('/analytics/<int:table>', methods=['GET'])
def analytics_metadate(table):
	data = get_metadate()
	if table < 0 or table >= len(data['tables']): return

	data['url'] = 'analytics_metadate'
	current_table = get_current_table(table)
	data['table_number'] = table
	data['coordinates'] = current_table.fields_title()
	data['id_index'] = current_table.get_index_id()
	data['title_columns'] = current_table.fields_title()
	return render_template('analytics.html', **data)


@app.route('/analytics/<int:table>/<int:x>/<int:y>', methods=['GET'])
def build_grouping(table, x, y):
	data = get_metadate()
	if table < 0 or table >= len(data['tables']) : return
	if not table in [4, 5, 8]: return 

	fields_number = request.args.getlist('fields_number[]', type=int)
	compare_number = request.args.getlist('comparison_operators[]', type=int)
	values = request.args.getlist('values[]')
	logical_number = request.args.get('logical_operation', type=int)
	target_table = request.args.getlist('target_table[]', type=int)
	current_table = get_current_table(table)
	data['index_id'] = current_table.get_index_id()

	try:
		conditions = cond.Conditions(columns=current_table.convert_to_columns(fields_number),
									 comparison_number=compare_number,
									 logical_number=logical_number,
									 values=values)
		entries = current_table.select(conditions=conditions, sorted_fields_number=[x] + [y],
									   target_number=[x] + [y] + [data['index_id']] + target_table)
	except ValueError:
		data['error'] = 1
		return jsonify(data)

	tables = dict()
	x_fields = OrderedDict()
	y_fields = OrderedDict()
	id_for_x_y = current_table.get_data_for_edit_card()



	for entry in entries:
		e_x = str(entry[0])
		e_y = str(entry[1])
		if not e_x in tables:
			tables[e_x] = dict()
			tables[e_x][e_y] = list()
		if not e_y in tables[e_x]:
			tables[e_x][e_y] = list()
		conf = True if current_table.get_conflict_by_id(entry[2]) else False
		tables[e_x][e_y].append(list(entry[3::]) + [conf, ])

		x_fields[e_x] = [xx[1] for xx in id_for_x_y[x].get('values') if xx[0] == e_x][0]
		y_fields[e_y] = [xx[1] for xx in id_for_x_y[y].get('values') if xx[0] == e_y][0]

	data['index_id'] = current_table.get_index_id()
	data['error'] = 0
	data['x_fields'] = list([k, v] for k, v in x_fields.items())
	data['y_fields'] = list([k, v] for k, v in y_fields.items())
	data['tables'] = tables

	print(tables)
	print('KeK')

	return jsonify(data)

@app.route('/conflicts_row', methods=['GET'])
@app.route('/conflicts_row/<int:id_row>', methods=['GET'])
def get_meta_conf(id_row=None):
	if id_row is None:
		return
	data = get_metadate()
	table = get_current_table(8)
	data['current_row'] = table.get_row_by_id(id_row)
	data['index_id'] = table.get_index_id()
	data['cur_id'] = id_row
	return render_template("conflicts.html", **data)

@app.route('/conflicts_row', methods=['POST'])
@app.route('/conflicts_row/<int:id_row>', methods=['POST'])
def get_conflicts_row(id_row=None):
	if id is None:
		return
	data = get_metadate()
	table = get_current_table(8)

	data['current_row'] = table.get_row_by_id(id_row)
	data['index_id'] = table.get_index_id()
	data['cur_id'] = id_row
	data['legend'] = 'Конфликты в строке с идентификатором ' + str(id_row)
	data['title_columns'] = table.fields_title()

	conflicts = table.get_conflict_by_id(id_row)
	conflicts = [list(x) for x in conflicts]
	if not conflicts:
		data['error'] = 1
		data['conflicts'] = []
		data['legend'] = 'У строки с идентификатором ' + str(id_row) + ' конфликтов нет'
		return jsonify(data)

	data['error'] = 0
	for i in range(len(conflicts)):
		conflicts[i][0] = table.get_row_by_id(conflicts[i][0])
	data['conflicts'] = conflicts

	print(conflicts)
	return jsonify(data)

@app.route("/tree_conflicts", methods=['GET'])
def tree_conflicts():
	data=get_metadate()
	table = get_current_table(8)
	entries = table.get_all_conflicts()
	type = OrderedDict()
	for i in range(len(entries)):
		type_name = entries[i][2]
		if not type_name in type:
			type[type_name] = []
		str_conf = str(entries[i][0]) + ' - ' + str(entries[i][1])
		row_to = table.get_row_by_id(entries[i][0])
		row_from = table.get_row_by_id(entries[i][1])
		type[type_name].append([str_conf, row_to, row_from])

	data['type'] = list(type.keys())
	data['index_id'] = table.get_index_id()
	data['title_columns'] = table.fields_title()
	data['entries'] = type
	print(type)
	return render_template('tree_conflicts.html', **data)


@app.route('/update/<int:table>', methods=['GET'])
@app.route('/update/<int:table>/<int:id_row>', methods=['GET'])
def create_update_card(table=None, id_row=None):
	data = get_metadate()
	if table < 0 or table >= len(data['tables']): return

	current_table = get_current_table(table) # !!
	data['legend'] = 'Обновление записи с идентификатор ' + str(id_row)
	data['table_number'] = table
	data['title_columns'] = current_table.fields_title()
	data['edit_card'] = current_table.get_data_for_edit_card()
	data['index_id'] = current_table.get_index_id()
	data['cur_id'] = id_row
	data['current_row'] = current_table.get_row_by_id(id_row)
	return render_template("update.html", **data)

@app.route('/update/<int:table>', methods=['POST'])
@app.route('/update/<int:table>/<int:id_row>', methods=['POST'])
def update_row(table=None, id_row=None):
	data = get_metadate()
	if table < 0 or table >= len(data['tables']): return

	current_table = get_current_table(table)
	data['edit_card'] = current_table.get_data_for_edit_card()

	conf = True if current_table.get_conflict_by_id(id_row) else False
	data['current_row'] = current_table.get_row_by_id(id_row) + [conf, ]
	data['index_id'] = current_table.get_index_id()

	values = request.form.getlist('values[]')
	fields_number = request.form.getlist('fields_number[]', type=int)
	print("dd", values)
	try:
		values = current_table.convert_values(values, fields_number)
		current_table.update_by_id(id=id_row, values=values, updated_fields_number=fields_number)

		conf = True if current_table.get_conflict_by_id(id_row) else False
		data['current_row'] = current_table.get_row_by_id(id_row) + [conf, ]
		data['error'] = 0
	except ValueError:
		data['error'] = 1
	return jsonify(data)


@app.route('/insert/<int:table>', methods=['GET'])
def create_insert_card(table=None):
	data = get_metadate()
	if table < 0 or table >= len(data['tables']): return

	current_table = get_current_table(table)
	data['legend'] = 'Вставить новую запись в таблицу ' + current_table.caption
	data['table_number'] = table
	data['index_id'] = current_table.get_index_id()
	data['title_columns'] = current_table.fields_title()
	data['edit_card'] = current_table.get_data_for_edit_card()
	return render_template('insert.html', **data)


@app.route('/insert/<int:table>', methods=['POST'])
def insert_row(table):
	data = get_metadate()
	if table < 0 or table >= len(data['tables']): return

	current_table = get_current_table(table)
	values = request.form.getlist('values[]')
	try:
		values = current_table.convert_values(values)
		current_table.insert_row(values)
		data['error'] = 0
	except ValueError:
		data['error'] = 1
	return jsonify(data)

@app.route('/delete/<int:table>/<int:id_row>', methods=['POST'])
def delete_row(table, id_row):
	data = get_metadate()
	if table < 0 or table >= len(data['tables']): return

	current_table = get_current_table(table)
	current_table.get_row_by_id(id_row)
	current_table.delete_by_id(id_row)

	data = {}
	return jsonify(data)


if __name__ == "__main__":
	app.run(debug=True)
