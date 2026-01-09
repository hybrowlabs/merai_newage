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
    new_brc.robot_serial_no = frappe.db.get_value("Robot Tracker",{"work_order":work_order},"name")

    item_doc = frappe.get_doc("Item", item_code)
    item_group = frappe.db.get_value("Item",item_code,"item_group")
    template_name = frappe.db.get_value(
            "Item Group",
            item_group,
            "custom_installtion_procedure__verification_template"
        )
    template_doc = frappe.get_doc(
            "Installation Procedure And Verification Template",
            template_name
        )
    print("template_doc-----------",template_doc)
    for row in template_doc.brc_check_deatils:
            
            new_brc.append("batch_release_certificate_details", {
                "test_description": row.check_name
            })

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


@frappe.whitelist()
def fetch_brc_details(work_order):

    wo_doc = frappe.get_doc("Work Order", work_order)    
    item_code = wo_doc.production_item 

    item_doc = frappe.get_doc("Item", item_code)
    item_group = frappe.db.get_value("Item", item_code, "item_group")

    template_name = frappe.db.get_value(
        "Item Group",
        item_group,
        "custom_installtion_procedure__verification_template"
    )

    response = {
        "child_items": [],          
        "verification_items": []    
    }

    if template_name:
        template_doc = frappe.get_doc(
            "Installation Procedure And Verification Template",
            template_name
        )

        for row in template_doc.brc_check_deatils:
            response["verification_items"].append({
                "test_description": row.check_name
            })

    if hasattr(item_doc, 'custom_dispatch_checklist_details'):
        for row in item_doc.custom_dispatch_checklist_details:
            response["child_items"].append({
                "part_no": row.product_name,
                "std_qty": row.qty,
                "description": row.product_description
            })

    return response



# @frappe.whitelist()
# def create_dispatch(doc):
#     doc = frappe.parse_json(doc)

#     new_dispatch = frappe.new_doc("Dispatch")
#     new_dispatch.robot_classification = doc.get("robot_classifcation")
#     new_dispatch.item_code = doc.get("item_code")
#     new_dispatch.dispatch_no = doc.get("name")
#     new_dispatch.hospital_name = doc.get("hospital_name")
#     new_dispatch.work_order = doc.get("work_order")
#     new_dispatch.hospital_address = frappe.db.get_value("Account Master",doc.hospital_name,"address")
#     new_dispatch.city = frappe.db.get_value("Account Master",doc.hospital_name,"city")
#     new_dispatch.state = frappe.db.get_value("Account Master",doc.hospital_name,"state")

#     new_assign_installation.insert(ignore_permissions=True)  # Save the doc

#     return new_assign_installation.name
