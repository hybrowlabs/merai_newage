# Copyright (c) 2026, Siddhant Hybrowlabs and contributors
# For license information, please see license.txt

import frappe

import frappe
from frappe import _

def execute(filters=None):
	filters = filters or {}

	conditions = []
	values = {}

	if filters.get("from_date"):
		conditions.append("creation >= %(from_date)s")
		values["from_date"] = filters["from_date"]

	if filters.get("to_date"):
		conditions.append("creation <= %(to_date)s")
		values["to_date"] = filters["to_date"]

	if filters.get("robot_serial_no"):
		conditions.append("robot_serial_no = %(robot_serial_no)s")
		values["robot_serial_no"] = filters["robot_serial_no"]

	if filters.get("hospital_name"):
		conditions.append("hospital_name = %(hospital_name)s")
		values["hospital_name"] = filters["hospital_name"]

	if filters.get("priorty"):
		conditions.append("priorty = %(priorty)s")
		values["priorty"] = filters["priorty"]

	if filters.get("status"):
		conditions.append("status = %(status)s")
		values["status"] = filters["status"]

	where_clause = ""
	if conditions:
		where_clause = "WHERE " + " AND ".join(conditions)

	columns = [
		{
			"label": _("Ticket"),
			"fieldname": "name",
			"fieldtype": "Link",
			"options": "Ticket Master",
			"width": 140
		},
		{
			"label": _("State"),
			"fieldname": "state",
			"fieldtype": "Link",
			"options": "State",
			"width": 140
		},
		{
			"label": _("Robot Serial No"),
			"fieldname": "robot_serial_no",
			"fieldtype": "Link",
			"options": "Robot Tracker",
			"width": 180
		},
		{
			"label": _("Hospital"),
			"fieldname": "hospital_name",
			"fieldtype": "Link",
			"options": "Account Master",
			"width": 180
		},
		
		{
			"label": _("Priority"),
			"fieldname": "priorty",
			"width": 100
		},
		{
			"label": _("Status"),
			"fieldname": "status",
			"width": 120
		},
		{
			"label": _("Created On"),
			"fieldname": "creation",
			"fieldtype": "Datetime",
			"width": 160
		}
	]

	data = frappe.db.sql(f"""
		SELECT
			name,
			state,
			robot_serial_no,
			hospital_name,
			priorty,
			status,
			creation
		FROM `tabTicket Master`
		{where_clause}
		ORDER BY creation DESC
	""", values, as_dict=True)

	return columns, data


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_robot_serials(doctype, txt, searchfield, start, page_len, filters):
	conditions = ""
	values = {}

	if filters.get("from_date"):
		conditions += " AND creation >= %(from_date)s"
		values["from_date"] = filters["from_date"]

	if filters.get("to_date"):
		conditions += " AND creation <= %(to_date)s"
		values["to_date"] = filters["to_date"]

	return frappe.db.sql(f"""
		SELECT DISTINCT robot_serial_no
		FROM `tabTicket Master`
		WHERE robot_serial_no IS NOT NULL
		{conditions}
		AND robot_serial_no LIKE %(txt)s
		LIMIT %(start)s, %(page_len)s
	""", {
		**values,
		"txt": f"%{txt}%",
		"start": start,
		"page_len": page_len
	})


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_hospitals(doctype, txt, searchfield, start, page_len, filters):
	conditions = ""
	values = {}

	if filters.get("from_date"):
		conditions += " AND creation >= %(from_date)s"
		values["from_date"] = filters["from_date"]

	if filters.get("to_date"):
		conditions += " AND creation <= %(to_date)s"
		values["to_date"] = filters["to_date"]

	return frappe.db.sql(f"""
		SELECT DISTINCT hospital_name
		FROM `tabTicket Master`
		WHERE hospital_name IS NOT NULL
		{conditions}
		AND hospital_name LIKE %(txt)s
		LIMIT %(start)s, %(page_len)s
	""", {
		**values,
		"txt": f"%{txt}%",
		"start": start,
		"page_len": page_len
	})



@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_state(doctype, txt, searchfield, start, page_len, filters):
	conditions = ""
	values = {}

	if filters.get("from_date"):
		conditions += " AND creation >= %(from_date)s"
		values["from_date"] = filters["from_date"]

	if filters.get("to_date"):
		conditions += " AND creation <= %(to_date)s"
		values["to_date"] = filters["to_date"]

	return frappe.db.sql(f"""
		SELECT DISTINCT state
		FROM `tabTicket Master`
		WHERE state IS NOT NULL
		{conditions}
		AND state LIKE %(txt)s
		LIMIT %(start)s, %(page_len)s
	""", {
		**values,
		"txt": f"%{txt}%",
		"start": start,
		"page_len": page_len
	})
