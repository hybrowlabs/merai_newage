# gate_entry.py

import frappe
from frappe import _
from frappe.utils import flt, cint

def before_save_gate_entry(doc, method):
    """Populate ACR from Purchase Order"""
    
    # Method 1: From Purchase Order items
    for item in doc.gate_entry_details:
        if item.purchase_order:
            po = frappe.get_doc("Purchase Order", item.purchase_order)
            if po.custom_asset_creation_request:
                doc.custom_asset_creation_request = po.custom_asset_creation_request
                frappe.msgprint(_("Asset Creation Request {0} linked from Purchase Order {1}").format(
                    po.custom_asset_creation_request, item.purchase_order
                ), alert=True, indicator="blue")
                break
    
    # Method 2: From Purchase Order reference field (if exists)
    if not doc.custom_asset_creation_request and hasattr(doc, 'purchase_order') and doc.purchase_order:
        po = frappe.get_doc("Purchase Order", doc.purchase_order)
        if po.custom_asset_creation_request:
            doc.custom_asset_creation_request = po.custom_asset_creation_request
            frappe.msgprint(_("Asset Creation Request {0} linked from Purchase Order {1}").format(
                po.custom_asset_creation_request, doc.purchase_order
            ), alert=True, indicator="blue")


def validate_gate_entry(doc, method):
    """Validate Gate Entry for asset items"""
    
    if doc.custom_asset_creation_request:
        acr = frappe.get_doc("Asset Creation Request", doc.custom_asset_creation_request)
        
        # Get asset category to check if CWIP
        asset_category = frappe.get_doc("Asset Category", acr.category_of_asset)
        is_cwip = cint(asset_category.enable_cwip_accounting)
        
        if not is_cwip:
            # For non-CWIP assets, validate quantity
            total_ge_qty = sum(flt(item.qty) for item in doc.gate_entry_details if hasattr(item, 'item_code') and item.item_code == acr.item)
            
            # Get total PO quantity for this ACR
            total_po_qty = 0
            for item in doc.gate_entry_details:
                if item.purchase_order:
                    po = frappe.get_doc("Purchase Order", item.purchase_order)
                    if po.custom_asset_creation_request == doc.custom_asset_creation_request:
                        total_po_qty += sum(flt(po_item.qty) for po_item in po.items)
            
            # Validate GE qty doesn't exceed PO qty
            if total_ge_qty > total_po_qty:
                frappe.throw(_("""Gate Entry quantity ({0}) exceeds Purchase Order quantity ({1}) for Asset Creation Request {2}""").format(
                    total_ge_qty, total_po_qty, doc.custom_asset_creation_request
                ))


def on_submit_gate_entry(doc, method):
    """Update tracking on Gate Entry submission"""
    
    if doc.custom_asset_creation_request:
        acr = frappe.get_doc("Asset Creation Request", doc.custom_asset_creation_request)
        
        # Update Asset Masters with Gate Entry reference
        for item in doc.gate_entry_details:
            if item.purchase_order:
                po = frappe.get_doc("Purchase Order", item.purchase_order)
                if po.custom_asset_creation_request == doc.custom_asset_creation_request:
                    # Update Asset Masters
                    frappe.db.sql("""
                        UPDATE `tabAsset Master`
                        SET gate_entry = %s,
                            gate_entry_date = %s,
                            gate_entry_status = 'Submitted'
                        WHERE custom_purchase_order = %s
                        AND asset_creation_request = %s
                        AND docstatus = 1
                    """, (doc.name, doc.gate_entry_date, item.purchase_order, doc.custom_asset_creation_request))
        
        frappe.db.commit()
        
        frappe.msgprint(_("✅ Gate Entry {0} linked to Asset Creation Request {1}").format(
            doc.name, doc.custom_asset_creation_request
        ), alert=True, indicator="green")


def on_cancel_gate_entry(doc, method):
    """Clear Gate Entry reference from Asset Masters"""
    
    if doc.custom_asset_creation_request:
        frappe.db.sql("""
            UPDATE `tabAsset Master`
            SET custom_gate_entry = NULL,
                custom_gate_entry_date = NULL,
                custom_gate_entry_status = 'Cancelled'
            WHERE custom_gate_entry = %s
        """, doc.name)
        
        frappe.db.commit()
        
        frappe.msgprint(_("Gate Entry reference cleared from Asset Masters"), 
                       alert=True, indicator="orange")