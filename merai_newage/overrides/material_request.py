
import frappe
from frappe.utils import cint
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
    is_cwip = cint(acr.enable_cwip_accounting)
    print("is_cwip=========",is_cwip)
    if available_qty <= 0 and not is_cwip:
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
        # "item": acr.item,
        # "item_name": acr.item_name,
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
        
        # if acr.docstatus != 1:
        #     frappe.throw(_("Asset Creation Request must be submitted"))
        
        # Validate items exist
        if not doc.items:
            frappe.throw(_("Please add items"))
        
        # Calculate total quantity in MR
        total_mr_qty = sum(flt(item.qty) for item in doc.items)
        
        # Check available quantity
        consumed_qty = flt(acr.consumed_qty)
        total_qty = flt(acr.qty)
        available_qty = total_qty - consumed_qty
        is_cwip = cint(acr.enable_cwip_accounting)
        if not is_cwip:
        # For new documents, check if requested qty is available
            if (doc.is_new() or doc.docstatus == 0) and is_cwip==0:
                if total_mr_qty > available_qty:
                    frappe.throw(_("""Requested quantity ({0}) exceeds available quantity ({1}) in Asset Creation Request {2}
                        <br><br>Total Qty: {3}
                        <br>Already Consumed: {4}
                        <br>Available: {5}""").format(
                        total_mr_qty, available_qty, doc.custom_asset_creation_request,
                        total_qty, consumed_qty, available_qty
                    ))
            
            # Validate items match ACR
            # for item in doc.items:
            #     if item.item_code != acr.item:
            #         frappe.throw(_("Row {0}: Item {1} does not match Asset Creation Request Item {2}").format(
            #             item.idx, item.item_code, acr.item))


def on_submit_material_request(doc, method):
    """Update Asset Masters and ACR consumed quantity after MR submission"""
    if doc.custom_asset_creation_request:
        acr = frappe.get_doc("Asset Creation Request", doc.custom_asset_creation_request)
        if doc.custom_purchase_types == "Asset" and doc.custom_asset_creation_request and acr.enable_cwip_accounting==0:
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
            acr.reload()
            frappe.db.commit()
            
            # Show updated quantity status
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
    print(" flt(mr_qty[0].total_qty)----", flt(mr_qty[0].total_qty))
    consumed_qty = flt(mr_qty[0].total_qty) if mr_qty and mr_qty[0].total_qty else 0
    print("consumed_qty----------",consumed_qty)
    # Update ACR
    frappe.db.set_value("Asset Creation Request", acr_name, "consumed_qty", consumed_qty, update_modified=False)
    
    return consumed_qty


@frappe.whitelist()
def get_warehouse_and_set_in_material_request(work_order_name, name):
    """Get warehouse from Work Order and set in Material Request"""
    
    # Validate inputs
    if not work_order_name or not name:
        frappe.throw(_("Work Order name and Material Request name are required"))
    
    # Check if warehouses are already set
    mr_doc = frappe.get_doc("Material Request", name)
    if mr_doc.set_from_warehouse and mr_doc.set_warehouse:
        return {
            "status": "already_set",
            "set_from_warehouse": mr_doc.set_from_warehouse,
            "set_warehouse": mr_doc.set_warehouse
        }
    
    # Fetch warehouse data from Work Order
    data = frappe.db.sql("""
        SELECT wo.wip_warehouse, woi.source_warehouse 
        FROM `tabWork Order` as wo
        INNER JOIN `tabWork Order Item` as woi ON woi.parent = wo.name
        WHERE wo.name = %s
        LIMIT 1
    """, (work_order_name,), as_dict=True)
    
    if not data:
        frappe.throw(_("No data found for Work Order {0}").format(work_order_name))
    
    wip_warehouse = data[0].get('wip_warehouse')
    source_warehouse = data[0].get('source_warehouse')
    
    # Check if warehouses exist
    if not wip_warehouse or not source_warehouse:
        return {
            "status": "failure",
            "message": "Warehouses not set in Work Order"
        }
    
    # Update the document object directly instead of using frappe.db.set_value
    mr_doc.set_from_warehouse = source_warehouse
    mr_doc.set_warehouse = wip_warehouse
    mr_doc.flags.ignore_permissions = True
    mr_doc.save()
    
    frappe.db.commit()
    
    return {
        "status": "success",
        "set_from_warehouse": source_warehouse,
        "set_warehouse": wip_warehouse
    }

