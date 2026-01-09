# import frappe, json

# @frappe.whitelist()
# def set_repoter_for_approval(doc):
#     doc = frappe.get_doc(json.loads(doc))

#     if doc.workflow_state == "Pending From Manager":
#         reports_to = frappe.db.get_value(
#             "Employee",
#             doc.custom_requisitioner,
#             "reports_to"
#         )
#         doc.custom_approval_manager = reports_to

#     elif doc.workflow_state == "Pending From Head":
#         reports_to = frappe.db.get_value(
#             "Employee",
#             doc.custom_approval_manager,
#             "reports_to"
#         )
#         doc.custom_approval_head = reports_to

#     doc.flags.ignore_permissions = True
#     doc.flags.ignore_validate_update_after_submit = True
#     doc.save()




# import frappe
# from frappe import _

# @frappe.whitelist()
# def get_acr_details(acr_name):
#     """Fetch Asset Creation Request details for Material Request"""
    
#     if not frappe.db.exists("Asset Creation Request", acr_name):
#         frappe.throw(_("Asset Creation Request {0} not found").format(acr_name))
    
#     acr = frappe.get_doc("Asset Creation Request", acr_name)
    
#     existing_mr = frappe.db.exists("Material Request", {
#         "custom_asset_creation_request": acr_name,
#         "docstatus": ["!=", 2]
#     })
    
#     if existing_mr:
#         frappe.msgprint(_("Asset Creation Request {0} is already used in Material Request {1}").format(
#             acr_name, existing_mr), alert=True, indicator="orange")
    
#     return {
#         "item": acr.item,
#         "item_name": acr.item_name,
#         "qty": acr.qty,
#         "location": acr.location,
#         "cost_centre": acr.cost_centre,
#         "category_of_asset": acr.category_of_asset,
#         "approx_cost": acr.approx_cost
#     }


# def validate_material_request(doc, method):
#     """Validate Material Request for Asset Purchase Type"""
    
#     if doc.custom_purchase_types == "Asset":
#         # ACR is mandatory
#         if not doc.custom_asset_creation_request:
#             frappe.throw(_("Asset Creation Request is mandatory when Purchase Type is Asset"))
        
#         # Validate ACR exists and is submitted
#         if not frappe.db.exists("Asset Creation Request", doc.custom_asset_creation_request):
#             frappe.throw(_("Invalid Asset Creation Request"))
        
#         acr = frappe.get_doc("Asset Creation Request", doc.custom_asset_creation_request)
        
#         if acr.docstatus != 1:
#             frappe.throw(_("Asset Creation Request must be submitted"))
        
#         # Validate items match ACR
#         if not doc.items:
#             frappe.throw(_("Please add items"))
        
#         for item in doc.items:
#             if item.item_code != acr.item:
#                 frappe.throw(_("Row {0}: Item {1} does not match Asset Creation Request Item {2}").format(
#                     item.idx, item.item_code, acr.item))
            
#             if item.qty != acr.qty:
#                 frappe.msgprint(_("Row {0}: Quantity {1} does not match ACR quantity {2}").format(
#                     item.idx, item.qty, acr.qty), alert=True, indicator="orange")


# def on_submit_material_request(doc, method):
#     """Update Asset Masters after MR submission"""
    
#     if doc.custom_purchase_types == "Asset" and doc.custom_asset_creation_request:
#         # Update Asset Masters with MR reference
#         frappe.db.sql("""
#             UPDATE `tabAsset Master`
#             SET custom_material_request = %s,
#                 custom_mr_date = %s,
#                 custom_mr_status = 'Submitted'
#             WHERE asset_creation_request = %s
#             AND docstatus = 1
#         """, (doc.name, doc.transaction_date, doc.custom_asset_creation_request))
        
#         frappe.db.commit()
        
#         frappe.msgprint(_("Asset Masters updated with Material Request reference"), 
#                        alert=True, indicator="green")


# def on_cancel_material_request(doc, method):
#     """Clear Asset Master references on MR cancellation"""
    
#     if doc.custom_asset_creation_request:
#         frappe.db.sql("""
#             UPDATE `tabAsset Master`
#             SET custom_material_request = NULL,
#                 custom_mr_date = NULL,
#                 custom_mr_status = 'Cancelled'
#             WHERE custom_material_request = %s
#         """, doc.name)
        
#         frappe.db.commit()

import frappe
import json
from frappe import _
from frappe.utils import flt

@frappe.whitelist()
def set_repoter_for_approval(doc):
    doc = frappe.get_doc(json.loads(doc))

    if doc.workflow_state == "Pending From Manager":
        reports_to = frappe.db.get_value(
            "Employee",
            doc.custom_requisitioner,
            "reports_to"
        )
        doc.custom_approval_manager = reports_to

    elif doc.workflow_state == "Pending From Head":
        reports_to = frappe.db.get_value(
            "Employee",
            doc.custom_approval_manager,
            "reports_to"
        )
        doc.custom_approval_head = reports_to

    doc.flags.ignore_permissions = True
    doc.flags.ignore_validate_update_after_submit = True
    doc.save()


@frappe.whitelist()
def get_acr_details(acr_name):
    """Fetch Asset Creation Request details for Material Request"""
    
    if not frappe.db.exists("Asset Creation Request", acr_name):
        frappe.throw(_("Asset Creation Request {0} not found").format(acr_name))
    
    acr = frappe.get_doc("Asset Creation Request", acr_name)
    
    # Check available quantity
    consumed_qty = flt(acr.consumed_qty)
    total_qty = flt(acr.qty)
    available_qty = total_qty - consumed_qty
    
    if available_qty <= 0:
        frappe.throw(_("Asset Creation Request {0} has been fully consumed (Total: {1}, Consumed: {2})").format(
            acr_name, total_qty, consumed_qty))
    
    existing_mr = frappe.db.exists("Material Request", {
        "custom_asset_creation_request": acr_name,
        "docstatus": ["!=", 2]
    })
    
    if existing_mr:
        frappe.msgprint(_("Asset Creation Request {0} is already used in Material Request {1}").format(
            acr_name, existing_mr), alert=True, indicator="orange")
    
    return {
        "item": acr.item,
        "item_name": acr.item_name,
        "qty": available_qty,  # Return available quantity instead of total
        "total_qty": total_qty,
        "consumed_qty": consumed_qty,
        "available_qty": available_qty,
        "location": acr.location,
        "cost_centre": acr.cost_centre,
        "category_of_asset": acr.category_of_asset,
        "approx_cost": acr.approx_cost
    }


def validate_material_request(doc, method):
    """Validate Material Request for Asset Purchase Type"""
    
    if doc.custom_purchase_types == "Asset":
        # ACR is mandatory
        if not doc.custom_asset_creation_request:
            frappe.throw(_("Asset Creation Request is mandatory when Purchase Type is Asset"))
        
        # Validate ACR exists and is submitted
        if not frappe.db.exists("Asset Creation Request", doc.custom_asset_creation_request):
            frappe.throw(_("Invalid Asset Creation Request"))
        
        acr = frappe.get_doc("Asset Creation Request", doc.custom_asset_creation_request)
        
        if acr.docstatus != 1:
            frappe.throw(_("Asset Creation Request must be submitted"))
        
        # Validate items exist
        if not doc.items:
            frappe.throw(_("Please add items"))
        
        # Calculate total quantity in MR
        total_mr_qty = sum(flt(item.qty) for item in doc.items if item.item_code == acr.item)
        
        # Check available quantity
        consumed_qty = flt(acr.consumed_qty)
        total_qty = flt(acr.qty)
        available_qty = total_qty - consumed_qty
        
        # For new documents, check if requested qty is available
        if doc.is_new() or doc.docstatus == 0:
            if total_mr_qty > available_qty:
                frappe.throw(_("""Requested quantity ({0}) exceeds available quantity ({1}) in Asset Creation Request {2}
                    <br><br>Total Qty: {3}
                    <br>Already Consumed: {4}
                    <br>Available: {5}""").format(
                    total_mr_qty, available_qty, doc.custom_asset_creation_request,
                    total_qty, consumed_qty, available_qty
                ))
        
        # Validate items match ACR
        for item in doc.items:
            if item.item_code != acr.item:
                frappe.throw(_("Row {0}: Item {1} does not match Asset Creation Request Item {2}").format(
                    item.idx, item.item_code, acr.item))


def on_submit_material_request(doc, method):
    """Update Asset Masters and ACR consumed quantity after MR submission"""
    
    if doc.custom_purchase_types == "Asset" and doc.custom_asset_creation_request:
        # Update Asset Masters with MR reference
        frappe.db.sql("""
            UPDATE `tabAsset Master`
            SET custom_material_request = %s,
                custom_mr_date = %s,
                custom_mr_status = 'Submitted'
            WHERE asset_creation_request = %s
            AND docstatus = 1
        """, (doc.name, doc.transaction_date, doc.custom_asset_creation_request))
        
        # Update consumed quantity in ACR
        update_acr_consumed_qty(doc.custom_asset_creation_request)
        
        frappe.db.commit()
        
        # Show updated quantity status
        acr = frappe.get_doc("Asset Creation Request", doc.custom_asset_creation_request)
        frappe.msgprint(_("""Material Request submitted successfully!
            <br><br><b>ACR Quantity Status:</b>
            <br>Total Qty: {0}
            <br>Consumed Qty: {1}
            <br>Available Qty: {2}""").format(
            acr.qty, acr.consumed_qty, flt(acr.qty) - flt(acr.consumed_qty)
        ), alert=True, indicator="green")


def on_cancel_material_request(doc, method):
    """Clear Asset Master references and revert consumed quantity on MR cancellation"""
    
    if doc.custom_asset_creation_request:
        frappe.db.sql("""
            UPDATE `tabAsset Master`
            SET custom_material_request = NULL,
                custom_mr_date = NULL,
                custom_mr_status = 'Cancelled'
            WHERE custom_material_request = %s
        """, doc.name)
        
        # Recalculate consumed quantity
        update_acr_consumed_qty(doc.custom_asset_creation_request)
        
        frappe.db.commit()


def update_acr_consumed_qty(acr_name):
    """Calculate and update consumed quantity in ACR based on submitted MRs"""
    
    # Get total quantity from all submitted Material Requests
    mr_qty = frappe.db.sql("""
        SELECT SUM(mri.qty) as total_qty
        FROM `tabMaterial Request Item` mri
        INNER JOIN `tabMaterial Request` mr ON mr.name = mri.parent
        WHERE mr.custom_asset_creation_request = %s
        AND mr.docstatus = 1
    """, acr_name, as_dict=1)
    
    consumed_qty = flt(mr_qty[0].total_qty) if mr_qty and mr_qty[0].total_qty else 0
    
    # Update ACR
    frappe.db.set_value("Asset Creation Request", acr_name, "consumed_qty", consumed_qty, update_modified=False)
    
    return consumed_qty