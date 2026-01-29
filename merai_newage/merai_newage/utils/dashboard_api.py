# # Copyright (c) 2026, Siddhant Hybrowlabs and contributors
# # For license information, please see license.txt

# import frappe
# from frappe import _
# from frappe.utils import now_datetime, add_days, getdate
# import json


# @frappe.whitelist()
# def get_dashboard_data(filters=None):
# 	"""
# 	Main API endpoint to fetch all dashboard data
# 	"""
# 	if isinstance(filters, str):
# 		filters = json.loads(filters)
	
# 	filters = filters or {}
	
# 	# Build conditions
# 	conditions = []
# 	values = {}
	
# 	if filters.get("from_date"):
# 		conditions.append("creation >= %(from_date)s")
# 		values["from_date"] = filters["from_date"]
	
# 	if filters.get("to_date"):
# 		conditions.append("creation <= %(to_date)s")
# 		values["to_date"] = filters["to_date"]
	
# 	if filters.get("state"):
# 		conditions.append("state = %(state)s")
# 		values["state"] = filters["state"]
	
# 	if filters.get("robot_serial_no"):
# 		conditions.append("robot_serial_no = %(robot_serial_no)s")
# 		values["robot_serial_no"] = filters["robot_serial_no"]
	
# 	if filters.get("hospital_name"):
# 		conditions.append("hospital_name = %(hospital_name)s")
# 		values["hospital_name"] = filters["hospital_name"]
	
# 	if filters.get("priorty"):
# 		conditions.append("priorty = %(priorty)s")
# 		values["priorty"] = filters["priorty"]
	
# 	if filters.get("status"):
# 		conditions.append("status = %(status)s")
# 		values["status"] = filters["status"]
	
# 	where_clause = ""
# 	if conditions:
# 		where_clause = "WHERE " + " AND ".join(conditions)
	
# 	# Get all the data
# 	data = {
# 		"metrics": get_metrics(where_clause, values),
# 		"status_distribution": get_status_distribution(where_clause, values),
# 		"issue_type_distribution": get_issue_type_distribution(where_clause, values),
# 		"timeline_data": get_timeline_data(where_clause, values),
# 		"hospital_data": get_hospital_data(where_clause, values),
# 		"robot_data": get_robot_data(where_clause, values),
# 		"recent_tickets": get_recent_tickets(where_clause, values),
# 		"priority_distribution": get_priority_distribution(where_clause, values),
# 		"state_distribution": get_state_distribution(where_clause, values)
# 	}
	
# 	return data


# def get_metrics(where_clause, values):
# 	"""Get key metrics for dashboard cards"""
	
# 	try:
# 		# Total tickets
# 		total_query = f"""
# 			SELECT COUNT(*) as count
# 			FROM `tabTicket Master`
# 			{where_clause}
# 		"""
# 		total = frappe.db.sql(total_query, values, as_dict=True)[0].count or 0
		
# 		# Resolved tickets (workflow_state = 'Resolved')
# 		resolved_conditions = where_clause
# 		if where_clause:
# 			resolved_conditions += " AND workflow_state = 'Resolved'"
# 		else:
# 			resolved_conditions = "WHERE workflow_state = 'Resolved'"
		
# 		resolved_query = f"""
# 			SELECT COUNT(*) as count
# 			FROM `tabTicket Master`
# 			{resolved_conditions}
# 		"""
# 		resolved = frappe.db.sql(resolved_query, values, as_dict=True)[0].count or 0
		
# 		# Cancelled tickets (workflow_state = 'Cancelled' OR docstatus = 2)
# 		cancelled_conditions = where_clause
# 		if where_clause:
# 			cancelled_conditions += " AND (workflow_state = 'Cancelled' OR docstatus = 2)"
# 		else:
# 			cancelled_conditions = "WHERE (workflow_state = 'Cancelled' OR docstatus = 2)"
		
# 		cancelled_query = f"""
# 			SELECT COUNT(*) as count
# 			FROM `tabTicket Master`
# 			{cancelled_conditions}
# 		"""
# 		cancelled = frappe.db.sql(cancelled_query, values, as_dict=True)[0].count or 0
		
# 		# Pending tickets (NOT resolved AND NOT cancelled AND docstatus != 1)
# 		pending_conditions = where_clause
# 		if where_clause:
# 			pending_conditions += " AND workflow_state != 'Resolved' AND workflow_state != 'Cancelled' AND docstatus != 2 AND docstatus != 1"
# 		else:
# 			pending_conditions = "WHERE workflow_state != 'Resolved' AND workflow_state != 'Cancelled' AND docstatus != 2 AND docstatus != 1"
		
# 		pending_query = f"""
# 			SELECT COUNT(*) as count
# 			FROM `tabTicket Master`
# 			{pending_conditions}
# 		"""
# 		pending = frappe.db.sql(pending_query, values, as_dict=True)[0].count or 0
		
# 		# Average resolution time (only for resolved tickets)
# 		avg_time_query = f"""
# 			SELECT AVG(DATEDIFF(modified, creation)) as avg_days
# 			FROM `tabTicket Master`
# 			{where_clause}
# 			{'AND' if where_clause else 'WHERE'} workflow_state = 'Resolved'
# 		"""
# 		avg_result = frappe.db.sql(avg_time_query, values, as_dict=True)
# 		avg_time = round(avg_result[0].avg_days, 1) if avg_result and avg_result[0].avg_days else 0
		
# 		# This week's tickets
# 		week_values = values.copy()
# 		week_values["week_start"] = add_days(now_datetime(), -7)
		
# 		week_conditions = where_clause
# 		if where_clause:
# 			week_conditions += " AND creation >= %(week_start)s"
# 		else:
# 			week_conditions = "WHERE creation >= %(week_start)s"
		
# 		week_query = f"""
# 			SELECT COUNT(*) as count
# 			FROM `tabTicket Master`
# 			{week_conditions}
# 		"""
# 		week_count = frappe.db.sql(week_query, week_values, as_dict=True)[0].count or 0
		
# 		return {
# 			"total": total,
# 			"resolved": resolved,
# 			"pending": pending,
# 			"cancelled": cancelled,
# 			"avg_resolution_time": avg_time,
# 			"week_count": week_count,
# 			"resolved_percentage": round((resolved / total * 100), 1) if total > 0 else 0,
# 			"pending_percentage": round((pending / total * 100), 1) if total > 0 else 0,
# 			"cancelled_percentage": round((cancelled / total * 100), 1) if total > 0 else 0
# 		}
# 	except Exception as e:
# 		frappe.log_error(f"Error in get_metrics: {str(e)}")
# 		return {
# 			"total": 0,
# 			"resolved": 0,
# 			"pending": 0,
# 			"cancelled": 0,
# 			"avg_resolution_time": 0,
# 			"week_count": 0,
# 			"resolved_percentage": 0,
# 			"pending_percentage": 0,
# 			"cancelled_percentage": 0
# 		}


# def get_status_distribution(where_clause, values):
# 	"""Get ticket count by workflow state"""
# 	try:
# 		query = f"""
# 			SELECT workflow_state, COUNT(*) as count
# 			FROM `tabTicket Master`
# 			{where_clause}
# 			GROUP BY workflow_state
# 			ORDER BY count DESC
# 		"""
		
# 		data = frappe.db.sql(query, values, as_dict=True)
# 		return {
# 			"labels": [d.workflow_state for d in data],
# 			"data": [d.count for d in data]
# 		}
# 	except Exception as e:
# 		frappe.log_error(f"Error in get_status_distribution: {str(e)}")
# 		return {"labels": [], "data": []}


# def get_issue_type_distribution(where_clause, values):
# 	"""Get ticket count by issue type"""
# 	try:
# 		query = f"""
# 			SELECT issue_type, COUNT(*) as count
# 			FROM `tabTicket Master`
# 			{where_clause}
# 			GROUP BY issue_type
# 			ORDER BY count DESC
# 		"""
		
# 		data = frappe.db.sql(query, values, as_dict=True)
# 		return {
# 			"labels": [d.issue_type or "Not Specified" for d in data],
# 			"data": [d.count for d in data]
# 		}
# 	except Exception as e:
# 		frappe.log_error(f"Error in get_issue_type_distribution: {str(e)}")
# 		return {"labels": [], "data": []}


# def get_priority_distribution(where_clause, values):
# 	"""Get ticket count by priority"""
# 	try:
# 		query = f"""
# 			SELECT priorty, COUNT(*) as count
# 			FROM `tabTicket Master`
# 			{where_clause}
# 			GROUP BY priorty
# 			ORDER BY count DESC
# 		"""
		
# 		data = frappe.db.sql(query, values, as_dict=True)
# 		return {
# 			"labels": [d.priorty or "Not Set" for d in data],
# 			"data": [d.count for d in data]
# 		}
# 	except Exception as e:
# 		frappe.log_error(f"Error in get_priority_distribution: {str(e)}")
# 		return {"labels": [], "data": []}


# def get_state_distribution(where_clause, values):
# 	"""Get ticket count by state"""
# 	try:
# 		query = f"""
# 			SELECT state, COUNT(*) as count
# 			FROM `tabTicket Master`
# 			{where_clause}
# 			GROUP BY state
# 			ORDER BY count DESC
# 			LIMIT 10
# 		"""
		
# 		data = frappe.db.sql(query, values, as_dict=True)
# 		return {
# 			"labels": [d.state or "Not Specified" for d in data],
# 			"data": [d.count for d in data]
# 		}
# 	except Exception as e:
# 		frappe.log_error(f"Error in get_state_distribution: {str(e)}")
# 		return {"labels": [], "data": []}


# def get_timeline_data(where_clause, values):
# 	"""Get tickets created over time (last 4 weeks)"""
# 	try:
# 		query = f"""
# 			SELECT 
# 				DATE(creation) as date,
# 				COUNT(*) as count
# 			FROM `tabTicket Master`
# 			{where_clause}
# 			{'AND' if where_clause else 'WHERE'} creation >= DATE_SUB(NOW(), INTERVAL 28 DAY)
# 			GROUP BY DATE(creation)
# 			ORDER BY date
# 		"""
		
# 		data = frappe.db.sql(query, values, as_dict=True)
		
# 		return {
# 			"labels": [str(d.date) for d in data],
# 			"data": [d.count for d in data]
# 		}
# 	except Exception as e:
# 		frappe.log_error(f"Error in get_timeline_data: {str(e)}")
# 		return {"labels": [], "data": []}


# def get_hospital_data(where_clause, values):
# 	"""Get top hospitals by ticket count"""
# 	try:
# 		query = f"""
# 			SELECT hospital_name, COUNT(*) as count
# 			FROM `tabTicket Master`
# 			{where_clause}
# 			GROUP BY hospital_name
# 			ORDER BY count DESC
# 			LIMIT 10
# 		"""
		
# 		data = frappe.db.sql(query, values, as_dict=True)
# 		return {
# 			"labels": [d.hospital_name or "Not Specified" for d in data],
# 			"data": [d.count for d in data]
# 		}
# 	except Exception as e:
# 		frappe.log_error(f"Error in get_hospital_data: {str(e)}")
# 		return {"labels": [], "data": []}


# def get_robot_data(where_clause, values):
# 	"""Get robots with most issues"""
# 	try:
# 		query = f"""
# 			SELECT robot_serial_no, COUNT(*) as count
# 			FROM `tabTicket Master`
# 			{where_clause}
# 			GROUP BY robot_serial_no
# 			ORDER BY count DESC
# 			LIMIT 10
# 		"""
		
# 		data = frappe.db.sql(query, values, as_dict=True)
# 		return {
# 			"labels": [d.robot_serial_no or "Not Specified" for d in data],
# 			"data": [d.count for d in data]
# 		}
# 	except Exception as e:
# 		frappe.log_error(f"Error in get_robot_data: {str(e)}")
# 		return {"labels": [], "data": []}


# def get_recent_tickets(where_clause, values, limit=20):
# 	"""Get recent tickets for the table"""
# 	try:
# 		query = f"""
# 			SELECT
# 				name,
# 				workflow_state,
# 				robot_serial_no,
# 				ticket_subject,
# 				hospital_name,
# 				issue_type,
# 				state,
# 				priorty,
# 				DATEDIFF(NOW(), creation) as days_open,
# 				creation,
# 				modified
# 			FROM `tabTicket Master`
# 			{where_clause}
# 			ORDER BY creation DESC
# 			LIMIT {limit}
# 		"""
		
# 		tickets = frappe.db.sql(query, values, as_dict=True)
		
# 		# Get engineers from child table for each ticket
# 		for ticket in tickets:
# 			try:
# 				engineers = frappe.db.sql("""
# 					SELECT software_engineer
# 					FROM `tabSoftware Team Members`
# 					WHERE parent = %(parent)s AND software_engineer IS NOT NULL AND software_engineer != ''
# 				""", {"parent": ticket.name}, as_dict=True)
				
# 				ticket.engineers = ", ".join([e.software_engineer for e in engineers]) if engineers else "-"
# 			except:
# 				ticket.engineers = "-"
		
# 		return tickets
# 	except Exception as e:
# 		frappe.log_error(f"Error in get_recent_tickets: {str(e)}")
# 		return []


# @frappe.whitelist()
# def get_filter_options(filter_type, from_date=None, to_date=None):
# 	"""
# 	Get available filter options based on date range
# 	"""
# 	try:
# 		conditions = []
# 		values = {}
		
# 		if from_date:
# 			conditions.append("creation >= %(from_date)s")
# 			values["from_date"] = from_date
		
# 		if to_date:
# 			conditions.append("creation <= %(to_date)s")
# 			values["to_date"] = to_date
		
# 		where_clause = ""
# 		if conditions:
# 			where_clause = "WHERE " + " AND ".join(conditions)
		
# 		if filter_type == "state":
# 			query = f"""
# 				SELECT DISTINCT state
# 				FROM `tabTicket Master`
# 				{where_clause}
# 				ORDER BY state
# 			"""
# 		elif filter_type == "hospital":
# 			query = f"""
# 				SELECT DISTINCT hospital_name
# 				FROM `tabTicket Master`
# 				{where_clause}
# 				ORDER BY hospital_name
# 			"""
# 		elif filter_type == "robot":
# 			query = f"""
# 				SELECT DISTINCT robot_serial_no
# 				FROM `tabTicket Master`
# 				{where_clause}
# 				ORDER BY robot_serial_no
# 			"""
# 		elif filter_type == "status":
# 			query = f"""
# 				SELECT DISTINCT status
# 				FROM `tabTicket Master`
# 				{where_clause}
# 				ORDER BY status
# 			"""
# 		elif filter_type == "priority":
# 			query = f"""
# 				SELECT DISTINCT priorty
# 				FROM `tabTicket Master`
# 				{where_clause}
# 				ORDER BY priorty
# 			"""
# 		elif filter_type == "issue_type":
# 			query = f"""
# 				SELECT DISTINCT issue_type
# 				FROM `tabTicket Master`
# 				{where_clause}
# 				ORDER BY issue_type
# 			"""
# 		else:
# 			return []
		
# 		data = frappe.db.sql(query, values, as_list=True)
# 		return [d[0] for d in data if d[0]]
# 	except Exception as e:
# 		frappe.log_error(f"Error in get_filter_options: {str(e)}")
# 		return []


# @frappe.whitelist()
# def get_ticket_details(ticket_id):
# 	"""
# 	Get detailed information for a specific ticket
# 	"""
# 	try:
# 		ticket = frappe.get_doc("Ticket Master", ticket_id)
# 		return ticket.as_dict()
# 	except Exception as e:
# 		frappe.log_error(f"Error in get_ticket_details: {str(e)}")
# 		return None





# Copyright (c) 2026, Siddhant Hybrowlabs and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import now_datetime, add_days, getdate
import json


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
		conditions.append("status = %(status)s")
		values["status"] = filters["status"]
	
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
		
		data = frappe.db.sql(query, values, as_dict=True)
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


def get_recent_tickets(where_clause, values, limit=100):
	"""Get recent tickets for the table - filtered by date range"""
	try:
		# This will now properly filter by the date range since where_clause includes date filters
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
				modified
			FROM `tabTicket Master`
			{where_clause}
			ORDER BY creation DESC
			LIMIT {limit}
		"""
		
		tickets = frappe.db.sql(query, values, as_dict=True)
		
		# Get engineers from child table for each ticket
		for ticket in tickets:
			try:
				engineers = frappe.db.sql("""
					SELECT software_engineer
					FROM `tabSoftware Team Members`
					WHERE parent = %(parent)s AND software_engineer IS NOT NULL AND software_engineer != ''
				""", {"parent": ticket.name}, as_dict=True)
				
				ticket.engineers = ", ".join([e.software_engineer for e in engineers]) if engineers else "-"
			except:
				ticket.engineers = "-"
		
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
			query = f"""
				SELECT DISTINCT status
				FROM `tabTicket Master`
				{where_clause}
				ORDER BY status
			"""
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