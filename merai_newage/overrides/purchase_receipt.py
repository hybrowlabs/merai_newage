

# import frappe
# from frappe import _
# from frappe.utils import nowdate, flt, cint, get_link_to_form
# from erpnext.controllers.buying_controller import BuyingController ,get_asset_item_details, get_dimensions

# frappe.whitelist()
# def auto_make_assets(asset_items):
#     print("Custom auto_make_assets override called=============================================================")
#     """
#     ✅ CORRECT OVERRIDE: This replaces ERPNext's auto_make_assets
    
#     Registered in hooks.py as:
#     override_whitelisted_methods = {
#         "erpnext.controllers.buying_controller.auto_make_assets": 
#             "merai_newage.overrides.purchase_receipt.auto_make_assets"
#     }
    
#     This function is called BEFORE on_submit hook
#     """
    
#     print("=" * 80)
#     print("Custom auto_make_assets called!")
#     print(f"Asset items: {asset_items}")
#     print("=" * 80)
    
#     # Return None to suppress the popup completely
#     # ERPNext checks if return value is truthy to show popup
#     return None

# @frappe.whitelist()
# def custom_make_asset(asset_items):
#     """
#     ✅ OVERRIDE: Custom make_asset to suppress popup
    
#     This function overrides: erpnext.stock.doctype.purchase_receipt.purchase_receipt.make_asset
#     """
    
#     if not asset_items:
#         return
    
#     # Get PR name
#     pr_name = None
#     if isinstance(asset_items, list) and len(asset_items) > 0:
#         pr_name = asset_items[0].get("purchase_receipt")
    
#     if pr_name:
#         pr = frappe.get_doc("Purchase Receipt", pr_name)
#         if pr.custom_asset_creation_request:
#             # Suppress for ACR
#             return None
    
#     # Default behavior for non-ACR
#     return asset_items
# def before_save_purchase_receipt(doc, method):
#     """Populate ACR from Purchase Order"""
#     if hasattr(doc, 'custom_gate_entry_no') and doc.custom_gate_entry_no:
#         ge = frappe.get_doc("Gate Entry", doc.custom_gate_entry_no)
#         if ge.custom_asset_creation_request:
#             doc.custom_asset_creation_request = ge.custom_asset_creation_request
#             frappe.msgprint(_("Asset Creation Request {0} linked from Gate Entry {1}").format(
#                 ge.custom_asset_creation_request, doc.custom_gate_entry_no
#             ), alert=True, indicator="blue")
#             return
    
#     for item in doc.items:
#         if item.purchase_order:
#             po = frappe.get_doc("Purchase Order", item.purchase_order)
#             if po.custom_asset_creation_request:
#                 doc.custom_asset_creation_request = po.custom_asset_creation_request
#                 break


# def validate_purchase_receipt(doc, method):
#     """Validate PR for asset items and quantity"""
    
#     if doc.custom_asset_creation_request:
#         acr = frappe.get_doc("Asset Creation Request", doc.custom_asset_creation_request)
        
#         # Get asset category to check if CWIP
#         asset_category = frappe.get_doc("Asset Category", acr.category_of_asset)
        
#         # For CWIP assets, we need special handling
#         if asset_category.enable_cwip_accounting:
#             # For CWIP, only mark actual asset items (not services) as fixed asset
#             for item in doc.items:
#                 # Get item master to check if it's a fixed asset item
#                 item_doc = frappe.get_doc("Item", item.item_code)
                
#                 if item_doc.is_fixed_asset:
#                     # This is an actual asset item
#                     item.is_fixed_asset = 1
#                     item.asset_category = acr.category_of_asset
#                     if not item.asset_location:
#                         item.asset_location = acr.get("location")
#                 else:
#                     # This is a service/stock item - don't mark as asset
#                     item.is_fixed_asset = 0
#         else:
#             # Non-CWIP validation
#             # Calculate total PR quantity across all items
#             total_pr_qty = sum(flt(item.qty) for item in doc.items)
            
#             # Get total PO quantity for this ACR
#             total_po_qty = 0
#             for item in doc.items:
#                 if item.purchase_order:
#                     po = frappe.get_doc("Purchase Order", item.purchase_order)
#                     if po.custom_asset_creation_request == doc.custom_asset_creation_request:
#                         total_po_qty += sum(flt(po_item.qty) for po_item in po.items)
            
#             # Validate PR qty doesn't exceed PO qty
#             if total_pr_qty > total_po_qty:
#                 frappe.msgprint(_("""Purchase Receipt quantity ({0}) exceeds Purchase Order quantity ({1}) for Asset Creation Request {2}""").format(
#                     total_pr_qty, total_po_qty, doc.custom_asset_creation_request
#                 ))


# def on_submit_purchase_receipt(doc, method):
#     """Create Assets or handle CWIP based on Asset Category"""
    
#     if doc.custom_asset_creation_request:
#         acr = frappe.get_doc("Asset Creation Request", doc.custom_asset_creation_request)
        
#         asset_category = frappe.get_doc("Asset Category", acr.category_of_asset)
        
#         # Check if CWIP is enabled (core field)
#         if asset_category.enable_cwip_accounting:
#             # Handle CWIP flow - just track PRs, don't create asset yet
#             handle_cwip_purchase_receipt(doc, acr, asset_category)
#         else:
#             # Normal flow - create assets directly
#             create_assets_from_asset_masters(doc)


# def handle_cwip_purchase_receipt(pr_doc, acr, asset_category):
#     """
#     Handle CWIP Purchase Receipt
#     1. Track PRs in ACR child table
#     2. Create/Update CWIP Asset
#     3. ERPNext automatically posts to CWIP account
#     """
    
#     acr_name = acr.name
    
#     # Get all PR items
#     pr_items_data = []
#     total_pr_amount = 0
    
#     for item in pr_doc.items:
#         po_name = item.purchase_order if item.purchase_order else None
        
#         # Check if item is a fixed asset item
#         item_doc = frappe.get_doc("Item", item.item_code)
#         is_asset_item = cint(item_doc.is_fixed_asset)
#         is_stock_item = cint(item_doc.is_stock_item)

#         # Service item = neither asset nor stock
#         is_service_item = 1 if not is_asset_item and not is_stock_item else 0
        
#         # Add to tracking list
#         pr_items_data.append({
#             "item_code": item.item_code,
#             "item_name": item.item_name,
#             "qty": item.qty,
#             "rate": item.rate,
#             "amount": item.amount,
#             "po_name": po_name,
#             "is_asset_item": is_asset_item,
#             "is_stock_item": is_stock_item,
#             "is_service_item": is_service_item,
#             "purchase_receipt_item": item.name  
#         })
        
#         total_pr_amount += flt(item.amount)
    
#     # Add PR entries to ACR child table (one entry per item)
#     for pr_item_data in pr_items_data:
#         acr.append("custom_cwip_purchase_receipts", {
#             "purchase_receipt": pr_doc.name,
#             "pr_date": pr_doc.posting_date,
#             "purchase_order": pr_item_data["po_name"],
#             "supplier": pr_doc.supplier,
#             "item_code": pr_item_data["item_code"],
#             "item_name": pr_item_data["item_name"],
#             "qty": pr_item_data["qty"],
#             "rate": pr_item_data["rate"],
#             "amount": pr_item_data["amount"], 
#             "is_service_item": pr_item_data["is_service_item"],
#             "is_stock_item": pr_item_data["is_stock_item"],
#             "is_asset_item": pr_item_data["is_asset_item"],
            
#             "purchase_receipt_item": pr_item_data["purchase_receipt_item"], 

#             "description": f"{pr_item_data['item_name']} - {'Service/Stock' if pr_item_data['is_service_item'] else 'Asset'}"
#         })
    
#     # Calculate total accumulated amount from all PRs
#     total_cwip_amount = sum(
#         flt(row.amount)
#         for row in acr.custom_cwip_purchase_receipts
#     )

#     acr.custom_total_cwip_amount = total_cwip_amount
    
#     acr.flags.ignore_validate_update_after_submit = True
#     acr.flags.ignore_permissions = True
#     acr.save()
    
#     # Update Asset Masters with items from PR
#     update_asset_master_items_cwip(pr_doc, acr)
    
#     # Check if CWIP Asset already exists
#     existing_cwip_asset = frappe.db.get_value("Asset", {
#         "custom_asset_creation_request": acr_name,
#         "docstatus": ["<", 2]  # Draft or Submitted
#     })
    
#     if existing_cwip_asset:
#         # ✅ For composite assets, DON'T update gross_purchase_amount
#         # It stays at 0 - all tracking is in ACR
#         frappe.msgprint(_("""✅ CWIP Tracking Updated!<br><br>
#             <b>Asset:</b> {0}<br>
#             <b>This PR Amount:</b> ₹{1:,.2f}<br>
#             <b>Total Accumulated:</b> ₹{2:,.2f}<br>
#             <b>Total PRs:</b> {3}<br><br>
            
#             <b>Status:</b> Costs tracked in ACR<br>
#             <b>Accounting:</b> Costs posted to CWIP account<br><br>
            
#             <b>Next Steps:</b><br>
#             - Continue adding PRs, OR<br>
#             - Click "Asset Capitalization" to capitalize
#         """).format(
#             get_link_to_form("Asset", existing_cwip_asset),
#             total_pr_amount,
#             total_cwip_amount,
#             len(set([row.purchase_receipt for row in acr.custom_cwip_purchase_receipts]))
#         ), alert=True, indicator="blue")
#     else:
#         # No asset yet - create new CWIP asset
#         if acr.composite_asset==0:
#             create_new_cwip_asset(pr_doc, acr, asset_category, total_pr_amount, total_cwip_amount)
    
#     frappe.db.commit()


# def create_new_cwip_asset(pr_doc, acr, asset_category, pr_amount, total_cwip_amount):
#     """
#     Create new CWIP Asset on first Purchase Receipt
#     ✅ FIXED: For composite assets, gross_purchase_amount = 0
#     """
    
#     # Get main asset item from PR
#     main_item = None
#     for item in pr_doc.items:
#         item_doc = frappe.get_doc("Item", item.item_code)
#         if item_doc.is_fixed_asset:
#             main_item = item
#             break
    
#     if not main_item:
#         # If no fixed asset item, use first item
#         main_item = pr_doc.items[0]
    
#     print("main item---------", main_item)
    
#     # ✅ KEY FIX: For composite assets, set gross_purchase_amount = 0
#     # All costs are tracked in ACR child table, not in asset itself
#     is_composite = cint(acr.get("composite_item")) or cint(acr.get("composite_asset"))
    
#     # Create Asset document
#     asset_doc = frappe.get_doc({
#         "doctype": "Asset",
#         "asset_name": acr.get("asset_name"),
#         "item_code": main_item.item_code,
#         "asset_category": acr.category_of_asset,
#         "company": pr_doc.company,
        
#         # Location & Department
#         "location": acr.get("location"),
#         "cost_center": acr.get("cost_centre") or pr_doc.cost_center,
#         "custodian": acr.get("custodian"),
#         "department": acr.get("department"),
        
#         # Purchase details
#         "purchase_date": pr_doc.posting_date,
#         "gross_purchase_amount": 0 if is_composite else total_cwip_amount,  # ✅ FIX: 0 for composite
#         "supplier": pr_doc.supplier,
#         "purchase_receipt": pr_doc.name,
        
#         # Reference fields
#         "custom_asset_creation_request": acr.name,
#         "is_composite_asset": 1 if is_composite else 0,  # ✅ Mark as composite
        
#         # Asset stays in DRAFT
#         "is_existing_asset": 0,
#         "docstatus": 0
#     })
    
#     asset_doc.flags.ignore_validate = True  # ✅ Skip validation since gross_purchase_amount = 0
#     asset_doc.insert(ignore_permissions=True)
    
#     frappe.msgprint(_("""✅ CWIP Asset Created!<br><br>
#         <b>Asset:</b> {0}<br>
#         <b>Type:</b> {1}<br>
#         <b>This PR Amount:</b> ₹{2:,.2f}<br>
#         <b>Total Accumulated:</b> ₹{3:,.2f}<br>
#         <b>Total PRs:</b> {4}<br><br>
        
#         <b>Accounting:</b><br>
#         - Costs tracked in ACR (not asset)<br>
#         - Posted to CWIP account<br><br>
        
#         <b>Next Steps:</b><br>
#         1. Continue creating PRs for all project costs<br>
#         2. All amounts tracked in ACR child table<br>
#         3. Click "Asset Capitalization" to capitalize when ready
#     """).format(
#         get_link_to_form("Asset", asset_doc.name),
#         "Composite Asset" if is_composite else "Single Asset",
#         pr_amount,
#         total_cwip_amount,
#         len(set([row.purchase_receipt for row in acr.custom_cwip_purchase_receipts]))
#     ), alert=True, indicator="green")
    
#     frappe.db.commit()


# def update_asset_master_items_cwip(pr_doc, acr):
#     """Update Asset Masters with item details from PR for CWIP"""
    
#     # Get Asset Masters for this ACR
#     asset_masters = frappe.get_all("Asset Master",
#         filters={
#             "asset_creation_request": acr.name,
#             "docstatus": 1
#         },
#         fields=["name", "item", "item_name"]
#     )
    
#     if not asset_masters:
#         return
    
#     # Get asset items from PR (items marked as fixed asset)
#     asset_items = []
#     for pr_item in pr_doc.items:
#         item_doc = frappe.get_doc("Item", pr_item.item_code)
#         if item_doc.is_fixed_asset:
#             asset_items.append(pr_item)
    
#     if not asset_items:
#         return
    
#     # Use first asset item for mapping
#     main_item = asset_items[0]
    
#     # Update Asset Masters that don't have item set
#     for am in asset_masters:
#         if not am.get("item"):
#             frappe.db.set_value("Asset Master", am.name, {
#                 "item": main_item.item_code,
#                 "item_name": main_item.item_name
#             }, update_modified=False)


# def get_asset_cost(am, pr_item, asset_qty):
#     """Calculate asset cost based on purchase amount or rate"""
#     if flt(am.get("purchase_amount_approx", 0)) > 0:
#         return flt(am.purchase_amount_approx)

#     if flt(pr_item.base_rate) > 0:
#         return flt(pr_item.base_rate) * asset_qty

#     return flt(pr_item.amount)


# def create_assets_from_asset_masters(pr_doc):
#     """
#     ✅ FIXED: Create assets based on ACTUAL PR quantity
#     Update Asset Masters with MR/PO references during asset creation
#     """
    
#     acr_name = pr_doc.custom_asset_creation_request
#     acr = frappe.get_doc("Asset Creation Request", acr_name)
    
#     # Get PO and MR from PR items
#     po_name = None
#     mr_name = None
#     for item in pr_doc.items:
#         if item.purchase_order and not po_name:
#             po_name = item.purchase_order
#         if item.material_request and not mr_name:
#             mr_name = item.material_request
#         if po_name and mr_name:
#             break
    
#     # Group PR items by item_code
#     pr_items_by_code = {}
#     for item in pr_doc.items:
#         if item.item_code not in pr_items_by_code:
#             pr_items_by_code[item.item_code] = []
#         pr_items_by_code[item.item_code].append(item)
    
#     created_assets = []
#     errors = []
    
#     # Process each item type separately
#     for item_code, pr_items_list in pr_items_by_code.items():
#         # ✅ Use ACTUAL PR received quantity
#         actual_received_qty = sum(flt(item.qty) for item in pr_items_list)
#         pr_item = pr_items_list[0]
        
#         # ✅ Get ONLY unused Asset Masters
#         filters = {
#             "asset_creation_request": acr_name,
#             "docstatus": 1,
#             "custom_asset_created": 0  # Only unused
#         }
        
#         all_asset_masters = frappe.get_all("Asset Master",
#             filters=filters,
#             fields=["name", "item", "item_name", "asset_category", "company", 
#                     "location", "cost_center", "custodian", "department", "plant",
#                     "qty", "bulk_item", "asset_count", "purchase_amount_approx"],
#             order_by="creation asc"
#         )
        
#         # Filter: matching item or unassigned
#         asset_masters = []
#         unassigned_masters = []
        
#         for am in all_asset_masters:
#             if am.get("item") == item_code:
#                 asset_masters.append(am)
#             elif not am.get("item"):
#                 unassigned_masters.append(am)
        
#         # ✅ Limit to ACTUAL received quantity
#         assets_needed = int(actual_received_qty)
        
#         # Assign unassigned masters if needed
#         if len(asset_masters) < assets_needed and unassigned_masters:
#             remaining_needed = assets_needed - len(asset_masters)
#             masters_to_assign = unassigned_masters[:remaining_needed]
            
#             for am in masters_to_assign:
#                 frappe.db.set_value("Asset Master", am["name"], {
#                     "item": item_code,
#                     "item_name": pr_item.item_name
#                 }, update_modified=False)
#                 am["item"] = item_code
#                 am["item_name"] = pr_item.item_name
#                 asset_masters.append(am)
        
#         # Limit to received quantity
#         asset_masters = asset_masters[:assets_needed]
        
#         if not asset_masters:
#             frappe.msgprint(_("⚠️ No Asset Masters available for item {0} (Received: {1})").format(
#                 item_code, actual_received_qty), alert=True, indicator="orange")
#             continue
        
#         # Create assets for ACTUAL received quantity only
#         for idx, am in enumerate(asset_masters, 1):
#             try:
#                 item_code_to_use = am.get("item") or item_code
#                 item_name_to_use = am.get("item_name") or pr_item.item_name
                
#                 asset_qty = 1
#                 if cint(am.get("bulk_item")):
#                     asset_qty = cint(am.get("qty")) or 1
#                 asset_category_name = am.get("asset_category") or acr.category_of_asset
#                 asset_category_doc = frappe.get_doc("Asset Category", asset_category_name)
#                 cost_per_asset = get_asset_cost(am, pr_item, asset_qty)
#                 calculate_depreciation = calculate_depreciation = cint(asset_category_doc.get("custom_auto_depreciation", 0))
#                 print("calculate_depreciation=================================================", calculate_depreciation,type(calculate_depreciation))
#                 # Create Asset
#                 asset_doc = frappe.get_doc({
#                     "doctype": "Asset",
#                     "asset_name": f"{item_name_to_use}-{am['name']}",
#                     "item_code": item_code_to_use,
#                     "asset_category": am.get("asset_category") or acr.category_of_asset,
#                     "company": am.get("company") or pr_doc.company,
                    
#                     "location": am.get("location"),
#                     "cost_center": am.get("cost_center") or pr_doc.cost_center,
#                     "custodian": am.get("custodian"),
#                     "department": am.get("department"),
                    
#                     "purchase_date": pr_doc.posting_date,
#                     "available_for_use_date": pr_doc.posting_date,
#                     "gross_purchase_amount": cost_per_asset,
#                     "purchase_receipt": pr_doc.name,
#                     "purchase_receipt_amount": cost_per_asset,
#                     "supplier": pr_doc.supplier,
#                     "asset_quantity": asset_qty,
                    
#                     "custom_asset_creation_request": acr_name,
#                     "custom_asset_master": am["name"],
#                     "custom_material_request": mr_name,
#                     "custom_purchase_order": po_name,
                    
#                     "is_existing_asset": 0,
#                     "calculate_depreciation": calculate_depreciation,
#                 })
                
#                 asset_doc.insert(ignore_permissions=True)
                
#                 created_assets.append({
#                     "asset": asset_doc.name,
#                     "item": item_code_to_use,
#                     "item_name": item_name_to_use
#                 })
                
#                 # ✅ Update Asset Master with MR/PO/PR references
#                 frappe.db.set_value("Asset Master", am["name"], {
#                     "custom_asset_created": 1,
#                     "custom_asset_number": asset_doc.name,
#                     "custom_material_request": mr_name,
#                     "custom_mr_date": frappe.db.get_value("Material Request", mr_name, "transaction_date") if mr_name else None,
#                     "custom_mr_status": "Submitted" if mr_name else None,
#                     "custom_purchase_order": po_name,
#                     "custom_po_date": frappe.db.get_value("Purchase Order", po_name, "transaction_date") if po_name else None,
#                     "custom_po_status": "Submitted" if po_name else None,
#                     "custom_purchase_receipt": pr_doc.name,
#                     "custom_pr_date": pr_doc.posting_date,
#                 }, update_modified=False)
                
#             except Exception as e:
#                 error_msg = _("❌ Error creating asset from Asset Master {0}: {1}").format(
#                     am["name"], str(e))
#                 errors.append(error_msg)
#                 frappe.log_error(message=str(e), title=f"Asset Creation Error - {am['name']}")
#                 frappe.msgprint(error_msg, alert=True, indicator="red")
    
#     # Update ACR status
#     if created_assets:
#         pending_count = frappe.db.count("Asset Master", {
#             "asset_creation_request": acr_name,
#             "docstatus": 1,
#             "custom_asset_created": 0
#         })
        
#         status = "Completed" if pending_count == 0 else "Partially Completed"
#         frappe.db.set_value("Asset Creation Request", acr_name, "asset_creation_status", status, update_modified=False)
    
#     frappe.db.commit()
    
#     # Summary message
#     if created_assets:
#         remaining = frappe.db.count("Asset Master", {
#             "asset_creation_request": acr_name,
#             "docstatus": 1,
#             "custom_asset_created": 0
#         })
        
#         frappe.msgprint(_("""<b>🎉 Assets Created Successfully!</b><br><br>
#             <b>This PR:</b> {0} assets created<br>
#             <b>Remaining:</b> {1} Asset Masters pending for future PRs
#         """).format(len(created_assets), remaining),
#             title=_("Success"),
#             indicator="green"
#         )
    
#     return [asset_info["asset"] for asset_info in created_assets]
# def on_cancel_purchase_receipt(doc, method):
#     """Handle PR cancellation for both CWIP and regular assets"""
    
#     if doc.custom_asset_creation_request:
#         acr = frappe.get_doc("Asset Creation Request", doc.custom_asset_creation_request)
#         asset_category = frappe.get_doc("Asset Category", acr.category_of_asset)
        
#         if asset_category.enable_cwip_accounting:
#             # Handle CWIP asset cancellation
#             cancel_cwip_purchase_receipt(doc, acr)
#         else:
#             # Cancel regular assets
#             cancel_regular_assets(doc)


# def cancel_cwip_purchase_receipt(pr_doc, acr):
#     """Handle CWIP PR cancellation - just remove from tracking"""
    
#     # Remove PR from ACR child table
#     acr.custom_cwip_purchase_receipts = [
#         row for row in acr.custom_cwip_purchase_receipts 
#         if row.purchase_receipt != pr_doc.name
#     ]
    
#     # Recalculate total
#     total_cwip_amount = sum(
#         flt(row.amount)
#         for row in acr.custom_cwip_purchase_receipts
#     )

#     acr.custom_total_cwip_amount = total_cwip_amount
    
#     acr.flags.ignore_validate_update_after_submit = True
#     acr.flags.ignore_permissions = True
#     acr.save()
    
#     frappe.msgprint(_("""✅ PR Removed from Tracking<br><br>
#         <b>Removed PR:</b> {0}<br>
#         <b>New Total:</b> ₹{1:,.2f}<br><br>
#         <b>Note:</b> For composite assets, amount tracked in ACR only<br>
#         GL entries reversed automatically
#     """).format(
#         pr_doc.name,
#         total_cwip_amount
#     ), alert=True, indicator="orange")
    
#     frappe.db.commit()


# def cancel_regular_assets(pr_doc):
#     """Cancel regular assets created from this PR"""
    
#     assets = frappe.get_all("Asset",
#         filters={
#             "purchase_receipt": pr_doc.name,
#             "custom_asset_creation_request": pr_doc.custom_asset_creation_request,
#             "docstatus": 1
#         },
#         pluck="name"
#     )
    
#     for asset_name in assets:
#         try:
#             asset = frappe.get_doc("Asset", asset_name)
#             asset.cancel()
#         except Exception as e:
#             frappe.log_error(f"Error cancelling asset {asset_name}: {str(e)}")
    
#     # Reset Asset Masters
#     frappe.db.sql("""
#         UPDATE `tabAsset Master`
#         SET custom_asset_created = 0,
#             custom_asset_number = NULL,
#             custom_purchase_receipt = NULL,
#             custom_pr_date = NULL
#         WHERE custom_purchase_receipt = %s
#     """, pr_doc.name)
    
#     frappe.db.commit()






import frappe
from frappe import _
from frappe.utils import nowdate, flt, cint, get_link_to_form, add_months, getdate
from erpnext.controllers.buying_controller import BuyingController, get_asset_item_details, get_dimensions

@frappe.whitelist()
def auto_make_assets(asset_items):
    print("Custom auto_make_assets override called=============================================================")
    """
    ✅ CORRECT OVERRIDE: This replaces ERPNext's auto_make_assets
    
    Registered in hooks.py as:
    override_whitelisted_methods = {
        "erpnext.controllers.buying_controller.auto_make_assets": 
            "merai_newage.overrides.purchase_receipt.auto_make_assets"
    }
    
    This function is called BEFORE on_submit hook
    """
    
    print("=" * 80)
    print("Custom auto_make_assets called!")
    print(f"Asset items: {asset_items}")
    print("=" * 80)
    
    # Return None to suppress the popup completely
    # ERPNext checks if return value is truthy to show popup
    return None

@frappe.whitelist()
def custom_make_asset(asset_items):
    """
    ✅ OVERRIDE: Custom make_asset to suppress popup
    
    This function overrides: erpnext.stock.doctype.purchase_receipt.purchase_receipt.make_asset
    """
    
    if not asset_items:
        return
    
    # Get PR name
    pr_name = None
    if isinstance(asset_items, list) and len(asset_items) > 0:
        pr_name = asset_items[0].get("purchase_receipt")
    
    if pr_name:
        pr = frappe.get_doc("Purchase Receipt", pr_name)
        if pr.custom_asset_creation_request:
            # Suppress for ACR
            return None
    
    # Default behavior for non-ACR
    return asset_items


def before_save_purchase_receipt(doc, method):
    """Populate ACR from Purchase Order"""
    if hasattr(doc, 'custom_gate_entry_no') and doc.custom_gate_entry_no:
        ge = frappe.get_doc("Gate Entry", doc.custom_gate_entry_no)
        if ge.custom_asset_creation_request:
            doc.custom_asset_creation_request = ge.custom_asset_creation_request
            frappe.msgprint(_("Asset Creation Request {0} linked from Gate Entry {1}").format(
                ge.custom_asset_creation_request, doc.custom_gate_entry_no
            ), alert=True, indicator="blue")
            return
    
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
        
        # Get asset category to check if CWIP
        asset_category = frappe.get_doc("Asset Category", acr.category_of_asset)
        
        # For CWIP assets, we need special handling
        if asset_category.enable_cwip_accounting:
            # For CWIP, only mark actual asset items (not services) as fixed asset
            for item in doc.items:
                # Get item master to check if it's a fixed asset item
                item_doc = frappe.get_doc("Item", item.item_code)
                
                if item_doc.is_fixed_asset:
                    # This is an actual asset item
                    item.is_fixed_asset = 1
                    item.asset_category = acr.category_of_asset
                    if not item.asset_location:
                        item.asset_location = acr.get("location")
                else:
                    # This is a service/stock item - don't mark as asset
                    item.is_fixed_asset = 0
        else:
            # Non-CWIP validation
            # Calculate total PR quantity across all items
            total_pr_qty = sum(flt(item.qty) for item in doc.items)
            
            # Get total PO quantity for this ACR
            total_po_qty = 0
            for item in doc.items:
                if item.purchase_order:
                    po = frappe.get_doc("Purchase Order", item.purchase_order)
                    if po.custom_asset_creation_request == doc.custom_asset_creation_request:
                        total_po_qty += sum(flt(po_item.qty) for po_item in po.items)
            
            # Validate PR qty doesn't exceed PO qty
            if total_pr_qty > total_po_qty:
                frappe.msgprint(_("""Purchase Receipt quantity ({0}) exceeds Purchase Order quantity ({1}) for Asset Creation Request {2}""").format(
                    total_pr_qty, total_po_qty, doc.custom_asset_creation_request
                ))


def on_submit_purchase_receipt(doc, method):
    """Create Assets or handle CWIP based on Asset Category"""
    
    if doc.custom_asset_creation_request:
        acr = frappe.get_doc("Asset Creation Request", doc.custom_asset_creation_request)
        
        asset_category = frappe.get_doc("Asset Category", acr.category_of_asset)
        
        # Check if CWIP is enabled (core field)
        if asset_category.enable_cwip_accounting:
            # Handle CWIP flow - just track PRs, don't create asset yet
            handle_cwip_purchase_receipt(doc, acr, asset_category)
        else:
            # Normal flow - create assets directly
            create_assets_from_asset_masters(doc)


def handle_cwip_purchase_receipt(pr_doc, acr, asset_category):
    """
    Handle CWIP Purchase Receipt
    1. Track PRs in ACR child table
    2. Create/Update CWIP Asset
    3. ERPNext automatically posts to CWIP account
    """
    
    acr_name = acr.name
    
    # Get all PR items
    pr_items_data = []
    total_pr_amount = 0
    
    for item in pr_doc.items:
        po_name = item.purchase_order if item.purchase_order else None
        
        # Check if item is a fixed asset item
        item_doc = frappe.get_doc("Item", item.item_code)
        is_asset_item = cint(item_doc.is_fixed_asset)
        is_stock_item = cint(item_doc.is_stock_item)

        # Service item = neither asset nor stock
        is_service_item = 1 if not is_asset_item and not is_stock_item else 0
        
        # Add to tracking list
        pr_items_data.append({
            "item_code": item.item_code,
            "item_name": item.item_name,
            "qty": item.qty,
            "rate": item.rate,
            "amount": item.amount,
            "po_name": po_name,
            "is_asset_item": is_asset_item,
            "is_stock_item": is_stock_item,
            "is_service_item": is_service_item,
            "purchase_receipt_item": item.name  
        })
        
        total_pr_amount += flt(item.amount)
    
    # Add PR entries to ACR child table (one entry per item)
    for pr_item_data in pr_items_data:
        acr.append("custom_cwip_purchase_receipts", {
            "purchase_receipt": pr_doc.name,
            "pr_date": pr_doc.posting_date,
            "purchase_order": pr_item_data["po_name"],
            "supplier": pr_doc.supplier,
            "item_code": pr_item_data["item_code"],
            "item_name": pr_item_data["item_name"],
            "qty": pr_item_data["qty"],
            "rate": pr_item_data["rate"],
            "amount": pr_item_data["amount"], 
            "is_service_item": pr_item_data["is_service_item"],
            "is_stock_item": pr_item_data["is_stock_item"],
            "is_asset_item": pr_item_data["is_asset_item"],
            
            "purchase_receipt_item": pr_item_data["purchase_receipt_item"], 

            "description": f"{pr_item_data['item_name']} - {'Service/Stock' if pr_item_data['is_service_item'] else 'Asset'}"
        })
    
    # Calculate total accumulated amount from all PRs
    total_cwip_amount = sum(
        flt(row.amount)
        for row in acr.custom_cwip_purchase_receipts
    )

    acr.custom_total_cwip_amount = total_cwip_amount
    
    acr.flags.ignore_validate_update_after_submit = True
    acr.flags.ignore_permissions = True
    acr.save()
    
    # Update Asset Masters with items from PR
    update_asset_master_items_cwip(pr_doc, acr)
    
    # Check if CWIP Asset already exists
    existing_cwip_asset = frappe.db.get_value("Asset", {
        "custom_asset_creation_request": acr_name,
        "docstatus": ["<", 2]  # Draft or Submitted
    })
    
    if existing_cwip_asset:
        # ✅ For composite assets, DON'T update gross_purchase_amount
        # It stays at 0 - all tracking is in ACR
        frappe.msgprint(_("""✅ CWIP Tracking Updated!<br><br>
            <b>Asset:</b> {0}<br>
            <b>This PR Amount:</b> ₹{1:,.2f}<br>
            <b>Total Accumulated:</b> ₹{2:,.2f}<br>
            <b>Total PRs:</b> {3}<br><br>
            
            <b>Status:</b> Costs tracked in ACR<br>
            <b>Accounting:</b> Costs posted to CWIP account<br><br>
            
            <b>Next Steps:</b><br>
            - Continue adding PRs, OR<br>
            - Click "Asset Capitalization" to capitalize
        """).format(
            get_link_to_form("Asset", existing_cwip_asset),
            total_pr_amount,
            total_cwip_amount,
            len(set([row.purchase_receipt for row in acr.custom_cwip_purchase_receipts]))
        ), alert=True, indicator="blue")
    else:
        # No asset yet - create new CWIP asset
        if acr.composite_asset==0:
            create_new_cwip_asset(pr_doc, acr, asset_category, total_pr_amount, total_cwip_amount)
    
    frappe.db.commit()


def create_new_cwip_asset(pr_doc, acr, asset_category, pr_amount, total_cwip_amount):
    """
    Create new CWIP Asset on first Purchase Receipt
    ✅ FIXED: For composite assets, gross_purchase_amount = 0
    """
    
    # Get main asset item from PR
    main_item = None
    for item in pr_doc.items:
        item_doc = frappe.get_doc("Item", item.item_code)
        if item_doc.is_fixed_asset:
            main_item = item
            break
    
    if not main_item:
        # If no fixed asset item, use first item
        main_item = pr_doc.items[0]
    
    print("main item---------", main_item)
    
    # ✅ KEY FIX: For composite assets, set gross_purchase_amount = 0
    # All costs are tracked in ACR child table, not in asset itself
    is_composite = cint(acr.get("composite_item")) or cint(acr.get("composite_asset"))
    
    # Create Asset document
    asset_doc = frappe.get_doc({
        "doctype": "Asset",
        "asset_name": acr.get("asset_name"),
        "item_code": main_item.item_code,
        "asset_category": acr.category_of_asset,
        "company": pr_doc.company,
        
        # Location & Department
        "location": acr.get("location"),
        "cost_center": acr.get("cost_centre") or pr_doc.cost_center,
        "custodian": acr.get("custodian"),
        "department": acr.get("department"),
        
        # Purchase details
        "purchase_date": pr_doc.posting_date,
        "gross_purchase_amount": 0 if is_composite else total_cwip_amount,  # ✅ FIX: 0 for composite
        "supplier": pr_doc.supplier,
        "purchase_receipt": pr_doc.name,
        
        # Reference fields
        "custom_asset_creation_request": acr.name,
        "is_composite_asset": 1 if is_composite else 0,  # ✅ Mark as composite
        
        # Asset stays in DRAFT
        "is_existing_asset": 0,
        "docstatus": 0
    })
    
    asset_doc.flags.ignore_validate = True  # ✅ Skip validation since gross_purchase_amount = 0
    asset_doc.insert(ignore_permissions=True)
    
    frappe.msgprint(_("""✅ CWIP Asset Created!<br><br>
        <b>Asset:</b> {0}<br>
        <b>Type:</b> {1}<br>
        <b>This PR Amount:</b> ₹{2:,.2f}<br>
        <b>Total Accumulated:</b> ₹{3:,.2f}<br>
        <b>Total PRs:</b> {4}<br><br>
        
        <b>Accounting:</b><br>
        - Costs tracked in ACR (not asset)<br>
        - Posted to CWIP account<br><br>
        
        <b>Next Steps:</b><br>
        1. Continue creating PRs for all project costs<br>
        2. All amounts tracked in ACR child table<br>
        3. Click "Asset Capitalization" to capitalize when ready
    """).format(
        get_link_to_form("Asset", asset_doc.name),
        "Composite Asset" if is_composite else "Single Asset",
        pr_amount,
        total_cwip_amount,
        len(set([row.purchase_receipt for row in acr.custom_cwip_purchase_receipts]))
    ), alert=True, indicator="green")
    
    frappe.db.commit()


def update_asset_master_items_cwip(pr_doc, acr):
    """Update Asset Masters with item details from PR for CWIP"""
    
    # Get Asset Masters for this ACR
    asset_masters = frappe.get_all("Asset Master",
        filters={
            "asset_creation_request": acr.name,
            "docstatus": 1
        },
        fields=["name", "item", "item_name"]
    )
    
    if not asset_masters:
        return
    
    # Get asset items from PR (items marked as fixed asset)
    asset_items = []
    for pr_item in pr_doc.items:
        item_doc = frappe.get_doc("Item", pr_item.item_code)
        if item_doc.is_fixed_asset:
            asset_items.append(pr_item)
    
    if not asset_items:
        return
    
    # Use first asset item for mapping
    main_item = asset_items[0]
    
    # Update Asset Masters that don't have item set
    for am in asset_masters:
        if not am.get("item"):
            frappe.db.set_value("Asset Master", am.name, {
                "item": main_item.item_code,
                "item_name": main_item.item_name
            }, update_modified=False)


def get_asset_cost(am, pr_item, asset_qty):
    """Calculate asset cost based on purchase amount or rate"""
    if flt(am.get("purchase_amount_approx", 0)) > 0:
        return flt(am.purchase_amount_approx)

    if flt(pr_item.base_rate) > 0:
        return flt(pr_item.base_rate) * asset_qty

    return flt(pr_item.amount)


def setup_depreciation_schedule(asset_doc, asset_category_doc, purchase_date):
    """
    ✅ FIXED: Setup depreciation schedule from Asset Category
    This function adds finance books to the asset BEFORE it's inserted
    """
    
    # Get finance books from Asset Category
    if not asset_category_doc.finance_books:
        print("⚠️ No finance books found in Asset Category")
        return False
    
    print(f"✅ Found {len(asset_category_doc.finance_books)} finance book(s) in Asset Category")
    
    # Add each finance book from Asset Category
    for fb in asset_category_doc.finance_books:
        finance_book_name = fb.finance_book if fb.finance_book else None
        
        # Get depreciation method and details
        depreciation_method = fb.depreciation_method or "Straight Line"
        total_number_of_depreciations = cint(fb.total_number_of_depreciations) or 12
        frequency_of_depreciation = cint(fb.frequency_of_depreciation) or 1
        
        # Calculate depreciation start date
        depreciation_start_date = add_months(getdate(purchase_date), frequency_of_depreciation)
        
        print(f"✅ Adding finance book: {finance_book_name or 'None'}, Method: {depreciation_method}, Periods: {total_number_of_depreciations}")
        
        # Add to asset's finance books
        asset_doc.append("finance_books", {
            "finance_book": finance_book_name,
            "depreciation_method": depreciation_method,
            "total_number_of_depreciations": total_number_of_depreciations,
            "frequency_of_depreciation": frequency_of_depreciation,
            "depreciation_start_date": depreciation_start_date,
            "expected_value_after_useful_life": flt(fb.expected_value_after_useful_life) or 0
        })
    
    return True


def create_assets_from_asset_masters(pr_doc):
    """
    ✅ FIXED: Create assets based on ACTUAL PR quantity
    ✅ FIXED: Proper depreciation setup - set calculate_depreciation ONLY if finance books added
    Update Asset Masters with MR/PO references during asset creation
    """
    
    acr_name = pr_doc.custom_asset_creation_request
    acr = frappe.get_doc("Asset Creation Request", acr_name)
    
    # Get PO and MR from PR items
    po_name = None
    mr_name = None
    for item in pr_doc.items:
        if item.purchase_order and not po_name:
            po_name = item.purchase_order
        if item.material_request and not mr_name:
            mr_name = item.material_request
        if po_name and mr_name:
            break
    
    # Group PR items by item_code
    pr_items_by_code = {}
    for item in pr_doc.items:
        if item.item_code not in pr_items_by_code:
            pr_items_by_code[item.item_code] = []
        pr_items_by_code[item.item_code].append(item)
    
    created_assets = []
    errors = []
    
    # Process each item type separately
    for item_code, pr_items_list in pr_items_by_code.items():
        # ✅ Use ACTUAL PR received quantity
        actual_received_qty = sum(flt(item.qty) for item in pr_items_list)
        pr_item = pr_items_list[0]
        
        # ✅ Get ONLY unused Asset Masters
        filters = {
            "asset_creation_request": acr_name,
            "docstatus": 1,
            "custom_asset_created": 0  # Only unused
        }
        
        all_asset_masters = frappe.get_all("Asset Master",
            filters=filters,
            fields=["name", "item", "item_name", "asset_category", "company", 
                    "location", "cost_center", "custodian", "department", "plant",
                    "qty", "bulk_item", "asset_count", "purchase_amount_approx"],
            order_by="creation asc"
        )
        
        # Filter: matching item or unassigned
        asset_masters = []
        unassigned_masters = []
        
        for am in all_asset_masters:
            if am.get("item") == item_code:
                asset_masters.append(am)
            elif not am.get("item"):
                unassigned_masters.append(am)
        
        # ✅ Limit to ACTUAL received quantity
        assets_needed = int(actual_received_qty)
        
        # Assign unassigned masters if needed
        if len(asset_masters) < assets_needed and unassigned_masters:
            remaining_needed = assets_needed - len(asset_masters)
            masters_to_assign = unassigned_masters[:remaining_needed]
            
            for am in masters_to_assign:
                frappe.db.set_value("Asset Master", am["name"], {
                    "item": item_code,
                    "item_name": pr_item.item_name
                }, update_modified=False)
                am["item"] = item_code
                am["item_name"] = pr_item.item_name
                asset_masters.append(am)
        
        # Limit to received quantity
        asset_masters = asset_masters[:assets_needed]
        
        if not asset_masters:
            frappe.msgprint(_("⚠️ No Asset Masters available for item {0} (Received: {1})").format(
                item_code, actual_received_qty), alert=True, indicator="orange")
            continue
        
        # Create assets for ACTUAL received quantity only
        for idx, am in enumerate(asset_masters, 1):
            try:
                item_code_to_use = am.get("item") or item_code
                item_name_to_use = am.get("item_name") or pr_item.item_name
                
                asset_qty = 1
                if cint(am.get("bulk_item")):
                    asset_qty = cint(am.get("qty")) or 1
                
                # Get Asset Category
                asset_category_name = am.get("asset_category") or acr.category_of_asset
                asset_category_doc = frappe.get_doc("Asset Category", asset_category_name)
                
                cost_per_asset = get_asset_cost(am, pr_item, asset_qty)
                
                # ✅ Check custom field for auto depreciation
                should_calculate_depreciation = cint(asset_category_doc.get("custom_auto_depreciation", 0))
                
                print(f"=" * 80)
                print(f"Creating asset {idx} for {item_code_to_use}")
                print(f"Asset Category: {asset_category_name}")
                print(f"custom_auto_depreciation from category: {should_calculate_depreciation}")
                
                # ✅ FIX: Create Asset WITHOUT calculate_depreciation first
                asset_doc = frappe.get_doc({
                    "doctype": "Asset",
                    "asset_name": f"{item_name_to_use}-{am['name']}",
                    "item_code": item_code_to_use,
                    "asset_category": asset_category_name,
                    "company": am.get("company") or pr_doc.company,
                    
                    "location": am.get("location"),
                    "cost_center": am.get("cost_center") or pr_doc.cost_center,
                    "custodian": am.get("custodian"),
                    "department": am.get("department"),
                    
                    "purchase_date": pr_doc.posting_date,
                    "available_for_use_date": pr_doc.posting_date,
                    "gross_purchase_amount": cost_per_asset,
                    "purchase_receipt": pr_doc.name,
                    "purchase_receipt_amount": cost_per_asset,
                    "supplier": pr_doc.supplier,
                    "asset_quantity": asset_qty,
                    
                    "custom_asset_creation_request": acr_name,
                    "custom_asset_master": am["name"],
                    "custom_material_request": mr_name,
                    "custom_purchase_order": po_name,
                    
                    "is_existing_asset": 0,
                    # ✅ DON'T set calculate_depreciation yet
                })
                
                # ✅ FIX: Add finance books FIRST, then set calculate_depreciation
                depreciation_added = False
                if should_calculate_depreciation == 1:
                    print("Setting up depreciation for asset...")
                    depreciation_added = setup_depreciation_schedule(asset_doc, asset_category_doc, pr_doc.posting_date)
                    
                    if depreciation_added:
                        # ✅ Only set calculate_depreciation if finance books were successfully added
                        asset_doc.calculate_depreciation = 1
                        print(f"✅ Depreciation enabled: finance books added = {len(asset_doc.finance_books)}")
                    else:
                        print("⚠️ Could not add finance books, calculate_depreciation will be 0")
                        asset_doc.calculate_depreciation = 0
                else:
                    asset_doc.calculate_depreciation = 0
                    print("Depreciation disabled (custom_auto_depreciation = 0)")
                
                print(f"Final calculate_depreciation value: {asset_doc.calculate_depreciation}")
                print(f"=" * 80)
                
                # ✅ Insert asset
                asset_doc.insert(ignore_permissions=True)
                
                created_assets.append({
                    "asset": asset_doc.name,
                    "item": item_code_to_use,
                    "item_name": item_name_to_use
                })
                if should_calculate_depreciation==1:
                    asset_doc.submit()  # Submit immediately after insert
                # ✅ Update Asset Master with MR/PO/PR references
                frappe.db.set_value("Asset Master", am["name"], {
                    "custom_asset_created": 1,
                    "custom_asset_number": asset_doc.name,
                    "custom_material_request": mr_name,
                    "custom_mr_date": frappe.db.get_value("Material Request", mr_name, "transaction_date") if mr_name else None,
                    "custom_mr_status": "Submitted" if mr_name else None,
                    "custom_purchase_order": po_name,
                    "custom_po_date": frappe.db.get_value("Purchase Order", po_name, "transaction_date") if po_name else None,
                    "custom_po_status": "Submitted" if po_name else None,
                    "custom_purchase_receipt": pr_doc.name,
                    "custom_pr_date": pr_doc.posting_date,
                }, update_modified=False)
                
            except Exception as e:
                import traceback
                error_trace = traceback.format_exc()
                error_msg = _("❌ Error creating asset from Asset Master {0}: {1}").format(
                    am["name"], str(e))
                errors.append(error_msg)
                frappe.log_error(message=error_trace, title=f"Asset Creation Error - {am['name']}")
                frappe.msgprint(error_msg, alert=True, indicator="red")
                print(f"ERROR: {error_trace}")
    
    # Update ACR status
    if created_assets:
        pending_count = frappe.db.count("Asset Master", {
            "asset_creation_request": acr_name,
            "docstatus": 1,
            "custom_asset_created": 0
        })
        
        status = "Completed" if pending_count == 0 else "Partially Completed"
        frappe.db.set_value("Asset Creation Request", acr_name, "asset_creation_status", status, update_modified=False)
    
    frappe.db.commit()
    
    # Summary message
    if created_assets:
        remaining = frappe.db.count("Asset Master", {
            "asset_creation_request": acr_name,
            "docstatus": 1,
            "custom_asset_created": 0
        })
        
        frappe.msgprint(_("""<b>🎉 Assets Created Successfully!</b><br><br>
            <b>This PR:</b> {0} assets created<br>
            <b>Remaining:</b> {1} Asset Masters pending for future PRs
        """).format(len(created_assets), remaining),
            title=_("Success"),
            indicator="green"
        )
    
    return [asset_info["asset"] for asset_info in created_assets]


def on_cancel_purchase_receipt(doc, method):
    """Handle PR cancellation for both CWIP and regular assets"""
    
    if doc.custom_asset_creation_request:
        acr = frappe.get_doc("Asset Creation Request", doc.custom_asset_creation_request)
        asset_category = frappe.get_doc("Asset Category", acr.category_of_asset)
        
        if asset_category.enable_cwip_accounting:
            # Handle CWIP asset cancellation
            cancel_cwip_purchase_receipt(doc, acr)
        else:
            # Cancel regular assets
            cancel_regular_assets(doc)


def cancel_cwip_purchase_receipt(pr_doc, acr):
    """Handle CWIP PR cancellation - just remove from tracking"""
    
    # Remove PR from ACR child table
    acr.custom_cwip_purchase_receipts = [
        row for row in acr.custom_cwip_purchase_receipts 
        if row.purchase_receipt != pr_doc.name
    ]
    
    # Recalculate total
    total_cwip_amount = sum(
        flt(row.amount)
        for row in acr.custom_cwip_purchase_receipts
    )

    acr.custom_total_cwip_amount = total_cwip_amount
    
    acr.flags.ignore_validate_update_after_submit = True
    acr.flags.ignore_permissions = True
    acr.save()
    
    frappe.msgprint(_("""✅ PR Removed from Tracking<br><br>
        <b>Removed PR:</b> {0}<br>
        <b>New Total:</b> ₹{1:,.2f}<br><br>
        <b>Note:</b> For composite assets, amount tracked in ACR only<br>
        GL entries reversed automatically
    """).format(
        pr_doc.name,
        total_cwip_amount
    ), alert=True, indicator="orange")
    
    frappe.db.commit()


def cancel_regular_assets(pr_doc):
    """Cancel regular assets created from this PR"""
    
    assets = frappe.get_all("Asset",
        filters={
            "purchase_receipt": pr_doc.name,
            "custom_asset_creation_request": pr_doc.custom_asset_creation_request,
            "docstatus": 1
        },
        pluck="name"
    )
    
    for asset_name in assets:
        try:
            asset = frappe.get_doc("Asset", asset_name)
            asset.cancel()
        except Exception as e:
            frappe.log_error(f"Error cancelling asset {asset_name}: {str(e)}")
    
    # Reset Asset Masters
    frappe.db.sql("""
        UPDATE `tabAsset Master`
        SET custom_asset_created = 0,
            custom_asset_number = NULL,
            custom_purchase_receipt = NULL,
            custom_pr_date = NULL
        WHERE custom_purchase_receipt = %s
    """, pr_doc.name)
    
    frappe.db.commit()