# Copyright (c) 2025, Siddhant Hybrowlabs and contributors
# For license information, please see license.txt

import frappe,json
from frappe.model.document import Document


class Surgery(Document):
    def on_submit(self):
        # Get last max count for this Installed Robot
        last_count = frappe.db.get_value(
            self.doctype,
            {
                "installed_robot": self.installed_robot,
                "docstatus": 1  # only submitted docs
            },
            "MAX(count)"
        ) or 0

        # Increment logic based on surgery type
        if self.surgery_type == "Bilateral":
            self.count = last_count + 2
        else:  # Unilateral
            self.count = last_count + 1

        # Save updated count in DB
        self.db_set("count", self.count)




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

# @frappe.whitelist()
# def total_minutes_for_surgery(doc):
#     data = frappe._dict(json.loads(doc))

#     start = datetime.strptime(data.robot_surgery_start_time, "%H:%M:%S")
#     end = datetime.strptime(data.robot_surgery_end_time, "%H:%M:%S")

#     start_dt = datetime.combine(datetime.today(), start.time())
#     end_dt = datetime.combine(datetime.today(), end.time())

#     if end_dt < start_dt:
#         end_dt += timedelta(days=1)

#     diff_minutes = (end_dt - start_dt).total_seconds() / 60

#     return round(diff_minutes)

@frappe.whitelist()
def total_minutes_for_surgery(doc):
    data = frappe._dict(json.loads(doc))

    def calculate_diff(start_time, end_time):
        if not start_time or not end_time:
            return 0

        start = datetime.strptime(start_time, "%H:%M:%S")
        end = datetime.strptime(end_time, "%H:%M:%S")

        start_seconds = start.hour * 3600 + start.minute * 60 + start.second
        end_seconds = end.hour * 3600 + end.minute * 60 + end.second

        # Handle overnight case
        if end_seconds < start_seconds:
            end_seconds += 24 * 3600

        return (end_seconds - start_seconds) / 60

    diff_minutes = 0

    # First surgery duration
    diff_minutes += calculate_diff(
        data.robot_surgery_start_time,
        data.robot_surgery_end_time
    )

    # Second surgery duration (for bilateral)
    diff_minutes += calculate_diff(
        data.robot_surgery_start_time_2,
        data.robot_surgery_end_time_2
    )

    return round(diff_minutes)
