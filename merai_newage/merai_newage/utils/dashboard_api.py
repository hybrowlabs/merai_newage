

# Copyright (c) 2026, Siddhant Hybrowlabs and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import now_datetime, add_days, getdate
import json
from collections import defaultdict


@frappe.whitelist()
def get_year_overview():
	"""
	Get year-wise overview of tickets grouped by status (Open, Pending, Resolved)
	This loads WITHOUT any filters - shows ALL tickets ever created
	Draft = Open (red bar)
	"""
	try:
		# Get all tickets grouped by year and status
		tickets = frappe.db.sql("""
			SELECT 
				YEAR(creation) as year,
				workflow_state,
				COUNT(*) as count
			FROM `tabTicket Master`
			GROUP BY YEAR(creation), workflow_state
			ORDER BY year ASC
		""", as_dict=True)
		
		# Organize data by year
		year_data = defaultdict(lambda: {'open': 0, 'pending': 0, 'resolved': 0})
		
		for ticket in tickets:
			year = str(ticket.year)
			status = (ticket.workflow_state or 'Draft').strip()
			count = ticket.count
			
			# Map statuses to categories
			# Draft and Open = Open (red bar)
			if status in ['Draft', 'Open']:
				year_data[year]['open'] += count
			# Resolved = Resolved (green bar)
			elif status == 'Resolved':
				year_data[year]['resolved'] += count
			# Everything else = Pending (orange bar)
			else:
				year_data[year]['pending'] += count
		
		# Sort years and prepare data
		years = sorted(year_data.keys())
		open_counts = [year_data[y]['open'] for y in years]
		pending_counts = [year_data[y]['pending'] for y in years]
		resolved_counts = [year_data[y]['resolved'] for y in years]
		
		return {
			'years': years,
			'open': open_counts,
			'pending': pending_counts,
			'resolved': resolved_counts
		}
		
	except Exception as e:
		frappe.log_error(f"Error in get_year_overview: {str(e)}")
		return {
			'years': [],
			'open': [],
			'pending': [],
			'resolved': []
		}


@frappe.whitelist()
def get_dashboard_data(filters=None):
	"""
	Main API endpoint to fetch all dashboard data
	"""
	if isinstance(filters, str):
		filters = json.loads(filters)
	
	filters = filters or {}
	
	# Build conditions
	conditions = []
	values = {}
	
	if filters.get("from_date"):
		conditions.append("creation >= %(from_date)s")
		values["from_date"] = filters["from_date"] + " 00:00:00"
	
	if filters.get("to_date"):
		conditions.append("creation <= %(to_date)s")
		values["to_date"] = filters["to_date"] + " 23:59:59"
	
	if filters.get("state"):
		conditions.append("state = %(state)s")
		values["state"] = filters["state"]
	
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

		if filters["status"] == "Open":
			conditions.append("workflow_state = 'Draft'")

		elif filters["status"] == "Closed":
			conditions.append("workflow_state = 'Resolved'")

		elif filters["status"] == "Pending":
			conditions.append("""
				workflow_state NOT IN (
					'Draft',
					'Resolved'
				)
			""")
	
	where_clause = ""
	if conditions:
		where_clause = "WHERE " + " AND ".join(conditions)
	
	# Get all the data
	data = {
		"metrics": get_metrics(where_clause, values),
		"status_distribution": get_status_distribution(where_clause, values),
		"issue_type_distribution": get_issue_type_distribution(where_clause, values),
		"timeline_data": get_timeline_data(where_clause, values),
		"hospital_data": get_hospital_data(where_clause, values),
		"robot_data": get_robot_data(where_clause, values),
		"recent_tickets": get_recent_tickets(where_clause, values),
		"priority_distribution": get_priority_distribution(where_clause, values),
		"state_distribution": get_state_distribution(where_clause, values)
	}
	
	return data


def get_metrics(where_clause, values):
	"""Get key metrics for dashboard cards"""
	
	try:
		# Total tickets
		total_query = f"""
			SELECT COUNT(*) as count
			FROM `tabTicket Master`
			{where_clause}
		"""
		total = frappe.db.sql(total_query, values, as_dict=True)[0].count or 0
		
		# Resolved tickets (workflow_state = 'Resolved')
		resolved_conditions = where_clause
		if where_clause:
			resolved_conditions += " AND workflow_state = 'Resolved'"
		else:
			resolved_conditions = "WHERE workflow_state = 'Resolved'"
		
		resolved_query = f"""
			SELECT COUNT(*) as count
			FROM `tabTicket Master`
			{resolved_conditions}
		"""
		resolved = frappe.db.sql(resolved_query, values, as_dict=True)[0].count or 0
		
		# Cancelled tickets (workflow_state = 'Cancelled' OR docstatus = 2)
		cancelled_conditions = where_clause
		if where_clause:
			cancelled_conditions += " AND (workflow_state = 'Cancelled' OR docstatus = 2)"
		else:
			cancelled_conditions = "WHERE (workflow_state = 'Cancelled' OR docstatus = 2)"
		
		cancelled_query = f"""
			SELECT COUNT(*) as count
			FROM `tabTicket Master`
			{cancelled_conditions}
		"""
		cancelled = frappe.db.sql(cancelled_query, values, as_dict=True)[0].count or 0
		
		# Pending tickets (NOT resolved AND NOT cancelled AND docstatus != 1)
		pending_conditions = where_clause
		if where_clause:
			pending_conditions += " AND workflow_state != 'Resolved' AND workflow_state != 'Cancelled' AND docstatus != 2 AND docstatus != 1"
		else:
			pending_conditions = "WHERE workflow_state != 'Resolved' AND workflow_state != 'Cancelled' AND docstatus != 2 AND docstatus != 1"
		
		pending_query = f"""
			SELECT COUNT(*) as count
			FROM `tabTicket Master`
			{pending_conditions}
		"""
		pending = frappe.db.sql(pending_query, values, as_dict=True)[0].count or 0
		
		# Average resolution time (only for resolved tickets)
		avg_time_query = f"""
			SELECT AVG(DATEDIFF(modified, creation)) as avg_days
			FROM `tabTicket Master`
			{where_clause}
			{'AND' if where_clause else 'WHERE'} workflow_state = 'Resolved'
		"""
		avg_result = frappe.db.sql(avg_time_query, values, as_dict=True)
		avg_time = round(avg_result[0].avg_days, 1) if avg_result and avg_result[0].avg_days else 0
		
		# This week's tickets
		week_values = values.copy()
		week_values["week_start"] = add_days(now_datetime(), -7)
		
		week_conditions = where_clause
		if where_clause:
			week_conditions += " AND creation >= %(week_start)s"
		else:
			week_conditions = "WHERE creation >= %(week_start)s"
		
		week_query = f"""
			SELECT COUNT(*) as count
			FROM `tabTicket Master`
			{week_conditions}
		"""
		week_count = frappe.db.sql(week_query, week_values, as_dict=True)[0].count or 0
		
		return {
			"total": total,
			"resolved": resolved,
			"pending": pending,
			"cancelled": cancelled,
			"avg_resolution_time": avg_time,
			"week_count": week_count,
			"resolved_percentage": round((resolved / total * 100), 1) if total > 0 else 0,
			"pending_percentage": round((pending / total * 100), 1) if total > 0 else 0,
			"cancelled_percentage": round((cancelled / total * 100), 1) if total > 0 else 0
		}
	except Exception as e:
		frappe.log_error(f"Error in get_metrics: {str(e)}")
		return {
			"total": 0,
			"resolved": 0,
			"pending": 0,
			"cancelled": 0,
			"avg_resolution_time": 0,
			"week_count": 0,
			"resolved_percentage": 0,
			"pending_percentage": 0,
			"cancelled_percentage": 0
		}


def get_status_distribution(where_clause, values):
	"""Get ticket count by workflow state"""
	try:
		query = f"""
			SELECT workflow_state, COUNT(*) as count
			FROM `tabTicket Master`
			{where_clause}
			GROUP BY workflow_state
			ORDER BY count DESC
		"""
		print("query=============771",query,"where_clause",where_clause)
		
		data = frappe.db.sql(query, values, as_dict=True)
		print("data-----------773",data)
		return {
			"labels": [d.workflow_state for d in data],
			"data": [d.count for d in data]
		}
	except Exception as e:
		frappe.log_error(f"Error in get_status_distribution: {str(e)}")
		return {"labels": [], "data": []}


def get_issue_type_distribution(where_clause, values):
	"""Get ticket count by issue type"""
	try:
		query = f"""
			SELECT issue_type, COUNT(*) as count
			FROM `tabTicket Master`
			{where_clause}
			GROUP BY issue_type
			ORDER BY count DESC
		"""
		
		data = frappe.db.sql(query, values, as_dict=True)
		return {
			"labels": [d.issue_type or "Not Specified" for d in data],
			"data": [d.count for d in data]
		}
	except Exception as e:
		frappe.log_error(f"Error in get_issue_type_distribution: {str(e)}")
		return {"labels": [], "data": []}


def get_priority_distribution(where_clause, values):
	"""Get ticket count by priority"""
	try:
		query = f"""
			SELECT priorty, COUNT(*) as count
			FROM `tabTicket Master`
			{where_clause}
			GROUP BY priorty
			ORDER BY count DESC
		"""
		
		data = frappe.db.sql(query, values, as_dict=True)
		return {
			"labels": [d.priorty or "Not Set" for d in data],
			"data": [d.count for d in data]
		}
	except Exception as e:
		frappe.log_error(f"Error in get_priority_distribution: {str(e)}")
		return {"labels": [], "data": []}


def get_state_distribution(where_clause, values):
	"""Get ticket count by state"""
	try:
		query = f"""
			SELECT state, COUNT(*) as count
			FROM `tabTicket Master`
			{where_clause}
			GROUP BY state
			ORDER BY count DESC
		"""
		
		data = frappe.db.sql(query, values, as_dict=True)
		return {
			"labels": [d.state or "Not Specified" for d in data],
			"data": [d.count for d in data]
		}
	except Exception as e:
		frappe.log_error(f"Error in get_state_distribution: {str(e)}")
		return {"labels": [], "data": []}


def get_timeline_data(where_clause, values):
	"""Get tickets created over time within the selected date range"""
	try:
		query = f"""
			SELECT 
				DATE(creation) as date,
				COUNT(*) as count
			FROM `tabTicket Master`
			{where_clause}
			GROUP BY DATE(creation)
			ORDER BY date
		"""
		
		data = frappe.db.sql(query, values, as_dict=True)
		
		return {
			"labels": [str(d.date) for d in data],
			"data": [d.count for d in data]
		}
	except Exception as e:
		frappe.log_error(f"Error in get_timeline_data: {str(e)}")
		return {"labels": [], "data": []}


def get_hospital_data(where_clause, values):
	"""Get top hospitals by ticket count"""
	try:
		query = f"""
			SELECT hospital_name, COUNT(*) as count
			FROM `tabTicket Master`
			{where_clause}
			GROUP BY hospital_name
			ORDER BY count DESC
		"""
		
		data = frappe.db.sql(query, values, as_dict=True)
		return {
			"labels": [d.hospital_name or "Not Specified" for d in data],
			"data": [d.count for d in data]
		}
	except Exception as e:
		frappe.log_error(f"Error in get_hospital_data: {str(e)}")
		return {"labels": [], "data": []}


def get_robot_data(where_clause, values):
	"""Get robots with most issues"""
	try:
		query = f"""
			SELECT robot_serial_no, COUNT(*) as count
			FROM `tabTicket Master`
			{where_clause}
			GROUP BY robot_serial_no
			ORDER BY count DESC
		"""
		
		data = frappe.db.sql(query, values, as_dict=True)
		return {
			"labels": [d.robot_serial_no or "Not Specified" for d in data],
			"data": [d.count for d in data]
		}
	except Exception as e:
		frappe.log_error(f"Error in get_robot_data: {str(e)}")
		return {"labels": [], "data": []}



import re
import frappe


def get_employee_name(employee_code):
	"""
	Resolve a single employee code / user email to a display name.
	Checks Employee doctype first, then User, falls back to the raw value.
	"""
	if not employee_code or employee_code == "-":
		return employee_code or "-"

	# ── Try Employee doctype (employee_id / name field) ──
	emp_name = frappe.db.get_value(
		"Employee",
		{"employee": employee_code},   # employee field stores the code like 37001
		"employee_name"
	)
	if emp_name:
		return emp_name

	# ── Try by employee name directly (some setups store it differently) ──
	emp_name = frappe.db.get_value(
		"Employee",
		{"name": employee_code},
		"employee_name"
	)
	if emp_name:
		return emp_name

	# ── Try User doctype (in case raised_by is an email / user id) ──
	user_name = frappe.db.get_value(
		"User",
		{"name": employee_code},
		"full_name"
	)
	if user_name:
		return user_name

	# ── Fall back to the raw code ──
	return employee_code


def get_recent_tickets(where_clause, values, limit=100):
	"""Get recent tickets for the table - filtered by date range"""

	try:
		query = f"""
			SELECT
				name,
				workflow_state,
				robot_serial_no,
				ticket_subject,
				hospital_name,
				issue_type,
				state,
				priorty,
				DATEDIFF(NOW(), creation) as days_open,
				creation,
				modified,
				raised_by,
				issue_reported,
				city
			FROM `tabTicket Master`
			{where_clause}
			ORDER BY creation DESC
			LIMIT {limit}
		"""

		tickets = frappe.db.sql(query, values, as_dict=True)

		# ── Build a set of all unique employee codes that appear ──
		# so we can batch-resolve them in one query instead of N queries
		all_codes = set()
		for ticket in tickets:
			if ticket.get("raised_by"):
				all_codes.add(ticket["raised_by"])

		# Also collect engineer codes from child table
		ticket_names = [t["name"] for t in tickets]
		engineer_rows = []
		if ticket_names:
			engineer_rows = frappe.db.sql("""
				SELECT parent, software_engineer
				FROM `tabSoftware Team Members`
				WHERE parent IN %(parents)s
				  AND software_engineer IS NOT NULL
				  AND software_engineer != ''
			""", {"parents": ticket_names}, as_dict=True)

			for row in engineer_rows:
				if row.software_engineer:
					all_codes.add(row.software_engineer)

		# ── Batch-resolve all codes → names ──
		code_to_name = {}
		if all_codes:
			# Resolve via Employee doctype
			emp_records = frappe.db.sql("""
				SELECT employee, employee_name
				FROM `tabEmployee`
				WHERE employee IN %(codes)s
			""", {"codes": list(all_codes)}, as_dict=True)

			for emp in emp_records:
				code_to_name[emp.employee] = emp.employee_name

			# For any codes still unresolved, try User doctype
			unresolved = [c for c in all_codes if c not in code_to_name]
			if unresolved:
				user_records = frappe.db.sql("""
					SELECT name, full_name
					FROM `tabUser`
					WHERE name IN %(codes)s
				""", {"codes": unresolved}, as_dict=True)

				for user in user_records:
					code_to_name[user.name] = user.full_name

		# ── Group engineer rows by parent ticket ──
		engineers_by_ticket = {}
		for row in engineer_rows:
			engineers_by_ticket.setdefault(row.parent, []).append(row.software_engineer)

		# ── Enrich each ticket ──
		for ticket in tickets:

			# Resolve engineers (Assign To)
			raw_engineers = engineers_by_ticket.get(ticket["name"], [])
			if raw_engineers:
				ticket["engineers"] = ", ".join(
					f"{code_to_name[code]}\n({code})" if code in code_to_name else code
					for code in raw_engineers
					if code
				)
			else:
				ticket["engineers"] = "-"

			# Resolve raised_by
			raw_raised = ticket.get("raised_by") or ""
			# ticket["raised_by"] = code_to_name.get(raw_raised, raw_raised) or "-"
			if raw_raised and raw_raised in code_to_name:
				ticket["raised_by"] = f"{code_to_name[raw_raised]}\n({raw_raised})"
			else:
				ticket["raised_by"] = raw_raised or "-"

			# Clean issue_reported HTML
			description = ticket.get("issue_reported") or ""
			description = re.sub(r"<[^>]*>", " ", description)
			description = re.sub(r"&nbsp;|&amp;|&lt;|&gt;", " ", description)
			description = re.sub(r"\s+", " ", description).strip()
			ticket["issue_reported"] = description or "-"

		return tickets

	except Exception as e:
		frappe.log_error(f"Error in get_recent_tickets: {str(e)}")
		return []

@frappe.whitelist()
def get_filter_options(filter_type, from_date=None, to_date=None):
	"""
	Get available filter options based on date range
	"""
	try:
		conditions = []
		values = {}
		
		if from_date:
			conditions.append("creation >= %(from_date)s")
			values["from_date"] = from_date + " 00:00:00"
		
		if to_date:
			conditions.append("creation <= %(to_date)s")
			values["to_date"] = to_date + " 23:59:59"
		
		where_clause = ""
		if conditions:
			where_clause = "WHERE " + " AND ".join(conditions)
		
		if filter_type == "state":
			query = f"""
				SELECT DISTINCT state
				FROM `tabTicket Master`
				{where_clause}
				ORDER BY state
			"""
		elif filter_type == "hospital":
			query = f"""
				SELECT DISTINCT hospital_name
				FROM `tabTicket Master`
				{where_clause}
				ORDER BY hospital_name
			"""
		elif filter_type == "robot":
			query = f"""
				SELECT DISTINCT robot_serial_no
				FROM `tabTicket Master`
				{where_clause}
				ORDER BY robot_serial_no
			"""
		elif filter_type == "status":

			open_exists = frappe.db.exists(
				"Ticket Master",
				{
					"workflow_state": "Draft"
				}
			)

			closed_exists = frappe.db.exists(
				"Ticket Master",
				{
					"workflow_state": "Resolved"
				}
			)

			pending_exists = frappe.db.sql(f"""
				SELECT name
				FROM `tabTicket Master`
				{where_clause}
				{'AND' if where_clause else 'WHERE'}
				workflow_state NOT IN ('Draft', 'Resolved')
				LIMIT 1
			""", values)

			statuses = []

			if open_exists:
				statuses.append("Open")

			if pending_exists:
				statuses.append("Pending")

			if closed_exists:
				statuses.append("Closed")

			return statuses
		elif filter_type == "priority":
			query = f"""
				SELECT DISTINCT priorty
				FROM `tabTicket Master`
				{where_clause}
				ORDER BY priorty
			"""
		elif filter_type == "issue_type":
			query = f"""
				SELECT DISTINCT issue_type
				FROM `tabTicket Master`
				{where_clause}
				ORDER BY issue_type
			"""
		else:
			return []
		
		data = frappe.db.sql(query, values, as_list=True)
		return [d[0] for d in data if d[0]]
	except Exception as e:
		frappe.log_error(f"Error in get_filter_options: {str(e)}")
		return []


@frappe.whitelist()
def get_ticket_details(ticket_id):
	"""
	Get detailed information for a specific ticket
	"""
	try:
		ticket = frappe.get_doc("Ticket Master", ticket_id)
		return ticket.as_dict()
	except Exception as e:
		frappe.log_error(f"Error in get_ticket_details: {str(e)}")
		return None
import calendar
@frappe.whitelist()
def get_monthly_overview(year=None):
	if not year:
		year = frappe.utils.now_datetime().year
	year = int(year)
	
	months = list(range(1, 13))
	open_data, pending_data, resolved_data = [], [], []
	
	for m in months:
		start = f"{year}-{str(m).zfill(2)}-01 00:00:00"
		end_day = calendar.monthrange(year, m)[1]
		end = f"{year}-{str(m).zfill(2)}-{end_day} 23:59:59"
		
		open_data.append(frappe.db.count('Ticket Master', {'creation': ['between', [start, end]], 'workflow_state': 'Draft'}))
		pending_data.append(frappe.db.count('Ticket Master', {'creation': ['between', [start, end]], 'workflow_state': ['not in', ['Draft', 'Resolved','Rejected']]}))
		resolved_data.append(frappe.db.count('Ticket Master', {'creation': ['between', [start, end]], 'workflow_state': 'Resolved'}))
	
	return {'months': months, 'open': open_data, 'pending': pending_data, 'resolved': resolved_data}





import frappe
import json
import re

@frappe.whitelist()
def get_item_master_list():

	items = frappe.get_all(
		"Item",
		fields=["item_code", "item_name"],
		order_by="item_name asc",
		limit=500
	)

	return items


@frappe.whitelist()
def get_defected_materials_report(items):

	if isinstance(items, str):
		items = json.loads(items)

	result_items = []

	global_counts = {
		"total": 0,
		"open": 0,
		"pending": 0,
		"resolved": 0,
		"cancelled": 0
	}

	for item_code in items:

		# GET CHILD TABLE ROWS
		child_rows = frappe.get_all(
			"Robot Materials",
			filters={
				"item": item_code
			},
			fields=[
				"parent",
				"qty"
			]
		)

		if not child_rows:
			continue

		# UNIQUE TICKET IDS
		parent_names = list(set([
			d.parent for d in child_rows
		]))

		# QTY MAP
		qty_map = {}

		for d in child_rows:
			qty_map[d.parent] = d.qty

		# GET TICKET MASTER DATA
		tickets = frappe.get_all(
			"Ticket Master",
			filters={
				"name": ["in", parent_names]
			},
			fields=[
				"name",
				"creation",
				"modified",
				"robot_serial_no",
				"hospital_name",
				"ticket_subject",
				"city",
				"state",
				"issue_type",
				"raised_by",
				"issue_reported",
				"workflow_state"
			]
		)

		# ── BATCH COLLECT ALL EMPLOYEE CODES ──────────────────────
		# Gather raised_by codes
		all_codes = set()
		for t in tickets:
			if t.get("raised_by"):
				all_codes.add(t["raised_by"])

		# Gather engineer codes from child table (all tickets at once)
		ticket_names = [t["name"] for t in tickets]
		engineer_rows_all = []
		if ticket_names:
			engineer_rows_all = frappe.db.sql("""
				SELECT parent, software_engineer
				FROM `tabSoftware Team Members`
				WHERE parent IN %(parents)s
				  AND software_engineer IS NOT NULL
				  AND software_engineer != ''
			""", {"parents": ticket_names}, as_dict=True)

			for row in engineer_rows_all:
				if row.software_engineer:
					all_codes.add(row.software_engineer)

		# ── BATCH RESOLVE CODES → NAMES ───────────────────────────
		code_to_name = {}
		if all_codes:
			# Try Employee doctype first
			emp_records = frappe.db.sql("""
				SELECT employee, employee_name
				FROM `tabEmployee`
				WHERE employee IN %(codes)s
			""", {"codes": list(all_codes)}, as_dict=True)

			for emp in emp_records:
				code_to_name[emp.employee] = emp.employee_name

			# For any still unresolved, try User doctype (email-based)
			unresolved = [c for c in all_codes if c not in code_to_name]
			if unresolved:
				user_records = frappe.db.sql("""
					SELECT name, full_name
					FROM `tabUser`
					WHERE name IN %(codes)s
				""", {"codes": unresolved}, as_dict=True)

				for user in user_records:
					code_to_name[user.name] = user.full_name

		# ── GROUP ENGINEERS BY TICKET ─────────────────────────────
		engineers_by_ticket = {}
		for row in engineer_rows_all:
			engineers_by_ticket.setdefault(row.parent, []).append(
				row.software_engineer
			)

		# ── ENRICH EACH TICKET ────────────────────────────────────
		counts = {
			"total": len(tickets),
			"open": 0,
			"pending": 0,
			"resolved": 0,
			"cancelled": 0
		}

		for t in tickets:

			# Resolve engineers (Assign To) — use batch map
			raw_engineers = engineers_by_ticket.get(t["name"], [])
			if raw_engineers:
				t["engineers"] = ", ".join(
					code_to_name.get(code, code)
					for code in raw_engineers
					if code
				)
			else:
				t["engineers"] = "-"

			# Resolve raised_by
			raw_raised = t.get("raised_by") or ""
			t["raised_by"] = code_to_name.get(raw_raised, raw_raised) or "-"

			# CLEAN DESCRIPTION
			description = t.get("issue_reported") or ""

			# REMOVE HTML TAGS
			description = re.sub(
				r"<[^>]*>",
				" ",
				description
			)

			# REMOVE HTML ENTITIES
			description = re.sub(
				r"&nbsp;|&amp;|&lt;|&gt;",
				" ",
				description
			)

			# REMOVE EXTRA SPACES
			description = re.sub(
				r"\s+",
				" ",
				description
			).strip()

			t["issue_reported"] = description or "-"

			# EXTRA DATA
			t["defect_item_code"] = item_code

			t["defect_qty"] = qty_map.get(
				t["name"],
				0
			)

			# STATUS COUNTS
			state = (
				t.get("workflow_state") or ""
			).lower()

			if "resolved" in state:

				counts["resolved"] += 1

			elif "pending" in state:

				counts["pending"] += 1

			elif "cancel" in state:

				counts["cancelled"] += 1

			else:

				counts["open"] += 1

		# UPDATE GLOBAL COUNTS
		for k in global_counts:

			global_counts[k] += counts[k]

		# ITEM DETAILS
		item_doc = frappe.db.get_value(
			"Item",
			item_code,
			["item_code", "item_name"],
			as_dict=True
		) or {}

		result_items.append({

			"item_code": item_code,

			"item_name": item_doc.get(
				"item_name",
				item_code
			),

			"metrics": counts,

			"tickets": tickets
		})

	return {

		"global_metrics": global_counts,

		"items": result_items
	}