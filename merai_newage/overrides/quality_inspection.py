

import frappe
from frappe.utils import nowdate, getdate

@frappe.whitelist()
def generate_ar_no(reference_name, item_code, qi_docname):
    """
    Creates AR Number records and updates child table in Quality Inspection
    """
    if not (reference_name and item_code and qi_docname):
        frappe.throw("Missing required values")
    custom_generate_ar_no = frappe.db.get_value("Item", item_code, "custom_generate_ar_no")
    if not custom_generate_ar_no:
        frappe.msgprint(f"Item {item_code} is not configured for AR generation")
    pr = frappe.get_doc("Purchase Receipt", reference_name)
    qi = frappe.get_doc("Quality Inspection", qi_docname)

    # 1. Get qty from PR item table
    received_qty = 0
    for item in pr.items:
        if item.item_code == item_code:
            received_qty = int(item.qty or 0)
            break

    if received_qty <= 0:
        frappe.throw(f"No quantity found for Item {item_code} in Purchase Receipt")

    # 2. Prevent duplicate AR creation
    if frappe.db.exists("Analytic Number", {
        "purchase_receipt": reference_name,
        "item_code": item_code
    }):
        frappe.throw("AR Numbers already generated for this Item in this Purchase Receipt")

    posting_date = getdate(qi.report_date or pr.posting_date or nowdate())
    yy_mm = posting_date.strftime("%y-%m")

    # 3. Monthly item counter
    item_counter = get_item_month_counter(posting_date)
    item_counter_str = str(item_counter).zfill(3)

    created_ar_nos = []

    # 4. Create AR Numbers and update child table directly via DB
    for seq in range(1, received_qty + 1):
        qty_seq = str(seq).zfill(4)
        ar_no = f"QC/RM/{yy_mm}/{item_counter_str} {qty_seq}"

        # Insert Analytic Number doc
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
        ar_doc.quality_insepction = qi_docname  # keep existing field name (typo in schema)
        ar_doc.enabled = 1
        ar_doc.insert(ignore_permissions=True)

        created_ar_nos.append(ar_no)
    print(f"Created AR Nos: {created_ar_nos}")
    # 5. Update child table in QI directly using db.sql for performance
    # First clear existing rows for this QI
    frappe.db.delete("Analytic No Details",  # replace with your actual child doctype name
        {"parent": qi_docname, "parentfield": "custom_analytic_no_details"})

    # Bulk insert child rows
    for idx, ar_no in enumerate(created_ar_nos, start=1):
        frappe.db.sql("""
            INSERT INTO `tabAnalytic No Details`
            (name, creation, modified, modified_by, owner, docstatus,
             parent, parentfield, parenttype, idx, ar_no)
            VALUES (%s, NOW(), NOW(), %s, %s, 0, %s, %s, %s, %s, %s)
        """, (
            frappe.generate_hash(length=10),
            frappe.session.user,
            frappe.session.user,
            qi_docname,
            "custom_analytic_no_details",
            "Quality Inspection",
            idx,
            ar_no
        ))

    frappe.db.commit()

    return {"count": len(created_ar_nos), "message": f"{len(created_ar_nos)} AR Numbers generated successfully"}


def get_item_month_counter(posting_date):
    month_start = posting_date.replace(day=1)
    month_end = frappe.utils.get_last_day(posting_date)

    result = frappe.db.sql("""
        SELECT MAX(item_month_counter)
        FROM `tabAnalytic Number`
        WHERE posting_date BETWEEN %s AND %s
    """, (month_start, month_end))

    max_counter = result[0][0] or 0
    return max_counter + 1


def before_save(doc, method=None):
    employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
    if employee:
        doc.custom_inspection_done_by = employee
        doc.custom_inspection_date = nowdate()


def on_submit(doc, method=None):
    employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
    if employee:
        doc.custom_verification_done_by = employee
        doc.custom_verification_date = nowdate()
        doc.db_update()
    else:
        frappe.msgprint("No Employee mapped to the current user; verification fields left blank.")