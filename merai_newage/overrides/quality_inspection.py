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



def get_item_month_counter(posting_date):
    month_start = posting_date.replace(day=1)
    month_end = frappe.utils.get_last_day(posting_date)

    result = frappe.db.sql(
        """
        SELECT MAX(item_month_counter)
        FROM `tabAnalytic Number`
        WHERE posting_date BETWEEN %s AND %s
        """,
        (month_start, month_end),
    )

    max_counter = result[0][0] or 0
    return max_counter + 1



import frappe
from frappe.utils import nowdate, getdate

@frappe.whitelist()
def generate_ar_no(reference_name, item_code, qi_docname):
    """
    Creates AR Number records based on Purchase Receipt Item Qty
    """

    if not (reference_name and item_code and qi_docname):
        frappe.throw("Missing required values")

    pr = frappe.get_doc("Purchase Receipt", reference_name)
    qi = frappe.get_doc("Quality Inspection", qi_docname)

    # -----------------------------
    # 1️⃣ Get qty from PR item table
    # -----------------------------
    received_qty = 0
    for item in pr.items:
        if item.item_code == item_code:
            received_qty = int(item.qty or 0)
            break

    if received_qty <= 0:
        frappe.throw(f"No quantity found for Item {item_code} in Purchase Receipt")

    # -----------------------------
    # 2️⃣ Prevent duplicate AR creation
    # -----------------------------
    if frappe.db.exists(
        "Analytic Number",
        {
            "purchase_receipt": reference_name,
            "item_code": item_code
        }
    ):
        frappe.throw("AR Numbers already generated for this Item in this Purchase Receipt")

    posting_date = getdate(qi.report_date or pr.posting_date or nowdate())

    # YY-MM
    yy_mm = posting_date.strftime("%y-%m")

    # -----------------------------
    # 3️⃣ Monthly item counter
    # -----------------------------
    item_counter = get_item_month_counter(posting_date)
    item_counter_str = str(item_counter).zfill(3)

    created_ar_nos = []

    # -----------------------------
    # 4️⃣ Create AR Numbers
    # -----------------------------
    for seq in range(1, received_qty + 1):
        qty_seq = str(seq).zfill(4)

        ar_no = f"QC/RM/{yy_mm}/{item_counter_str} {qty_seq}"
        print(f"Creating AR No:=============127 {ar_no}")
        ar_doc = frappe.new_doc("Analytic Number")
        ar_doc.analytical_no = ar_no
        ar_doc.item_code = item_code
        ar_doc.purchase_receipt = reference_name
        ar_doc.quality_inspection = qi_docname
        ar_doc.item_month_counter = item_counter
        ar_doc.qty_sequence = seq
        ar_doc.posting_date = posting_date
        ar_doc.creation_from = "Purchase Receipt"
        ar_doc.creation_from_no = reference_name
        ar_doc.quality_insepction = qi_docname
        ar_doc.enabled = 1

        ar_doc.insert(ignore_permissions=True)

        created_ar_nos.append(ar_no)

    return created_ar_nos
