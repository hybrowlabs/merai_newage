

import frappe
from frappe import _
from frappe.utils import flt,cint

def before_save_purchase_order(doc, method):
    """Populate ACR from Material Request or Supplier Quotation"""
    
    for item in doc.items:
        if item.material_request:
            mr = frappe.get_doc("Material Request", item.material_request)
            doc.plant = mr.custom_plant  # Set plant at PO level from MR
            # doc.cost_center = mr.custom_cost_center  
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
        total_po_qty = sum(flt(item.qty) for item in doc.items)
        
        # Get consumed quantity from ACR
        consumed_qty = flt(acr.consumed_qty)
        total_qty = flt(acr.qty)
        available_qty = total_qty - consumed_qty
        is_cwip = cint(acr.enable_cwip_accounting)
        if not is_cwip:

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
            # for item in doc.items:
            #     if item.item_code != acr.item:
            #         frappe.throw(_("Row {0}: Item {1} does not match Asset Creation Request Item {2}").format(
            #             item.idx, item.item_code, acr.item))


def on_submit_purchase_order(doc, method):
    """Update Asset Masters with PO details"""
    is_mail_required = frappe.db.get_single_value("Purchase And Selling Settings", "mail_to_supplier_for_invoice")
    print("is_mail_required========",is_mail_required)
    if is_mail_required:
        send_invoice_form_to_supplier(doc)
    if doc.custom_asset_creation_request:
        # Get ACR item to match
        acr = frappe.get_doc("Asset Creation Request", doc.custom_asset_creation_request)
        
        # Calculate total ordered quantity for this ACR
        total_ordered = sum(flt(item.qty) for item in doc.items)
        print("total-ordered=======",total_ordered)
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


import frappe , json
from frappe.utils import get_url
import hashlib


def get_supplier_email(supplier_name):
    """
    Try multiple sources to get supplier email:
    1. Primary Contact linked to supplier
    2. Address email (like your screenshot shows)
    3. Contact email_ids child table
    """
    
    # Method 1: From Contact linked via Dynamic Link
    contact_email = frappe.db.sql("""
        SELECT cei.email_id 
        FROM `tabContact` c
        JOIN `tabDynamic Link` dl ON dl.parent = c.name
        JOIN `tabContact Email` cei ON cei.parent = c.name
        WHERE dl.link_doctype = 'Supplier' 
          AND dl.link_name = %s
          AND cei.email_id IS NOT NULL
          AND c.status != 'Passive'
        ORDER BY cei.is_primary DESC
        LIMIT 1
    """, supplier_name, as_dict=True)
    
    if contact_email:
        return contact_email[0].email_id
    
    # Method 2: From Address linked to supplier (your case - email in address)
    address_email = frappe.db.sql("""
        SELECT a.email_id
        FROM `tabAddress` a
        JOIN `tabDynamic Link` dl ON dl.parent = a.name
        WHERE dl.link_doctype = 'Supplier'
          AND dl.link_name = %s
          AND a.email_id IS NOT NULL
        ORDER BY a.is_primary_address DESC
        LIMIT 1
    """, supplier_name, as_dict=True)
    
    if address_email:
        return address_email[0].email_id
    
    # Method 3: From tabSupplier direct email fields (custom fields)
    supplier_doc = frappe.get_doc("Supplier", supplier_name)
    for field in ["email", "email_id", "contact_email", "supplier_email"]:
        val = supplier_doc.get(field)
        if val:
            return val
    
    return None


def send_invoice_form_to_supplier(po):
    
    supplier_email = get_supplier_email(po.supplier)
    
    frappe.logger().info(f"Supplier email for {po.supplier}: {supplier_email}")
    
    if not supplier_email:
        frappe.log_error(
            f"No email found for supplier {po.supplier} on PO {po.name}",
            "Supplier Invoice Form Email"
        )
        frappe.msgprint(
            f"⚠️ Could not send invoice form: No email found for supplier {po.supplier_name}. "
            f"Please add an email in the supplier's Contact or Address.",
            alert=True,
            indicator="orange"
        )
        return
    po_items = frappe.get_all(
        "Purchase Order Item",
        filters={"parent": po.name},
        fields=["item_code", "item_name", "description", "qty", "uom", "name"]
    )
    # Build pre-filled web form URL
    base_url = get_url("/supplier-invoice-form/new")
    params = (
        f"?po_number={po.name}"
        f"&vendor_id={po.supplier}"
        f"&vendor_name={po.supplier_name}"
    )
    form_url = base_url + params

    subject = f"Action Required: Upload Invoice for PO {po.name}"

    message = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;padding:24px;
                border:1px solid #e0e0e0;border-radius:8px;">
        <h2 style="color:#333;">Invoice Submission Required</h2>
        <p>Dear <strong>{po.supplier_name}</strong>,</p>
        <p>Your Purchase Order <strong>{po.name}</strong> has been approved. 
        Please upload your invoice using the link below.</p>
        <table style="width:100%;border-collapse:collapse;margin:16px 0;">
            <tr style="background:#f5f5f5;">
                <td style="padding:8px 12px;font-weight:bold;border:1px solid #ddd;">PO Number</td>
                <td style="padding:8px 12px;border:1px solid #ddd;">{po.name}</td>
            </tr>
            <tr>
                <td style="padding:8px 12px;font-weight:bold;border:1px solid #ddd;">PO Date</td>
                <td style="padding:8px 12px;border:1px solid #ddd;">{po.transaction_date}</td>
            </tr>
            <tr style="background:#f5f5f5;">
                <td style="padding:8px 12px;font-weight:bold;border:1px solid #ddd;">Amount</td>
                <td style="padding:8px 12px;border:1px solid #ddd;">{po.grand_total} {po.currency}</td>
            </tr>
            <tr>
                <td style="padding:8px 12px;font-weight:bold;border:1px solid #ddd;">Supplier</td>
                <td style="padding:8px 12px;border:1px solid #ddd;">{po.supplier_name}</td>
            </tr>
        </table>
        <p style="text-align:center;margin:28px 0;">
            <a href="{form_url}" 
               style="background:#1a73e8;color:white;padding:14px 32px;
                      text-decoration:none;border-radius:6px;font-size:16px;
                      font-weight:bold;display:inline-block;">
                📎 Upload Invoice Now
            </a>
        </p>
        <p style="color:#666;font-size:13px;">
            The form is pre-filled with your PO details. 
            Simply attach your invoice PDF and click Save.
        </p>
    </div>
    """

    frappe.sendmail(
        recipients=[supplier_email],
        subject=subject,
        message=message,
        reference_doctype="Purchase Order",
        reference_name=po.name
    )

    frappe.msgprint(
        f"✅ Invoice form link sent to {supplier_email}",
        alert=True,
        indicator="green"
    )


@frappe.whitelist(allow_guest=True)  # allow_guest since supplier is not logged in
def get_po_items(po_number):
    """Fetch PO items for the supplier invoice form"""
    if not po_number:
        return []
    
    # Verify PO exists and is submitted
    if not frappe.db.exists("Purchase Order", po_number):
        frappe.throw("Invalid PO Number")
    
    items = frappe.get_all(
        "Purchase Order Item",
        filters={"parent": po_number},
        fields=["name", "item_code", "item_name", "description", "qty", "uom","rate","amount"],
        order_by="idx asc"
    )
    return items