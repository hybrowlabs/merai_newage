# your_app/controllers/purchase_order.py

import frappe
from frappe import _

def before_save_purchase_order(doc, method):
    """Populate ACR from Material Request or Supplier Quotation"""
    
    # Method 1: From Material Request
    for item in doc.items:
        if item.material_request:
            mr = frappe.get_doc("Material Request", item.material_request)
            if mr.custom_asset_creation_request:
                doc.custom_asset_creation_request = mr.custom_asset_creation_request
                break
    
    # Method 2: From Supplier Quotation (if no MR)
    if not doc.custom_asset_creation_request:
        for item in doc.items:
            if item.supplier_quotation:
                sq = frappe.get_doc("Supplier Quotation", item.supplier_quotation)
                if sq.custom_asset_creation_request:
                    doc.custom_asset_creation_request = sq.custom_asset_creation_request
                    break


def validate_purchase_order(doc, method):
    """Validate PO for asset items"""
    
    if doc.custom_asset_creation_request:
        acr = frappe.get_doc("Asset Creation Request", doc.custom_asset_creation_request)        
        for item in doc.items:
            if item.item_code != acr.item:
                frappe.throw(_("Row {0}: Item {1} does not match Asset Creation Request Item {2}").format(
                    item.idx, item.item_code, acr.item))


def on_submit_purchase_order(doc, method):
    """Update Asset Masters with PO details"""
    
    if doc.custom_asset_creation_request:
        frappe.db.sql("""
            UPDATE `tabAsset Master`
            SET custom_purchase_order = %s,
                custom_po_date = %s,
                custom_supplier = %s,
                custom_po_status = 'Submitted'
            WHERE asset_creation_request = %s
            AND docstatus = 1
        """, (doc.name, doc.transaction_date, doc.supplier, doc.custom_asset_creation_request))
        
        frappe.db.commit()
        
        frappe.msgprint(_("Asset Masters updated with Purchase Order reference"), 
                       alert=True, indicator="green")


def on_cancel_purchase_order(doc, method):
    """Clear PO reference from Asset Masters"""
    
    if doc.custom_asset_creation_request:
        frappe.db.sql("""
            UPDATE `tabAsset Master`
            SET custom_purchase_order = NULL,
                custom_po_date = NULL,
                custom_supplier = NULL,
                custom_po_status = 'Cancelled'
            WHERE custom_purchase_order = %s
        """, doc.name)
        
        frappe.db.commit()