

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
#     """Validate PR for asset items and quantity"""
    
#     if doc.custom_asset_creation_request:
#         acr = frappe.get_doc("Asset Creation Request", doc.custom_asset_creation_request)
        
#         # Calculate total PR quantity
#         total_pr_qty = sum(flt(item.qty) for item in doc.items if item.item_code == acr.item)
        
#         # Get total PO quantity for this ACR
#         total_po_qty = 0
#         for item in doc.items:
#             if item.purchase_order:
#                 po = frappe.get_doc("Purchase Order", item.purchase_order)
#                 if po.custom_asset_creation_request == doc.custom_asset_creation_request:
#                     total_po_qty += sum(flt(po_item.qty) for po_item in po.items if po_item.item_code == acr.item)
        
#         # Validate PR qty doesn't exceed PO qty
#         if total_pr_qty > total_po_qty:
#             frappe.throw(_("""Purchase Receipt quantity ({0}) exceeds Purchase Order quantity ({1}) for Asset Creation Request {2}""").format(
#                 total_pr_qty, total_po_qty, doc.custom_asset_creation_request
#             ))
        
#         # Validate items match ACR
#         for item in doc.items:
#             if item.item_code != acr.item:
#                 frappe.throw(_("Row {0}: Item {1} does not match Asset Creation Request Item {2}").format(
#                     item.idx, item.item_code, acr.item))


# def on_submit_purchase_receipt(doc, method):
#     """Create Assets from Asset Masters"""
    
#     if doc.custom_asset_creation_request:
#         create_assets_from_asset_masters(doc)

# def get_asset_cost(am, pr_item, asset_qty):
#     if flt(am.purchase_amount_approx) > 0:
#         return flt(am.purchase_amount_approx)

#     if flt(pr_item.base_rate) > 0:
#         return flt(pr_item.base_rate) * asset_qty

#     return flt(pr_item.amount)

# def create_assets_from_asset_masters(pr_doc):
#     """
#     Create Asset documents from Asset Master based on Purchase Receipt
    
#     Logic:
#     1. Get ACR reference from PR
#     2. Find Asset Masters linked to ACR (not yet converted, with this PO)
#     3. Create Assets based on received quantity
#     4. Update Asset Masters
#     """
    
#     acr_name = pr_doc.custom_asset_creation_request
    
#     # Get Asset Creation Request
#     acr = frappe.get_doc("Asset Creation Request", acr_name)
    
#     # Get PO from PR items
#     po_name = None
#     for item in pr_doc.items:
#         if item.purchase_order:
#             po_name = item.purchase_order
#             break
    
#     # Calculate received quantity
#     total_received = sum(flt(item.qty) for item in pr_doc.items if item.item_code == acr.item)
    
#     # Get Asset Masters that need conversion (linked to this PO)
#     filters = {
#         "asset_creation_request": acr_name,
#         "docstatus": 1,
#         "custom_asset_created": 0
#     }
    
#     if po_name:
#         filters["custom_purchase_order"] = po_name
    
#     asset_masters = frappe.get_all("Asset Master",
#         filters=filters,
#         fields=["name", "item", "item_name", "asset_category", "company", 
#                 "location", "cost_center", "custodian", "department", "plant","qty","bulk_item","asset_count"],
#         order_by="creation asc",
#         limit=int(total_received)  # Only get as many as received
#     )
    
#     print("asset_masters--------", asset_masters)
    
#     if not asset_masters:
#         frappe.msgprint(_("No pending Asset Masters found for Asset Creation Request {0} with PO {1}").format(
#             acr_name, po_name or "N/A"), alert=True, indicator="orange")
#         return []
    
#     if len(asset_masters) < total_received:
#         frappe.msgprint(_("""Warning: Received quantity ({0}) is more than available Asset Masters ({1}).
#             <br>Only {2} assets will be created.""").format(
#             total_received, len(asset_masters), len(asset_masters)
#         ), alert=True, indicator="orange")
    
#     # Get purchase item from PR
#     pr_item = None
#     for item in pr_doc.items:
#         if item.item_code == acr.item:
#             pr_item = item
#             break
    
#     if not pr_item:
#         frappe.throw(_("No matching item found in Purchase Receipt for Asset Creation Request"))
    
#     # Calculate cost per asset
#     # total_assets = len(asset_masters)
#     # cost_per_asset = flt(pr_item.amount) / total_assets if total_assets > 0 else 0

#     cost_per_asset = get_asset_cost(am, pr_item, asset_qty)


    
#     created_assets = []
#     errors = []
#     asset_qty = 1

   

#     # Loop through each Asset Master and create Asset
#     for idx, am in enumerate(asset_masters, 1):
#         try:
#             if cint(am.bulk_item):
#                 asset_qty = cint(am.qty) or 1
#             else:
#                 asset_qty = 1
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
#                 "asset_quantity":asset_qty,
                
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

#             # Submit asset
#             # asset_doc.docstatus = 1
#             # asset_doc.status = "Submitted"
#             # asset_doc.submit()
            
#             created_assets.append(asset_doc.name)
            
#             # Update Asset Master
#             frappe.db.set_value("Asset Master", am.name, {
#                 "custom_asset_created": 1,
#                 "custom_asset_number": asset_doc.name,
#                 "custom_purchase_receipt": pr_doc.name,
#                 "custom_pr_date": pr_doc.posting_date,
#                 # "status": "Active"
#             }, update_modified=False)
            
#             frappe.msgprint(_("✅ Created Asset: {0} from Asset Master: {1}").format(
#                 asset_doc.name, am.name), alert=True, indicator="green")
            
#         except Exception as e:
#             error_msg = _("❌ Error creating asset from Asset Master {0}: {1}").format(am.name, str(e))
#             errors.append(error_msg)
#             frappe.log_error(message=str(e), title=f"Asset Creation Error - {am.name}")
#             frappe.msgprint(error_msg, alert=True, indicator="red")
    
#     # Update Asset Creation Request status
#     if created_assets:
#         # Check if all Asset Masters are converted
#         pending_count = frappe.db.count("Asset Master", {
#             "asset_creation_request": acr_name,
#             "docstatus": 1,
#             "custom_asset_created": 0
#         })
        
#         status = "Completed" if pending_count == 0 else "Partially Completed"
        
#         frappe.db.set_value("Asset Creation Request", acr_name, {
#             # "custom_assets_created": 1,
#             "asset_creation_status": status,
#             # "custom_assets_count": len(created_assets)
#         }, update_modified=False)
    
#     frappe.db.commit()
    
#     # Final summary message
#     if created_assets:
#         frappe.msgprint(
#             _("""<div style='font-size: 14px;'>
#                 <b>🎉 Asset Creation Successful!</b><br><br>
#                 <b>Created {0} Asset(s) from {1} received:</b><br>
#                 {2}
#                 </div>""").format(
#                 len(created_assets),
#                 total_received,
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
#     """Cancel linked Assets when PR is cancelled and revert quantities"""
    
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
        
#         frappe.db.commit()

# import frappe
# from frappe import _
# from frappe.utils import nowdate, flt, cint, get_link_to_form

# def before_save_purchase_receipt(doc, method):
#     """Populate ACR from Purchase Order"""
    
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
        
#         # Skip quantity validation for CWIP as we don't know total PRs upfront
#         if not asset_category.enable_cwip_accounting:
#             # Calculate total PR quantity across all items
#             total_pr_qty = sum(flt(item.qty) for item in doc.items)
            
#             # Get total PO quantity for this ACR
#             total_po_qty = 0
#             for item in doc.items:
#                 if item.purchase_order:
#                     po = frappe.get_doc("Purchase Order", item.purchase_order)
#                     if po.custom_asset_creation_request == doc.custom_asset_creation_request:
#                         total_po_qty += sum(flt(po_item.qty) for po_item in po.items)
            
#             # Validate PR qty doesn't exceed PO qty (only for non-CWIP)
#             if total_pr_qty > total_po_qty:
#                 frappe.throw(_("""Purchase Receipt quantity ({0}) exceeds Purchase Order quantity ({1}) for Asset Creation Request {2}""").format(
#                     total_pr_qty, total_po_qty, doc.custom_asset_creation_request
#                 ))


# def on_submit_purchase_receipt(doc, method):
#     """Create Assets or handle CWIP based on Asset Category"""
    
#     if doc.custom_asset_creation_request:
#         acr = frappe.get_doc("Asset Creation Request", doc.custom_asset_creation_request)
        
#         # Get asset category
#         asset_category = frappe.get_doc("Asset Category", acr.category_of_asset)
        
#         # Check if CWIP is enabled (core field)
#         if asset_category.enable_cwip_accounting:
#             # Handle CWIP flow
#             handle_cwip_purchase_receipt(doc, acr, asset_category)
#         else:
#             # Normal flow - create assets directly
#             create_assets_from_asset_masters(doc)


# def handle_cwip_purchase_receipt(pr_doc, acr, asset_category):
#     """
#     Handle CWIP Purchase Receipt
#     1. Update Asset Master items if not present
#     2. Add PR details to ACR child table
#     3. Create CWIP asset on first PR (or update if exists)
#     """
    
#     acr_name = acr.name
    
#     # Get all PR items (can be multiple items for CWIP - main asset + services)
#     pr_items_data = []
#     total_pr_amount = 0
    
#     for item in pr_doc.items:
#         po_name = item.purchase_order if item.purchase_order else None
        
#         # Add to tracking list
#         pr_items_data.append({
#             "item_code": item.item_code,
#             "item_name": item.item_name,
#             "qty": item.qty,
#             "rate": item.rate,
#             "amount": item.amount,
#             "po_name": po_name,
#             "is_service_item": 1 if item.item_code != acr.item else 0
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
#             "description": f"{pr_item_data['item_name']} - {'Service' if pr_item_data['is_service_item'] else 'Asset'}"
#         })
    
#     # Calculate total accumulated amount from all PRs
#     total_cwip_amount = sum(flt(row.amount) for row in acr.custom_cwip_purchase_receipts)
#     acr.custom_total_cwip_amount = total_cwip_amount
    
#     acr.flags.ignore_validate_update_after_submit = True
#     acr.flags.ignore_permissions = True
#     acr.save()
    
#     # Check if CWIP Asset already exists
#     existing_cwip_asset = frappe.db.get_value("Asset", {
#         "custom_asset_creation_request": acr_name,
#         "is_composite_asset": 1,
#         "docstatus": ["<", 2]
#     })
    
#     if existing_cwip_asset:
#         # Asset already exists - user will update it manually via "Convert to Fixed Asset" button
#         frappe.msgprint(_("""✅ PR added to CWIP ACR!<br><br>
#             <b>Purchase Receipt:</b> {0}<br>
#             <b>PR Amount:</b> ₹{1:,.2f}<br>
#             <b>Total CWIP Accumulated:</b> ₹{2:,.2f}<br>
#             <b>Total PRs:</b> {3}<br><br>
#             <b>CWIP Asset:</b> {4}<br><br>
#             Click <b>"Convert to Fixed Asset"</b> button in ACR to update asset amount.
#         """).format(
#             get_link_to_form("Purchase Receipt", pr_doc.name),
#             total_pr_amount,
#             total_cwip_amount,
#             len(set([row.purchase_receipt for row in acr.custom_cwip_purchase_receipts])),
#             get_link_to_form("Asset", existing_cwip_asset)
#         ), alert=True, indicator="blue")
        
#     else:
#         # First PR - Update Asset Master items and create CWIP Asset
#         update_asset_master_items(pr_doc, acr)
#         cwip_asset = create_cwip_asset(pr_doc, acr, asset_category, total_pr_amount)
        
#         # Update ACR with asset reference
#         acr.custom_cwip_asset = cwip_asset.name
#         acr.flags.ignore_validate_update_after_submit = True
#         acr.save()
        
#         frappe.msgprint(_("""✅ CWIP Asset Created!<br><br>
#             <b>Asset:</b> {0}<br>
#             <b>Initial Amount:</b> ₹{1:,.2f}<br>
#             <b>Status:</b> Composite Asset (Draft)<br><br>
#             <b>Instructions:</b><br>
#             1. Continue creating MR → PO → PR for all related costs<br>
#             2. Each PR will be added to ACR child table<br>
#             3. Use <b>"Convert to Fixed Asset"</b> button to update total amount<br>
#             4. Then use <b>"Capitalize Asset"</b> in Asset to finalize
#         """).format(
#             get_link_to_form("Asset", cwip_asset.name),
#             total_pr_amount
#         ), alert=True, indicator="green")
    
#     frappe.db.commit()


# def update_asset_master_items(pr_doc, acr):
#     """Update Asset Master with item details from PR if not already set"""
    
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
    
#     # Get the main item from PR (first non-service item)
#     main_item = None
#     for pr_item in pr_doc.items:
#         if pr_item.item_code == acr.item:
#             main_item = pr_item
#             break
    
#     if not main_item:
#         # If ACR item not in PR, use first item
#         main_item = pr_doc.items[0] if pr_doc.items else None
    
#     if not main_item:
#         return
    
#     # Update Asset Masters that don't have item set
#     for am in asset_masters:
#         if not am.get("item"):
#             frappe.db.set_value("Asset Master", am.name, {
#                 "item": main_item.item_code,
#                 "item_name": main_item.item_name
#             }, update_modified=False)
            
#             frappe.msgprint(_("Updated Asset Master {0} with item {1}").format(
#                 am.name, main_item.item_code), alert=True, indicator="blue")


# def create_cwip_asset(pr_doc, acr, asset_category, initial_amount):
#     """Create CWIP Asset - Composite Asset that will be capitalized later"""
    
#     initial_amount = 0  # Start with 0, will be updated via "Convert to Fixed Asset"
    
#     # Get Asset Master
#     asset_masters = frappe.get_all("Asset Master",
#         filters={
#             "asset_creation_request": acr.name,
#             "docstatus": 1
#         },
#         fields=["name", "item", "item_name", "company", "location", 
#                 "cost_center", "custodian", "department", "qty", "bulk_item"],
#         limit=1
#     )
    
#     if not asset_masters:
#         frappe.throw(_("No Asset Master found for Asset Creation Request {0}").format(acr.name))
    
#     am = asset_masters[0]
    
#     # If item is not set in Asset Master, get from ACR or PR
#     item_code = am.get("item") or acr.item
#     item_name = am.get("item_name") or acr.item_name
    
#     if not item_code:
#         # Fallback to first item in PR
#         if pr_doc.items:
#             item_code = pr_doc.items[0].item_code
#             item_name = pr_doc.items[0].item_name
    
#     if not item_code:
#         frappe.throw(_("Cannot determine item code for CWIP Asset. Please set item in Asset Master or ACR."))
    
#     # Determine asset quantity
#     asset_qty = 1
#     if cint(am.get("bulk_item")):
#         asset_qty = cint(am.get("qty")) or 1
    
#     # Create CWIP Asset as Composite Asset
#     asset_doc = frappe.get_doc({
#         "doctype": "Asset",
#         "asset_name": f"CWIP-{item_name}-{am['name']}",
#         "item_code": item_code,
#         "asset_category": acr.category_of_asset,
#         "company": am.get("company") or pr_doc.company,
        
#         # Location & Department
#         "location": am.get("location"),
#         "cost_center": am.get("cost_center") or pr_doc.cost_center,
#         "custodian": am.get("custodian"),
#         "department": am.get("department"),
        
#         # Purchase details from first PR
#         "purchase_date": pr_doc.posting_date,
#         "available_for_use_date": pr_doc.posting_date,
#         "gross_purchase_amount": flt(initial_amount),
#         "asset_quantity": asset_qty,
        
#         # CWIP Specific - Mark as Composite Asset
#         "is_composite_asset": 1,
#         "is_existing_asset": 0,
#         "calculate_depreciation": 0,
        
#         # Reference fields
#         "custom_asset_creation_request": acr.name,
#         "custom_asset_master": am["name"],
#     })
    
#     asset_doc.insert(ignore_permissions=True)
    
#     # Update Asset Master
#     frappe.db.set_value("Asset Master", am["name"], {
#         "custom_cwip_asset": asset_doc.name,
#         "asset_status": "CWIP"
#     }, update_modified=False)
    
#     return asset_doc


# def get_asset_cost(am, pr_item, asset_qty):
#     """Calculate asset cost based on purchase amount or rate"""
#     if flt(am.get("purchase_amount_approx", 0)) > 0:
#         return flt(am.purchase_amount_approx)

#     if flt(pr_item.base_rate) > 0:
#         return flt(pr_item.base_rate) * asset_qty

#     return flt(pr_item.amount)


# def create_assets_from_asset_masters(pr_doc):
#     """
#     Create Asset documents from Asset Master based on Purchase Receipt
#     Handles multiple different items in single PR - creates separate assets for each item type
#     """
    
#     acr_name = pr_doc.custom_asset_creation_request
#     acr = frappe.get_doc("Asset Creation Request", acr_name)
    
#     # Get PO from PR items
#     po_name = None
#     for item in pr_doc.items:
#         if item.purchase_order:
#             po_name = item.purchase_order
#             break
    
#     # Group PR items by item_code to handle different items separately
#     pr_items_by_code = {}
#     for item in pr_doc.items:
#         if item.item_code not in pr_items_by_code:
#             pr_items_by_code[item.item_code] = []
#         pr_items_by_code[item.item_code].append(item)
    
#     created_assets = []
#     errors = []
#     total_assets_to_create = sum(int(flt(item.qty)) for item in pr_doc.items)
    
#     # Process each item type separately
#     for item_code, pr_items_list in pr_items_by_code.items():
#         # Calculate quantity for this item type
#         item_qty = sum(flt(item.qty) for item in pr_items_list)
        
#         # Get the PR item for cost calculation
#         pr_item = pr_items_list[0]
        
#         # Get Asset Masters for this specific item that need conversion
#         filters = {
#             "asset_creation_request": acr_name,
#             "docstatus": 1,
#             "custom_asset_created": 0
#         }
        
#         if po_name:
#             filters["custom_purchase_order"] = po_name
        
#         # Get all pending asset masters (we'll filter by item match)
#         all_asset_masters = frappe.get_all("Asset Master",
#             filters=filters,
#             fields=["name", "item", "item_name", "asset_category", "company", 
#                     "location", "cost_center", "custodian", "department", "plant",
#                     "qty", "bulk_item", "asset_count", "purchase_amount_approx"],
#             order_by="creation asc"
#         )
        
#         # Filter asset masters: either matching item or no item set (will be mapped)
#         asset_masters = []
#         unassigned_masters = []
        
#         for am in all_asset_masters:
#             if am.get("item") == item_code:
#                 # Exact match
#                 asset_masters.append(am)
#             elif not am.get("item"):
#                 # No item assigned yet
#                 unassigned_masters.append(am)
        
#         # Calculate how many assets we need for this item
#         assets_needed = int(item_qty)
        
#         # First use exact matches
#         if len(asset_masters) < assets_needed and unassigned_masters:
#             # Assign unassigned masters to this item
#             remaining_needed = assets_needed - len(asset_masters)
#             masters_to_assign = unassigned_masters[:remaining_needed]
            
#             for am in masters_to_assign:
#                 # Update the asset master with this item
#                 frappe.db.set_value("Asset Master", am["name"], {
#                     "item": item_code,
#                     "item_name": pr_item.item_name
#                 }, update_modified=False)
#                 am["item"] = item_code
#                 am["item_name"] = pr_item.item_name
#                 asset_masters.append(am)
                
#                 frappe.msgprint(_("Assigned item {0} to Asset Master {1}").format(
#                     item_code, am["name"]), alert=True, indicator="blue")
        
#         # Limit to required quantity
#         asset_masters = asset_masters[:assets_needed]
        
#         if not asset_masters:
#             frappe.msgprint(_("No Asset Masters available for item {0} (Qty: {1})").format(
#                 item_code, item_qty), alert=True, indicator="orange")
#             continue
        
#         if len(asset_masters) < assets_needed:
#             frappe.msgprint(_("""Warning: Item {0} - Received {1} but only {2} Asset Masters available.
#                 <br>Creating {3} assets.""").format(
#                 item_code, assets_needed, len(asset_masters), len(asset_masters)
#             ), alert=True, indicator="orange")
        
#         # Create assets for this item type
#         for idx, am in enumerate(asset_masters, 1):
#             try:
#                 item_code_to_use = am.get("item") or item_code
#                 item_name_to_use = am.get("item_name") or pr_item.item_name
                
#                 # Determine asset quantity
#                 asset_qty = 1
#                 if cint(am.get("bulk_item")):
#                     asset_qty = cint(am.get("qty")) or 1
                
#                 # Calculate cost per asset
#                 cost_per_asset = get_asset_cost(am, pr_item, asset_qty)
                
#                 # Create Asset document
#                 asset_doc = frappe.get_doc({
#                     "doctype": "Asset",
#                     "asset_name": f"{item_name_to_use}-{am['name']}",
#                     "item_code": item_code_to_use,
#                     "asset_category": am.get("asset_category") or acr.category_of_asset,
#                     "company": am.get("company") or pr_doc.company,
                    
#                     # Location & Department
#                     "location": am.get("location"),
#                     "cost_center": am.get("cost_center") or pr_doc.cost_center,
#                     "custodian": am.get("custodian"),
#                     "department": am.get("department"),
                    
#                     # Purchase details from PR
#                     "purchase_date": pr_doc.posting_date,
#                     "available_for_use_date": pr_doc.posting_date,
#                     "gross_purchase_amount": cost_per_asset,
#                     "purchase_receipt": pr_doc.name,
#                     "purchase_receipt_amount": cost_per_asset,
#                     "supplier": pr_doc.supplier,
#                     "asset_quantity": asset_qty,
                    
#                     # Reference fields
#                     "custom_asset_creation_request": acr_name,
#                     "custom_asset_master": am["name"],
#                     "custom_material_request": pr_item.material_request,
#                     "custom_purchase_order": pr_item.purchase_order,
                    
#                     # Status
#                     "is_existing_asset": 0,
#                     "calculate_depreciation": 0,
#                 })
                
#                 # Insert asset (keep in draft)
#                 asset_doc.flags.ignore_validate = False
#                 asset_doc.insert(ignore_permissions=True)
                
#                 created_assets.append({
#                     "asset": asset_doc.name,
#                     "item": item_code_to_use,
#                     "item_name": item_name_to_use
#                 })
                
#                 # Update Asset Master
#                 frappe.db.set_value("Asset Master", am["name"], {
#                     "custom_asset_created": 1,
#                     "custom_asset_number": asset_doc.name,
#                     "custom_purchase_receipt": pr_doc.name,
#                     "custom_pr_date": pr_doc.posting_date,
#                 }, update_modified=False)
                
#                 frappe.msgprint(_("✅ Created Asset: {0} ({1}) from Asset Master: {2}").format(
#                     asset_doc.name, item_name_to_use, am["name"]), alert=True, indicator="green")
                
#             except Exception as e:
#                 error_msg = _("❌ Error creating asset from Asset Master {0} for item {1}: {2}").format(
#                     am["name"], item_code, str(e))
#                 errors.append(error_msg)
#                 frappe.log_error(message=str(e), title=f"Asset Creation Error - {am['name']}")
#                 frappe.msgprint(error_msg, alert=True, indicator="red")
    
#     # Update Asset Creation Request status
#     if created_assets:
#         pending_count = frappe.db.count("Asset Master", {
#             "asset_creation_request": acr_name,
#             "docstatus": 1,
#             "custom_asset_created": 0
#         })
        
#         status = "Completed" if pending_count == 0 else "Partially Completed"
        
#         frappe.db.set_value("Asset Creation Request", acr_name, {
#             "asset_creation_status": status,
#         }, update_modified=False)
    
#     frappe.db.commit()
    
#     # Final summary message - grouped by item
#     if created_assets:
#         # Group by item for display
#         items_summary = {}
#         for asset_info in created_assets:
#             item = asset_info["item"]
#             if item not in items_summary:
#                 items_summary[item] = {
#                     "item_name": asset_info["item_name"],
#                     "assets": []
#                 }
#             items_summary[item]["assets"].append(asset_info["asset"])
        
#         summary_html = ""
#         for item_code, item_data in items_summary.items():
#             summary_html += f"<br><b>{item_data['item_name']} ({item_code}):</b><br>"
#             summary_html += "<br>".join([f"  • {asset}" for asset in item_data["assets"]])
        
#         frappe.msgprint(
#             _("""<div style='font-size: 14px;'>
#                 <b>🎉 Asset Creation Successful!</b><br><br>
#                 <b>Created {0} Asset(s) from {1} items received:</b>
#                 {2}
#                 </div>""").format(
#                 len(created_assets),
#                 total_assets_to_create,
#                 summary_html
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
    
#     return [asset_info["asset"] for asset_info in created_assets]


# def on_cancel_purchase_receipt(doc, method):
#     """Handle PR cancellation"""
    
#     if doc.custom_asset_creation_request:
#         acr = frappe.get_doc("Asset Creation Request", doc.custom_asset_creation_request)
#         asset_category = frappe.get_doc("Asset Category", acr.category_of_asset)
        
#         if asset_category.enable_cwip_accounting:
#             # Remove PR from ACR child table
#             remove_pr_from_acr(doc, acr)
#         else:
#             # Cancel regular assets
#             cancel_regular_assets(doc)


# def remove_pr_from_acr(pr_doc, acr):
#     """Remove PR entry from ACR child table and recalculate"""
    
#     # Remove all entries for this PR from child table
#     acr.custom_cwip_purchase_receipts = [
#         row for row in acr.custom_cwip_purchase_receipts 
#         if row.purchase_receipt != pr_doc.name
#     ]
    
#     # Recalculate total
#     acr.custom_total_cwip_amount = sum(
#         flt(row.amount) for row in acr.custom_cwip_purchase_receipts
#     )
    
#     acr.flags.ignore_validate_update_after_submit = True
#     acr.flags.ignore_permissions = True
#     acr.save()
    
#     frappe.msgprint(_("Removed PR {0} from ACR. New total: ₹{1:,.2f}").format(
#         pr_doc.name, acr.custom_total_cwip_amount),
#         alert=True, indicator="orange")
    
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
from frappe.utils import nowdate, flt, cint, get_link_to_form

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
                frappe.throw(_("""Purchase Receipt quantity ({0}) exceeds Purchase Order quantity ({1}) for Asset Creation Request {2}""").format(
                    total_pr_qty, total_po_qty, doc.custom_asset_creation_request
                ))


def on_submit_purchase_receipt(doc, method):
    """Create Assets or handle CWIP based on Asset Category"""
    
    if doc.custom_asset_creation_request:
        acr = frappe.get_doc("Asset Creation Request", doc.custom_asset_creation_request)
        
        # Get asset category
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
    For CWIP, we only track PRs in ACR child table
    Asset will be created manually by user via "Create CWIP Asset" button when ready
    
    ERPNext will automatically:
    - Debit CWIP account for asset items
    - Debit Expense account for service items
    - Credit Creditors/Bank account
    """
    
    acr_name = acr.name
    
    # Get all PR items (can be multiple items for CWIP - main asset + services)
    pr_items_data = []
    total_pr_amount = 0
    
    for item in pr_doc.items:
        po_name = item.purchase_order if item.purchase_order else None
        
        # Check if item is a fixed asset item
        item_doc = frappe.get_doc("Item", item.item_code)
        is_asset_item = 1 if item_doc.is_fixed_asset else 0
        
        # Add to tracking list
        pr_items_data.append({
            "item_code": item.item_code,
            "item_name": item.item_name,
            "qty": item.qty,
            "rate": item.rate,
            "amount": item.amount,
            "po_name": po_name,
            "is_service_item": 0 if is_asset_item else 1
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
            "description": f"{pr_item_data['item_name']} - {'Service/Stock' if pr_item_data['is_service_item'] else 'Asset'}"
        })
    
    # Calculate total accumulated amount from all PRs
    total_cwip_amount = sum(flt(row.amount) for row in acr.custom_cwip_purchase_receipts)
    acr.custom_total_cwip_amount = total_cwip_amount
    
    acr.flags.ignore_validate_update_after_submit = True
    acr.flags.ignore_permissions = True
    acr.save()
    
    # Update Asset Masters with items from PR
    update_asset_master_items_cwip(pr_doc, acr)
    
    # Check if CWIP Asset already exists
    existing_cwip_asset = frappe.db.get_value("Asset", {
        "custom_asset_creation_request": acr_name,
        "is_composite_asset": 1,
        "docstatus": ["<", 2]
    })
    
    if existing_cwip_asset:
        # Asset already exists
        frappe.msgprint(_("""✅ PR added to CWIP tracking!<br><br>
            <b>Purchase Receipt:</b> {0}<br>
            <b>PR Amount:</b> ₹{1:,.2f}<br>
            <b>Total CWIP Accumulated:</b> ₹{2:,.2f}<br>
            <b>Total PRs:</b> {3}<br><br>
            <b>Existing CWIP Asset:</b> {4}<br><br>
            <b>Accounting:</b><br>
            - Asset items posted to CWIP account<br>
            - Service items posted to Expense account<br><br>
            <b>Next Steps:</b><br>
            1. Continue creating PRs for all project costs<br>
            2. Update asset amount in Asset doctype when ready<br>
            3. Use <b>"Capitalize CWIP"</b> to convert to Fixed Asset
        """).format(
            get_link_to_form("Purchase Receipt", pr_doc.name),
            total_pr_amount,
            total_cwip_amount,
            len(set([row.purchase_receipt for row in acr.custom_cwip_purchase_receipts])),
            get_link_to_form("Asset", existing_cwip_asset)
        ), alert=True, indicator="blue")
    else:
        # No asset yet - inform user
        frappe.msgprint(_("""✅ PR tracked in CWIP!<br><br>
            <b>Purchase Receipt:</b> {0}<br>
            <b>PR Amount:</b> ₹{1:,.2f}<br>
            <b>Total CWIP Accumulated:</b> ₹{2:,.2f}<br>
            <b>Total PRs:</b> {3}<br><br>
            <b>Accounting:</b><br>
            - Asset items → CWIP account<br>
            - Service items → Expense account<br><br>
            <b>Next Steps:</b><br>
            1. Continue creating PRs for all project costs<br>
            2. When project is ready, go to ACR and use <b>"Create CWIP Asset"</b> button<br>
            3. This will create a composite asset with total accumulated amount<br>
            4. Then use <b>"Capitalize CWIP"</b> in Asset to finalize
        """).format(
            get_link_to_form("Purchase Receipt", pr_doc.name),
            total_pr_amount,
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


def create_assets_from_asset_masters(pr_doc):
    """
    Create Asset documents from Asset Master based on Purchase Receipt
    Handles multiple different items in single PR - creates separate assets for each item type
    """
    
    acr_name = pr_doc.custom_asset_creation_request
    acr = frappe.get_doc("Asset Creation Request", acr_name)
    
    # Get PO from PR items
    po_name = None
    for item in pr_doc.items:
        if item.purchase_order:
            po_name = item.purchase_order
            break
    
    # Group PR items by item_code to handle different items separately
    pr_items_by_code = {}
    for item in pr_doc.items:
        if item.item_code not in pr_items_by_code:
            pr_items_by_code[item.item_code] = []
        pr_items_by_code[item.item_code].append(item)
    
    created_assets = []
    errors = []
    total_assets_to_create = sum(int(flt(item.qty)) for item in pr_doc.items)
    
    # Process each item type separately
    for item_code, pr_items_list in pr_items_by_code.items():
        # Calculate quantity for this item type
        item_qty = sum(flt(item.qty) for item in pr_items_list)
        
        # Get the PR item for cost calculation
        pr_item = pr_items_list[0]
        
        # Get Asset Masters for this specific item that need conversion
        filters = {
            "asset_creation_request": acr_name,
            "docstatus": 1,
            "custom_asset_created": 0
        }
        
        if po_name:
            filters["custom_purchase_order"] = po_name
        
        # Get all pending asset masters (we'll filter by item match)
        all_asset_masters = frappe.get_all("Asset Master",
            filters=filters,
            fields=["name", "item", "item_name", "asset_category", "company", 
                    "location", "cost_center", "custodian", "department", "plant",
                    "qty", "bulk_item", "asset_count", "purchase_amount_approx"],
            order_by="creation asc"
        )
        
        # Filter asset masters: either matching item or no item set (will be mapped)
        asset_masters = []
        unassigned_masters = []
        
        for am in all_asset_masters:
            if am.get("item") == item_code:
                # Exact match
                asset_masters.append(am)
            elif not am.get("item"):
                # No item assigned yet
                unassigned_masters.append(am)
        
        # Calculate how many assets we need for this item
        assets_needed = int(item_qty)
        
        # First use exact matches
        if len(asset_masters) < assets_needed and unassigned_masters:
            # Assign unassigned masters to this item
            remaining_needed = assets_needed - len(asset_masters)
            masters_to_assign = unassigned_masters[:remaining_needed]
            
            for am in masters_to_assign:
                # Update the asset master with this item
                frappe.db.set_value("Asset Master", am["name"], {
                    "item": item_code,
                    "item_name": pr_item.item_name
                }, update_modified=False)
                am["item"] = item_code
                am["item_name"] = pr_item.item_name
                asset_masters.append(am)
                
                frappe.msgprint(_("Assigned item {0} to Asset Master {1}").format(
                    item_code, am["name"]), alert=True, indicator="blue")
        
        # Limit to required quantity
        asset_masters = asset_masters[:assets_needed]
        
        if not asset_masters:
            frappe.msgprint(_("No Asset Masters available for item {0} (Qty: {1})").format(
                item_code, item_qty), alert=True, indicator="orange")
            continue
        
        if len(asset_masters) < assets_needed:
            frappe.msgprint(_("""Warning: Item {0} - Received {1} but only {2} Asset Masters available.
                <br>Creating {3} assets.""").format(
                item_code, assets_needed, len(asset_masters), len(asset_masters)
            ), alert=True, indicator="orange")
        
        # Create assets for this item type
        for idx, am in enumerate(asset_masters, 1):
            try:
                item_code_to_use = am.get("item") or item_code
                item_name_to_use = am.get("item_name") or pr_item.item_name
                
                # Determine asset quantity
                asset_qty = 1
                if cint(am.get("bulk_item")):
                    asset_qty = cint(am.get("qty")) or 1
                
                # Calculate cost per asset
                cost_per_asset = get_asset_cost(am, pr_item, asset_qty)
                
                # Create Asset document
                asset_doc = frappe.get_doc({
                    "doctype": "Asset",
                    "asset_name": f"{item_name_to_use}-{am['name']}",
                    "item_code": item_code_to_use,
                    "asset_category": am.get("asset_category") or acr.category_of_asset,
                    "company": am.get("company") or pr_doc.company,
                    
                    # Location & Department
                    "location": am.get("location"),
                    "cost_center": am.get("cost_center") or pr_doc.cost_center,
                    "custodian": am.get("custodian"),
                    "department": am.get("department"),
                    
                    # Purchase details from PR
                    "purchase_date": pr_doc.posting_date,
                    "available_for_use_date": pr_doc.posting_date,
                    "gross_purchase_amount": cost_per_asset,
                    "purchase_receipt": pr_doc.name,
                    "purchase_receipt_amount": cost_per_asset,
                    "supplier": pr_doc.supplier,
                    "asset_quantity": asset_qty,
                    
                    # Reference fields
                    "custom_asset_creation_request": acr_name,
                    "custom_asset_master": am["name"],
                    "custom_material_request": pr_item.material_request,
                    "custom_purchase_order": pr_item.purchase_order,
                    
                    # Status
                    "is_existing_asset": 0,
                    "calculate_depreciation": 0,
                })
                
                # Insert asset (keep in draft)
                asset_doc.flags.ignore_validate = False
                asset_doc.insert(ignore_permissions=True)
                
                created_assets.append({
                    "asset": asset_doc.name,
                    "item": item_code_to_use,
                    "item_name": item_name_to_use
                })
                
                # Update Asset Master
                frappe.db.set_value("Asset Master", am["name"], {
                    "custom_asset_created": 1,
                    "custom_asset_number": asset_doc.name,
                    "custom_purchase_receipt": pr_doc.name,
                    "custom_pr_date": pr_doc.posting_date,
                }, update_modified=False)
                
                frappe.msgprint(_("✅ Created Asset: {0} ({1}) from Asset Master: {2}").format(
                    asset_doc.name, item_name_to_use, am["name"]), alert=True, indicator="green")
                
            except Exception as e:
                error_msg = _("❌ Error creating asset from Asset Master {0} for item {1}: {2}").format(
                    am["name"], item_code, str(e))
                errors.append(error_msg)
                frappe.log_error(message=str(e), title=f"Asset Creation Error - {am['name']}")
                frappe.msgprint(error_msg, alert=True, indicator="red")
    
    # Update Asset Creation Request status
    if created_assets:
        pending_count = frappe.db.count("Asset Master", {
            "asset_creation_request": acr_name,
            "docstatus": 1,
            "custom_asset_created": 0
        })
        
        status = "Completed" if pending_count == 0 else "Partially Completed"
        
        frappe.db.set_value("Asset Creation Request", acr_name, {
            "asset_creation_status": status,
        }, update_modified=False)
    
    frappe.db.commit()
    
    # Final summary message - grouped by item
    if created_assets:
        # Group by item for display
        items_summary = {}
        for asset_info in created_assets:
            item = asset_info["item"]
            if item not in items_summary:
                items_summary[item] = {
                    "item_name": asset_info["item_name"],
                    "assets": []
                }
            items_summary[item]["assets"].append(asset_info["asset"])
        
        summary_html = ""
        for item_code, item_data in items_summary.items():
            summary_html += f"<br><b>{item_data['item_name']} ({item_code}):</b><br>"
            summary_html += "<br>".join([f"  • {asset}" for asset in item_data["assets"]])
        
        frappe.msgprint(
            _("""<div style='font-size: 14px;'>
                <b>🎉 Asset Creation Successful!</b><br><br>
                <b>Created {0} Asset(s) from {1} items received:</b>
                {2}
                </div>""").format(
                len(created_assets),
                total_assets_to_create,
                summary_html
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
    
    return [asset_info["asset"] for asset_info in created_assets]


def on_cancel_purchase_receipt(doc, method):
    """Handle PR cancellation"""
    
    if doc.custom_asset_creation_request:
        acr = frappe.get_doc("Asset Creation Request", doc.custom_asset_creation_request)
        asset_category = frappe.get_doc("Asset Category", acr.category_of_asset)
        
        if asset_category.enable_cwip_accounting:
            # Remove PR from ACR child table
            # ERPNext will automatically reverse GL entries
            remove_pr_from_acr(doc, acr)
        else:
            # Cancel regular assets
            cancel_regular_assets(doc)


def remove_pr_from_acr(pr_doc, acr):
    """Remove PR entry from ACR child table and recalculate"""
    
    # Remove all entries for this PR from child table
    acr.custom_cwip_purchase_receipts = [
        row for row in acr.custom_cwip_purchase_receipts 
        if row.purchase_receipt != pr_doc.name
    ]
    
    # Recalculate total
    acr.custom_total_cwip_amount = sum(
        flt(row.amount) for row in acr.custom_cwip_purchase_receipts
    )
    
    acr.flags.ignore_validate_update_after_submit = True
    acr.flags.ignore_permissions = True
    acr.save()
    
    frappe.msgprint(_("Removed PR {0} from ACR. New total: ₹{1:,.2f}<br>GL entries reversed automatically.").format(
        pr_doc.name, acr.custom_total_cwip_amount),
        alert=True, indicator="orange")
    
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