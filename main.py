from flask import Flask, request, render_template, g, jsonify
import condition
import tables as t
import fdb

app = Flask(__name__)


def get_db():
	if not hasattr(g, "fb_db"):
		g.fb_db = fdb.connect(
		dsn='db/TIMETABLE.fdb',
		user='sysdba',
		password='masterkey',
		charset='UTF8'
	)
	return g.fb_db


def execute(smth, val=()):
	print(smth)
	cur = get_db().cursor()
	cur.execute(smth, val)
	return cur.fetchall()

def convert_index(self, index):
	try:
		index = int(index)
		return index
	except ValueError:
		return None

@app.teardown_appcontext
def close_db(error):
	if hasattr(g, "man"):
		g.mng.fb_db.close()

@app.route("/<int:table>", methods=['GET', 'POST'] )
@app.route("/", methods=['GET', 'POST'])
def home(table=None):

	data = {}
	list_tables = t.BaseTable.tables()
	list_logic = condition.LogicalOperator.logical_operations()
	list_cond = condition.Compare.comparison_operators()
	data['tables'] = [x.caption for x in list_tables]
	data['coms'] = [x.caption for x in list_cond]
	data['logicals'] = [x.caption for x in list_logic]
	data['length_page_size'] = [5, 10, 15, 25]

	data['table'] = table
	if table is not None and 0 <= table < len(list_tables):
		current_table = list_tables[table]

		if request.method == 'POST':
			index_fields = request.form.getlist("fields[]", type=int)
			index_comps = request.form.getlist("comps[]", type=int)
			values = request.form.getlist("values[]")
			index_log = request.form.get("logical", type=int)
			index_sorted = request.form.getlist("order_field[]", type=int)

			logical_operator = list_logic[index_log]
			comps = []
			for i in index_comps:
				comps.append(list_cond[i])

			select_data = {'logical_operator':logical_operator,'index_fields': index_fields,'index_comps':comps,
							"values":values, 'index_sorted': index_sorted}
			try:
				sql, values = current_table.select_all(**select_data)
				data["entries"] = execute(sql, values)
				data['error'] = 0
			except ValueError:
				data['error'] = 1

			return jsonify(data)

		data['fields'] = current_table.fields_title
		data['title'] = current_table.fields_title
		data['entries'] = execute(current_table.select_all())

	return render_template('menu.html', **data)


if __name__ == "__main__":
	app.run(debug=True)	
