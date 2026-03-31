import frappe
from frappe.utils import now_datetime, get_datetime


def get_remaining_time(deadline):
    if not deadline:
        return ""

    deadline = get_datetime(deadline)
    now = now_datetime()

    diff_seconds = int((deadline - now).total_seconds())

    if diff_seconds <= 0: 
        return "Expired"

    minutes = diff_seconds // 60
    hours = minutes // 60
    days = hours // 24

    if days > 0:
        return f"{days}d {hours % 24}h left"
    elif hours > 0:
        return f"{hours}h {minutes % 60}m left"
    elif minutes > 0:
        return f"{minutes}m left"
    else:
        return f"{diff_seconds}s left"


def update_single_rfq_expiry(doc):
    if doc.docstatus != 1:
        doc.custom_current_status = ""
        doc.custom_remaining_time = ""
        return

    deadline = doc.get("custom_quotation_deadline1")

    if not deadline:
        return

    deadline = get_datetime(deadline)
    now = now_datetime()

    if deadline <= now:
        doc.custom_current_status = "Expired"
        doc.custom_remaining_time = "Expired"
    else:
        doc.custom_current_status = "Active"
        doc.custom_remaining_time = get_remaining_time(deadline)


def update_all_rfq_expiry_status():
    rfqs = frappe.get_all(
        "Request for Quotation",
        filters={"custom_quotation_deadline1": ["is", "set"]},
        fields=["name"]
    )

    now = now_datetime()

    for rfq in rfqs:
        try:
            doc = frappe.get_doc("Request for Quotation", rfq.name)
            deadline = get_datetime(doc.custom_quotation_deadline1)

            # Draft ignore
            if doc.docstatus != 1:
                frappe.db.set_value(doc.doctype, doc.name, {
                    "custom_current_status": "",
                    "custom_remaining_time": ""
                })
                continue

            # Submitted case
            if deadline <= now:
                status = "Expired"
                remaining = "Expired"
            else:
                status = "Active"
                remaining = get_remaining_time(deadline)

            frappe.db.set_value(doc.doctype, doc.name, {
                "custom_current_status": status,
                "custom_remaining_time": remaining
            })

        except Exception as e:
            frappe.log_error(str(e), "RFQ Expiry Error")
            
            
@frappe.whitelist()
def update_rfq_status(name):
    doc = frappe.get_doc("Request for Quotation", name)

    update_single_rfq_expiry(doc)

    doc.save(ignore_permissions=True)

    return True