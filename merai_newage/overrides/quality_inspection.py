# import frappe
# from erpnext.manufacturing.doctype.job_card.job_card import JobCard
# import json
# from frappe.query_builder import Criterion
# from frappe.utils import nowdate, add_to_date, get_datetime


# @frappe.whitelist()
# def on_submit(self,method=None):
#     employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
#     self.custom_verification_done_by = employee
#     self.custom_verification_date = frappe.utils.nowdate()
   
# @frappe.whitelist()
# def get_employee_by_user():
#     print("frappe.session.uer------12000000---",frappe.session.user)
#     employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
#     print("employe----------",employee)
#     return employee   

# import frappe
# from frappe.utils import nowdate

# def before_submit(doc, method=None):
#     employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
#     if employee:
#         doc.custom_verification_done_by = employee
#         doc.custom_verification_date = nowdate()
#     else:
#         # optional: block submit or just note it
#         frappe.msgprint("No Employee mapped to the current user; verification fields left blank.")

import frappe
from frappe.utils import nowdate

def before_save(doc, method=None):
    """Executed before document save"""
    employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
    frappe.logger().info(f"Employee found from server side: {employee}")
    if employee:
        doc.custom_inspection_done_by = employee
        doc.custom_inspection_date = nowdate()

def on_submit(doc, method=None):
    """Executed when document is submitted"""
    employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
    if employee:
        doc.custom_verification_done_by = employee
        doc.custom_verification_date = nowdate()
        doc.db_update()  # <-- important: persist changes made after submit
    else:
        frappe.msgprint("No Employee mapped to the current user; verification fields left blank.")
