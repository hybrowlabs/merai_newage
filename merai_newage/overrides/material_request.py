import frappe, json

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



# your_app/controllers/material_request.py

import frappe
from frappe import _

@frappe.whitelist()
def get_acr_details(acr_name):
    """Fetch Asset Creation Request details for Material Request"""
    
    if not frappe.db.exists("Asset Creation Request", acr_name):
        frappe.throw(_("Asset Creation Request {0} not found").format(acr_name))
    
    acr = frappe.get_doc("Asset Creation Request", acr_name)
    
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
        "qty": acr.qty,
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
        
        # Validate items match ACR
        if not doc.items:
            frappe.throw(_("Please add items"))
        
        for item in doc.items:
            if item.item_code != acr.item:
                frappe.throw(_("Row {0}: Item {1} does not match Asset Creation Request Item {2}").format(
                    item.idx, item.item_code, acr.item))
            
            if item.qty != acr.qty:
                frappe.msgprint(_("Row {0}: Quantity {1} does not match ACR quantity {2}").format(
                    item.idx, item.qty, acr.qty), alert=True, indicator="orange")


def on_submit_material_request(doc, method):
    """Update Asset Masters after MR submission"""
    
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
        
        frappe.db.commit()
        
        frappe.msgprint(_("Asset Masters updated with Material Request reference"), 
                       alert=True, indicator="green")


def on_cancel_material_request(doc, method):
    """Clear Asset Master references on MR cancellation"""
    
    if doc.custom_asset_creation_request:
        frappe.db.sql("""
            UPDATE `tabAsset Master`
            SET custom_material_request = NULL,
                custom_mr_date = NULL,
                custom_mr_status = 'Cancelled'
            WHERE custom_material_request = %s
        """, doc.name)
        
        frappe.db.commit()