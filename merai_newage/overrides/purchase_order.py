# # your_app/controllers/purchase_order.py

# import frappe
# from frappe import _

# def before_save_purchase_order(doc, method):
#     """Populate ACR from Material Request or Supplier Quotation"""
    
#     # Method 1: From Material Request
#     for item in doc.items:
#         if item.material_request:
#             mr = frappe.get_doc("Material Request", item.material_request)
#             if mr.custom_asset_creation_request:
#                 doc.custom_asset_creation_request = mr.custom_asset_creation_request
#                 break
    
#     # Method 2: From Supplier Quotation (if no MR)
#     if not doc.custom_asset_creation_request:
#         for item in doc.items:
#             if item.supplier_quotation:
#                 sq = frappe.get_doc("Supplier Quotation", item.supplier_quotation)
#                 if sq.custom_asset_creation_request:
#                     doc.custom_asset_creation_request = sq.custom_asset_creation_request
#                     break


# def validate_purchase_order(doc, method):
#     """Validate PO for asset items"""
    
#     if doc.custom_asset_creation_request:
#         acr = frappe.get_doc("Asset Creation Request", doc.custom_asset_creation_request)        
#         for item in doc.items:
#             if item.item_code != acr.item:
#                 frappe.throw(_("Row {0}: Item {1} does not match Asset Creation Request Item {2}").format(
#                     item.idx, item.item_code, acr.item))


# def on_submit_purchase_order(doc, method):
#     """Update Asset Masters with PO details"""
    
#     if doc.custom_asset_creation_request:
#         frappe.db.sql("""
#             UPDATE `tabAsset Master`
#             SET custom_purchase_order = %s,
#                 custom_po_date = %s,
#                 custom_supplier = %s,
#                 custom_po_status = 'Submitted'
#             WHERE asset_creation_request = %s
#             AND docstatus = 1
#         """, (doc.name, doc.transaction_date, doc.supplier, doc.custom_asset_creation_request))
        
#         frappe.db.commit()
        
#         frappe.msgprint(_("Asset Masters updated with Purchase Order reference"), 
#                        alert=True, indicator="green")


# def on_cancel_purchase_order(doc, method):
#     """Clear PO reference from Asset Masters"""
    
#     if doc.custom_asset_creation_request:
#         frappe.db.sql("""
#             UPDATE `tabAsset Master`
#             SET custom_purchase_order = NULL,
#                 custom_po_date = NULL,
#                 custom_supplier = NULL,
#                 custom_po_status = 'Cancelled'
#             WHERE custom_purchase_order = %s
#         """, doc.name)
        
#         frappe.db.commit()


import frappe
from frappe import _
from frappe.utils import flt

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
    """Validate PO for asset items and quantity"""
    
    if doc.custom_asset_creation_request:
        acr = frappe.get_doc("Asset Creation Request", doc.custom_asset_creation_request)
        
        # Calculate total PO quantity for ACR item
        total_po_qty = sum(flt(item.qty) for item in doc.items if item.item_code == acr.item)
        
        # Get consumed quantity from ACR
        consumed_qty = flt(acr.consumed_qty)
        total_qty = flt(acr.qty)
        available_qty = total_qty - consumed_qty
        
        # For new PO or draft, validate against available quantity
        if doc.is_new() or doc.docstatus == 0:
            # Check if this PO quantity was already reserved via MR
            mr_reserved_qty = 0
            for item in doc.items:
                if item.material_request:
                    mr = frappe.get_doc("Material Request", item.material_request)
                    if mr.custom_asset_creation_request == doc.custom_asset_creation_request:
                        mr_reserved_qty += flt(item.qty)
            
            # If not from MR, check available quantity
            if mr_reserved_qty == 0 and total_po_qty > available_qty:
                frappe.throw(_("""Purchase Order quantity ({0}) exceeds available quantity ({1}) in Asset Creation Request {2}
                    <br><br>Total Qty: {3}
                    <br>Already Consumed: {4}
                    <br>Available: {5}
                    <br><br>Please create Material Request first to reserve the quantity.""").format(
                    total_po_qty, available_qty, doc.custom_asset_creation_request,
                    total_qty, consumed_qty, available_qty
                ))
        
        # Validate items match ACR
        for item in doc.items:
            if item.item_code != acr.item:
                frappe.throw(_("Row {0}: Item {1} does not match Asset Creation Request Item {2}").format(
                    item.idx, item.item_code, acr.item))


def on_submit_purchase_order(doc, method):
    """Update Asset Masters with PO details"""
    
    if doc.custom_asset_creation_request:
        # Get ACR item to match
        acr = frappe.get_doc("Asset Creation Request", doc.custom_asset_creation_request)
        
        # Calculate total ordered quantity for this ACR
        total_ordered = sum(flt(item.qty) for item in doc.items if item.item_code == acr.item)
        
        # Update Asset Masters (limited to ordered quantity)
        frappe.db.sql("""
            UPDATE `tabAsset Master`
            SET custom_purchase_order = %s,
                custom_po_date = %s,
                custom_supplier = %s,
                custom_po_status = 'Submitted'
            WHERE asset_creation_request = %s
            AND docstatus = 1
            AND (custom_purchase_order IS NULL OR custom_purchase_order = '')
            LIMIT %s
        """, (doc.name, doc.transaction_date, doc.supplier, doc.custom_asset_creation_request, int(total_ordered)))
        
        frappe.db.commit()
        
        frappe.msgprint(_("Asset Masters updated with Purchase Order reference for {0} units").format(total_ordered), 
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