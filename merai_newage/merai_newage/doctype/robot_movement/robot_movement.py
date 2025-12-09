# Copyright (c) 2025, Siddhant Hybrowlabs and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class RobotMovement(Document):
	pass

@frappe.whitelist()
def get_item_code(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.sql("""
        SELECT DISTINCT item_code
        FROM `tabRobot Tracker`
        WHERE item_code LIKE %s
        LIMIT %s OFFSET %s
    """, ("%" + txt + "%", page_len, start))


@frappe.whitelist()
def get_robot_names(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.sql("""
        SELECT  name
        FROM `tabRobot Tracker`
        WHERE robot_classification LIKE %s
        LIMIT %s OFFSET %s
    """, ("%" + txt + "%", page_len, start))

import frappe, json

@frappe.whitelist()
def get_robot_tracker_data(doc):
    data = frappe._dict(json.loads(doc))

    robot_tracker = frappe.get_doc("Robot Tracker", data.robot_name)

    data.item_code = robot_tracker.item_code
    data.batch = robot_tracker.name

    last_row = robot_tracker.robot_tracker_details[-1]
    data.robot_status = last_row.robot_status
    data.from_location = last_row.location

    return data
