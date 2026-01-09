# # your_app/controllers/purchase_receipt.py

# import frappe
# from frappe import _
# from frappe.utils import nowdate, flt, cint

# def before_save_purchase_receipt(doc, method):
#     """Populate ACR from Purchase Order"""
    
#     for item in doc.items:
#         if item.purchase_order:
#             po = frappe.get_doc("Purchase Order", item.purchase_order)
#             if po.custom_asset_creation_request:
#                 doc.custom_asset_creation_request = po.custom_asset_creation_request
#                 break


# def validate_purchase_receipt(doc, method):
#     """Validate PR for asset items"""
    
#     if doc.custom_asset_creation_request:
#         acr = frappe.get_doc("Asset Creation Request", doc.custom_asset_creation_request)
        
#         # Validate items match ACR
#         for item in doc.items:
#             if item.item_code != acr.item:
#                 frappe.throw(_("Row {0}: Item {1} does not match Asset Creation Request Item {2}").format(
#                     item.idx, item.item_code, acr.item))


# def on_submit_purchase_receipt(doc, method):
#     """
#     🎯 MAIN LOGIC: Create Assets from Asset Masters
#     """
    
#     if doc.custom_asset_creation_request:
#         create_assets_from_asset_masters(doc)


# def create_assets_from_asset_masters(pr_doc):
#     """
#     Create Asset documents from Asset Master based on Purchase Receipt
    
#     Logic:
#     1. Get ACR reference from PR
#     2. Find all Asset Masters linked to ACR (not yet converted)
#     3. Loop through Asset Masters
#     4. Create Asset for each Asset Master
#     5. Add purchase details from PR
#     """
    
#     acr_name = pr_doc.custom_asset_creation_request
    
#     # Get Asset Creation Request
#     acr = frappe.get_doc("Asset Creation Request", acr_name)
    
#     # Get all Asset Masters that need conversion
#     asset_masters = frappe.get_all("Asset Master",
#         filters={
#             "asset_creation_request": acr_name,
#             "docstatus": 1,
#             "custom_asset_created": 0 
#         },
#         fields=["name", "item", "item_name", "asset_category", "company", 
#                 "location", "cost_center", "custodian", "department", "plant"],
#         order_by="creation asc"
#     )
#     print("asset_masters--------",asset_masters)
#     if not asset_masters:
#         frappe.msgprint(_("No pending Asset Masters found for Asset Creation Request {0}").format(acr_name),
#                        alert=True, indicator="orange")
#         return []
    
#     # Get purchase item from PR
#     pr_item = None
#     for item in pr_doc.items:
#         if item.item_code == acr.item:
#             pr_item = item
#             break
    
#     if not pr_item:
#         frappe.throw(_("No matching item found in Purchase Receipt for Asset Creation Request"))
    
#     # Calculate cost per asset
#     total_assets = len(asset_masters)
#     cost_per_asset = flt(pr_item.amount) / total_assets if total_assets > 0 else 0
    
#     created_assets = []
#     errors = []
    
#     # 🔄 Loop through each Asset Master and create Asset
#     for idx, am in enumerate(asset_masters, 1):
#         try:
#             # Create Asset document
#             asset_doc = frappe.get_doc({
#                 "doctype": "Asset",
#                 "asset_name": f"{am.item_name}-{am.name}",
#                 "item_code": am.item,
#                 "asset_category": am.asset_category,
#                 "company": am.company,
                
#                 # Location & Department
#                 "location": am.location,
#                 "cost_center": am.cost_center,
#                 "custodian": am.custodian,
#                 "department": am.department,
                
#                 # Purchase details from PR
#                 "purchase_date": pr_doc.posting_date,
#                 "available_for_use_date": pr_doc.posting_date,
#                 "gross_purchase_amount": cost_per_asset,
#                 "purchase_receipt": pr_doc.name,
#                 "purchase_receipt_amount": cost_per_asset,
#                 "supplier": pr_doc.supplier,
                
#                 # Reference fields
#                 "custom_asset_creation_request": acr_name,
#                 "custom_asset_master": am.name,
#                 "custom_material_request": pr_item.material_request,
#                 "custom_purchase_order": pr_item.purchase_order,
                
#                 # Status
#                 "is_existing_asset": 0,
#                 "calculate_depreciation": 0,
#             })
            
#             # Insert asset
#             asset_doc.flags.ignore_validate = False
#             asset_doc.insert(ignore_permissions=True)

#             # ✅ FIX: Proper submission
#             asset_doc.docstatus = 1
#             asset_doc.status = "Submitted"
#             asset_doc.submit()
            
#             created_assets.append(asset_doc.name)
            
#             # Update Asset Master
#             frappe.db.set_value("Asset Master", am.name, {
#                 "custom_asset_created": 1,
#                 "custom_asset_number": asset_doc.name,
#                 "custom_purchase_receipt": pr_doc.name,
#                 "custom_pr_date": pr_doc.posting_date,
#                 "status": "Active"
#             }, update_modified=False)
            
#             frappe.msgprint(_("✅ Created Asset: {0} from Asset Master: {1}").format(
#                 asset_doc.name, am.name), alert=True, indicator="green")
            
#         except Exception as e:
#             error_msg = _("❌ Error creating asset from Asset Master {0}: {1}").format(am.name, str(e))
#             errors.append(error_msg)
#             frappe.log_error(message=str(e), title=f"Asset Creation Error - {am.name}")
#             frappe.msgprint(error_msg, alert=True, indicator="red")
    
#     # Update Asset Creation Request
#     if created_assets:
#         frappe.db.set_value("Asset Creation Request", acr_name, {
#             "custom_assets_created": 1,
#             "custom_asset_creation_status": "Completed",
#             "custom_assets_count": len(created_assets)
#         }, update_modified=False)
    
#     frappe.db.commit()
    
#     # Final summary message
#     if created_assets:
#         frappe.msgprint(
#             _("""<div style='font-size: 14px;'>
#                 <b>🎉 Asset Creation Successful!</b><br><br>
#                 <b>Created {0} Asset(s):</b><br>
#                 {1}
#                 </div>""").format(
#                 len(created_assets),
#                 "<br>".join([f"• {asset}" for asset in created_assets])
#             ),
#             title=_("Assets Created"),
#             indicator="green"
#         )
    
#     if errors:
#         frappe.msgprint(
#             _("<b>⚠️ Some errors occurred:</b><br>{0}").format("<br>".join(errors)),
#             title=_("Errors"),
#             indicator="orange"
#         )
    
#     return created_assets


# def on_cancel_purchase_receipt(doc, method):
#     """Cancel linked Assets when PR is cancelled"""
    
#     if doc.custom_asset_creation_request:
#         # Find and cancel assets created from this PR
#         assets = frappe.get_all("Asset",
#             filters={
#                 "purchase_receipt": doc.name,
#                 "custom_asset_creation_request": doc.custom_asset_creation_request,
#                 "docstatus": 1
#             },
#             pluck="name"
#         )
        
#         cancelled_assets = []
#         for asset_name in assets:
#             try:
#                 asset = frappe.get_doc("Asset", asset_name)
#                 asset.cancel()
#                 cancelled_assets.append(asset_name)
#             except Exception as e:
#                 frappe.log_error(f"Error cancelling asset {asset_name}: {str(e)}")
        
#         if cancelled_assets:
#             frappe.msgprint(_("Cancelled {0} Asset(s): {1}").format(
#                 len(cancelled_assets), ", ".join(cancelled_assets)),
#                 alert=True, indicator="orange")
        
#         # Reset Asset Masters
#         frappe.db.sql("""
#             UPDATE `tabAsset Master`
#             SET custom_asset_created = 0,
#                 custom_asset_number = NULL,
#                 custom_purchase_receipt = NULL,
#                 custom_pr_date = NULL
#             WHERE custom_purchase_receipt = %s
#         """, doc.name)
        
#         # Reset ACR status
#         # frappe.db.set_value("Asset Creation Request", doc.custom_asset_creation_request, {
#         #     "custom_assets_created": 0,
#         #     "custom_asset_creation_status": "Pending"
#         # })
        
#         frappe.db.commit()


import frappe
from frappe import _
from frappe.utils import nowdate, flt, cint

def before_save_purchase_receipt(doc, method):
    """Populate ACR from Purchase Order"""
    
    for item in doc.items:
        if item.purchase_order:
            po = frappe.get_doc("Purchase Order", item.purchase_order)
            if po.custom_asset_creation_request:
                doc.custom_asset_creation_request = po.custom_asset_creation_request
                break


def validate_purchase_receipt(doc, method):
    """Validate PR for asset items and quantity"""
    
    if doc.custom_asset_creation_request:
        acr = frappe.get_doc("Asset Creation Request", doc.custom_asset_creation_request)
        
        # Calculate total PR quantity
        total_pr_qty = sum(flt(item.qty) for item in doc.items if item.item_code == acr.item)
        
        # Get total PO quantity for this ACR
        total_po_qty = 0
        for item in doc.items:
            if item.purchase_order:
                po = frappe.get_doc("Purchase Order", item.purchase_order)
                if po.custom_asset_creation_request == doc.custom_asset_creation_request:
                    total_po_qty += sum(flt(po_item.qty) for po_item in po.items if po_item.item_code == acr.item)
        
        # Validate PR qty doesn't exceed PO qty
        if total_pr_qty > total_po_qty:
            frappe.throw(_("""Purchase Receipt quantity ({0}) exceeds Purchase Order quantity ({1}) for Asset Creation Request {2}""").format(
                total_pr_qty, total_po_qty, doc.custom_asset_creation_request
            ))
        
        # Validate items match ACR
        for item in doc.items:
            if item.item_code != acr.item:
                frappe.throw(_("Row {0}: Item {1} does not match Asset Creation Request Item {2}").format(
                    item.idx, item.item_code, acr.item))


def on_submit_purchase_receipt(doc, method):
    """Create Assets from Asset Masters"""
    
    if doc.custom_asset_creation_request:
        create_assets_from_asset_masters(doc)


def create_assets_from_asset_masters(pr_doc):
    """
    Create Asset documents from Asset Master based on Purchase Receipt
    
    Logic:
    1. Get ACR reference from PR
    2. Find Asset Masters linked to ACR (not yet converted, with this PO)
    3. Create Assets based on received quantity
    4. Update Asset Masters
    """
    
    acr_name = pr_doc.custom_asset_creation_request
    
    # Get Asset Creation Request
    acr = frappe.get_doc("Asset Creation Request", acr_name)
    
    # Get PO from PR items
    po_name = None
    for item in pr_doc.items:
        if item.purchase_order:
            po_name = item.purchase_order
            break
    
    # Calculate received quantity
    total_received = sum(flt(item.qty) for item in pr_doc.items if item.item_code == acr.item)
    
    # Get Asset Masters that need conversion (linked to this PO)
    filters = {
        "asset_creation_request": acr_name,
        "docstatus": 1,
        "custom_asset_created": 0
    }
    
    if po_name:
        filters["custom_purchase_order"] = po_name
    
    asset_masters = frappe.get_all("Asset Master",
        filters=filters,
        fields=["name", "item", "item_name", "asset_category", "company", 
                "location", "cost_center", "custodian", "department", "plant"],
        order_by="creation asc",
        limit=int(total_received)  # Only get as many as received
    )
    
    print("asset_masters--------", asset_masters)
    
    if not asset_masters:
        frappe.msgprint(_("No pending Asset Masters found for Asset Creation Request {0} with PO {1}").format(
            acr_name, po_name or "N/A"), alert=True, indicator="orange")
        return []
    
    if len(asset_masters) < total_received:
        frappe.msgprint(_("""Warning: Received quantity ({0}) is more than available Asset Masters ({1}).
            <br>Only {2} assets will be created.""").format(
            total_received, len(asset_masters), len(asset_masters)
        ), alert=True, indicator="orange")
    
    # Get purchase item from PR
    pr_item = None
    for item in pr_doc.items:
        if item.item_code == acr.item:
            pr_item = item
            break
    
    if not pr_item:
        frappe.throw(_("No matching item found in Purchase Receipt for Asset Creation Request"))
    
    # Calculate cost per asset
    total_assets = len(asset_masters)
    cost_per_asset = flt(pr_item.amount) / total_assets if total_assets > 0 else 0
    
    created_assets = []
    errors = []
    
    # Loop through each Asset Master and create Asset
    for idx, am in enumerate(asset_masters, 1):
        try:
            # Create Asset document
            asset_doc = frappe.get_doc({
                "doctype": "Asset",
                "asset_name": f"{am.item_name}-{am.name}",
                "item_code": am.item,
                "asset_category": am.asset_category,
                "company": am.company,
                
                # Location & Department
                "location": am.location,
                "cost_center": am.cost_center,
                "custodian": am.custodian,
                "department": am.department,
                
                # Purchase details from PR
                "purchase_date": pr_doc.posting_date,
                "available_for_use_date": pr_doc.posting_date,
                "gross_purchase_amount": cost_per_asset,
                "purchase_receipt": pr_doc.name,
                "purchase_receipt_amount": cost_per_asset,
                "supplier": pr_doc.supplier,
                
                # Reference fields
                "custom_asset_creation_request": acr_name,
                "custom_asset_master": am.name,
                "custom_material_request": pr_item.material_request,
                "custom_purchase_order": pr_item.purchase_order,
                
                # Status
                "is_existing_asset": 0,
                "calculate_depreciation": 0,
            })
            
            # Insert asset
            asset_doc.flags.ignore_validate = False
            asset_doc.insert(ignore_permissions=True)

            # Submit asset
            asset_doc.docstatus = 1
            asset_doc.status = "Submitted"
            asset_doc.submit()
            
            created_assets.append(asset_doc.name)
            
            # Update Asset Master
            frappe.db.set_value("Asset Master", am.name, {
                "custom_asset_created": 1,
                "custom_asset_number": asset_doc.name,
                "custom_purchase_receipt": pr_doc.name,
                "custom_pr_date": pr_doc.posting_date,
                "status": "Active"
            }, update_modified=False)
            
            frappe.msgprint(_("✅ Created Asset: {0} from Asset Master: {1}").format(
                asset_doc.name, am.name), alert=True, indicator="green")
            
        except Exception as e:
            error_msg = _("❌ Error creating asset from Asset Master {0}: {1}").format(am.name, str(e))
            errors.append(error_msg)
            frappe.log_error(message=str(e), title=f"Asset Creation Error - {am.name}")
            frappe.msgprint(error_msg, alert=True, indicator="red")
    
    # Update Asset Creation Request status
    if created_assets:
        # Check if all Asset Masters are converted
        pending_count = frappe.db.count("Asset Master", {
            "asset_creation_request": acr_name,
            "docstatus": 1,
            "custom_asset_created": 0
        })
        
        status = "Completed" if pending_count == 0 else "Partially Completed"
        
        frappe.db.set_value("Asset Creation Request", acr_name, {
            "custom_assets_created": 1,
            "custom_asset_creation_status": status,
            "custom_assets_count": len(created_assets)
        }, update_modified=False)
    
    frappe.db.commit()
    
    # Final summary message
    if created_assets:
        frappe.msgprint(
            _("""<div style='font-size: 14px;'>
                <b>🎉 Asset Creation Successful!</b><br><br>
                <b>Created {0} Asset(s) from {1} received:</b><br>
                {2}
                </div>""").format(
                len(created_assets),
                total_received,
                "<br>".join([f"• {asset}" for asset in created_assets])
            ),
            title=_("Assets Created"),
            indicator="green"
        )
    
    if errors:
        frappe.msgprint(
            _("<b>⚠️ Some errors occurred:</b><br>{0}").format("<br>".join(errors)),
            title=_("Errors"),
            indicator="orange"
        )
    
    return created_assets


def on_cancel_purchase_receipt(doc, method):
    """Cancel linked Assets when PR is cancelled and revert quantities"""
    
    if doc.custom_asset_creation_request:
        # Find and cancel assets created from this PR
        assets = frappe.get_all("Asset",
            filters={
                "purchase_receipt": doc.name,
                "custom_asset_creation_request": doc.custom_asset_creation_request,
                "docstatus": 1
            },
            pluck="name"
        )
        
        cancelled_assets = []
        for asset_name in assets:
            try:
                asset = frappe.get_doc("Asset", asset_name)
                asset.cancel()
                cancelled_assets.append(asset_name)
            except Exception as e:
                frappe.log_error(f"Error cancelling asset {asset_name}: {str(e)}")
        
        if cancelled_assets:
            frappe.msgprint(_("Cancelled {0} Asset(s): {1}").format(
                len(cancelled_assets), ", ".join(cancelled_assets)),
                alert=True, indicator="orange")
        
        # Reset Asset Masters
        frappe.db.sql("""
            UPDATE `tabAsset Master`
            SET custom_asset_created = 0,
                custom_asset_number = NULL,
                custom_purchase_receipt = NULL,
                custom_pr_date = NULL
            WHERE custom_purchase_receipt = %s
        """, doc.name)
        
        frappe.db.commit()