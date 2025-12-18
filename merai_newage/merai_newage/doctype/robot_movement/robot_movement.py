# # Copyright (c) 2025, Siddhant Hybrowlabs and contributors
# # For license information, please see license.txt

# import frappe
# from frappe.model.document import Document
# from frappe.utils import nowdate


# class RobotMovement(Document):
# 	def on_submit(self):
#           update_robot_tracker(self)
          



# def update_robot_tracker(self):
#         robot_tracker_name = frappe.db.get_value(
#             "Robot Tracker",
#             {
#                 "document_no": self.get("work_order"),
#                 # "batch_number": self.batch_no
#             },
#             "name"
#         )

#         if not robot_tracker_name:
#             frappe.msgprint("Robot Tracker not found for this Work Order & Batch No.")
#             return
        

#         tracker = frappe.get_doc("Robot Tracker", robot_tracker_name)

#         new_row = tracker.append("robot_tracker_details", {})
#         new_row.document_no = self.name
#         new_row.date = nowdate()
#         new_row.location = self.to_location
#         new_row.robot_status = "Transfered"
#         tracker.robot_status = "Transfered"
        

#         tracker.save(ignore_permissions=True)
#         frappe.db.commit()


# @frappe.whitelist()
# def get_item_code(doctype, txt, searchfield, start, page_len, filters):
#     return frappe.db.sql("""
#         SELECT DISTINCT item_code
#         FROM `tabRobot Tracker`
#         WHERE item_code LIKE %s
#         LIMIT %s OFFSET %s
#     """, ("%" + txt + "%", page_len, start))

# @frappe.whitelist()
# def get_robot_names(doctype, txt, searchfield, start, page_len, filters):
#     return frappe.db.sql("""
#         SELECT name, name
#         FROM `tabRobot Tracker`
#         WHERE robot_classification LIKE %s
#         LIMIT %s OFFSET %s
#     """, ("%" + txt + "%", page_len, start))


# import frappe, json

# @frappe.whitelist()
# def get_robot_tracker_data(doc):
#     data = frappe._dict(json.loads(doc))

#     robot_tracker = frappe.get_doc("Robot Tracker", data.robot_name)

#     data.item_code = robot_tracker.item_code
#     data.batch = robot_tracker.name

#     last_row = robot_tracker.robot_tracker_details[-1]
#     data.robot_status = last_row.robot_status
#     data.from_location = last_row.location
#     data.work_order = robot_tracker.work_order

#     return data


# Copyright (c) 2025, Siddhant Hybrowlabs and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import nowdate


class RobotMovement(Document):
     
    def validate(self):
        self.set_print_format_from_item_group()
   
    def set_print_format_from_item_group(self):
        if self.item_group:
            robot_movement__print_format = frappe.db.get_value(
                "Item Group",
                self.item_group,
                "custom_robot_movement_print_format"
            )

            if robot_movement__print_format:
                self.custom_print_format = robot_movement__print_format
            else:
                self.custom_print_format = None     

    def on_submit(self):
          update_robot_tracker(self)
          



def update_robot_tracker(self):
    robot_tracker_name = frappe.db.get_value(
        "Robot Tracker",
        {
            "document_no": self.get("work_order"),
            # "batch_number": self.batch_no
        },
        "name"
    )

    if not robot_tracker_name:
        frappe.msgprint("Robot Tracker not found for this Work Order & Batch No.")
        return

    tracker = frappe.get_doc("Robot Tracker", robot_tracker_name)

    new_row = tracker.append("robot_tracker_details", {})
    new_row.document_no = self.name
    new_row.date = nowdate()
    new_row.location = self.to_location
    new_row.robot_status = "Transfered"
    new_row.doctype_name="Robot Movement"
    tracker.robot_status = "Transfered"

    tracker.save(ignore_permissions=True)
    frappe.db.commit()


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
    robot_classification = filters.get("robot_classification")
    
    conditions = "WHERE name LIKE %s"
    values = ["%" + txt + "%"]
    
    if robot_classification:
        conditions += " AND robot_classification = %s"
        values.append(robot_classification)
    
    values.extend([page_len, start])
    
    return frappe.db.sql(f"""
        SELECT name, robot_classification
        FROM `tabRobot Tracker`
        {conditions}
        LIMIT %s OFFSET %s
    """, tuple(values))


@frappe.whitelist()
def get_robot_tracker_data(doc):
    data = frappe._dict(frappe.parse_json(doc))

    robot_tracker = frappe.get_doc("Robot Tracker", data.robot_name)

    data.item_code = robot_tracker.item_code
    data.batch = robot_tracker.name

    if robot_tracker.robot_tracker_details:
        last_row = robot_tracker.robot_tracker_details[-1]
        data.robot_status = last_row.robot_status
        data.from_location = last_row.location
    
    data.work_order = robot_tracker.work_order

    return data