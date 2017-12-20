
var fields = []
{% for t in title -%}
fields.push("{{ t }}")
{% endfor %}

var compares = []
{% for c in comparison_operators %}
compares.push("{{ c }}")
{% endfor %}
    
var sorted_fields = []



function add_button(){
	var $fieldset = $("fieldset")
	var $d_col = $("<div>", { "class": "col" })

	var $select_op = $("<option>")
	var $sel_field = $("<select>", { "class": "form-control no-arrow", "name": "fields_number", "id": "field_select" })

	var $op
	for (var i = 0; i < fields.length; i++){
		$op = $select_op.clone()
		$op.val(i)
		$op.html(fields[i])
		$sel_field.append($op)
	}

	var $sel_cmp = $("<select>", { "class": "form-control no-arrow", "name": "comparison_operators"})
	for (var i = 0; i < compares.length; i++){
		$op = $select_op.clone()
		$op.val(i)
		$op.html(compares[i])
		$sel_cmp.append($op)
	}

	var $in_value = $("<input>", { "class": "form-control", "type": "search", "name":"values", "id":"val_select"})
	var $d_button = $("<div>", { "class": "col" })
	var $button = $("<button>", { "class": "btn", "name": "remove", "onclick": "remove_condition(this)" })
	$button.html("-")

	$d_button.append($button)
	$d_col.append($sel_field)
	$d_col.append($sel_cmp)
	$d_col.append($in_value)
	$d_col.append($d_button)
	$fieldset.append($d_col)
}

function remove_condition(but) {
	var $but = $(but)
	var $statements = $("fieldset.form-group > div").nextAll()
	for (var i = 0; i < $statements.length; i++)
	 	if ($but[0] == $statements.eq(i).find("button")[0])
	 		$statements.eq(i).remove()
	page_number = 0
	send_parameters()
}

function add_or_remove_sort(){
    var $this = $(this)
    var index_sorted = sorted_fields.indexOf($this.attr("id"))
    if (index_sorted == -1){
        sorted_fields.push($this.attr("id"))
        $this.addClass("active")
        var $i = $("<i>", {"class":"fa fa-sort-asc", "aria-hidden":"true"})
        $this.append($i)
    }
    else {
        sorted_fields.splice(index_sorted, 1)
        $this.removeClass("active")
        $this.find("i").remove()
    }
    send_parameters()
}