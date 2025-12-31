# Copyright (c) 2025, Siddhant Hybrowlabs and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from frappe.utils import get_link_to_form

class BatchReleaseCertificate(Document):
    pass


import frappe

@frappe.whitelist()
def create_brc(work_order):
    # Get Work Order doc properly
    doc = frappe.get_doc("Work Order", work_order)
    brc_exists_name = frappe.db.get_value(
        "Batch Release Certificate",
        {"work_order": work_order},
        "name"
    )

    if brc_exists_name:
        link = get_link_to_form(
            "Batch Release Certificate",
            brc_exists_name
        )
        frappe.throw(
            f"Batch Release Certificate already exists: {link} "
            f"for Work Order {work_order}"
        )
    item_code = doc.production_item

    new_brc = frappe.new_doc("Batch Release Certificate")
    new_brc.product_name = item_code
    new_brc.brand_name = frappe.db.get_value("Item", item_code, "brand")
    new_brc.product_description = frappe.db.get_value(
        "Item", item_code, "description"
    )
    new_brc.work_order = doc.name
    new_brc.batch = frappe.db.get_value("Batch",{"custom_batch_number":doc.custom_batch_number},"name")
    new_brc.batch_qty = doc.qty
    new_brc.manufacturing_date = doc.planned_start_date
    new_brc.work_order = work_order

    item_doc = frappe.get_doc("Item", item_code)

    for row in item_doc.custom_dispatch_checklist_details:
        new_brc.append(
            "batch_release_certificate_item_details",
            {
                "part_no": row.product_name,
                "std_qty": row.qty,
                "description": row.product_description,
            }
        )

    new_brc.insert(ignore_permissions=True)

    return new_brc.name
