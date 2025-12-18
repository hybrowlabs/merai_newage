# Copyright (c) 2025, Siddhant Hybrowlabs and contributors
# For license information, please see license.txt

import frappe,json
from frappe.model.document import Document


class Surgery(Document):
	pass



@frappe.whitelist()
def get_robot_tracker_data(doc):
    data = frappe._dict(json.loads(doc))

    robot_tracker = frappe.get_doc("Robot Tracker", data.installed_robot)

    data.item_code = robot_tracker.item_code
    data.batch = robot_tracker.name

    last_row = robot_tracker.robot_tracker_details[-1]
    data.robot_status = last_row.robot_status
    data.from_location = last_row.location
    data.work_order = robot_tracker.work_order

    return data

from datetime import datetime
import frappe, json
from datetime import datetime, timedelta

@frappe.whitelist()
def total_minutes_for_surgery(doc):
    data = frappe._dict(json.loads(doc))

    start = datetime.strptime(data.robot_surgery_start_time, "%H:%M:%S")
    end = datetime.strptime(data.robot_surgery_end_time, "%H:%M:%S")

    start_dt = datetime.combine(datetime.today(), start.time())
    end_dt = datetime.combine(datetime.today(), end.time())

    if end_dt < start_dt:
        end_dt += timedelta(days=1)

    diff_minutes = (end_dt - start_dt).total_seconds() / 60

    return round(diff_minutes)
