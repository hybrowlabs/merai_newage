


# Copyright (c) 2025, Siddhant Hybrowlabs and contributors
# For license information, please see license.txt

import frappe
import random
from frappe.model.document import Document
from frappe import _
import json
from frappe.utils import nowdate, flt, get_link_to_form, getdate


class AssetCreationRequest(Document):
	pass


@frappe.whitelist()
def create_assets_from_request(doc):
    doc = frappe.parse_json(doc)
    
    item_code = doc.get("item")
    qty = int(doc.get("qty") or 0)
    is_composite = doc.get("composite_item")
    
    asset_count = 1 if is_composite else qty
    
    created_assets = []
    
    for _ in range(asset_count):
        asset = frappe.get_doc({
            "doctype": "Asset Master",
            "item": item_code,
            "asset_category": doc.get("category_of_asset"),
            "company": doc.get("entinty"),
            "location": doc.get("location"),
            "cost_center": doc.get("cost_centre"),
            "purchase_amount_approx": doc.get("approx_cost"),
            "status": "Draft",
            "custom_asset_creation_request": doc.get("name"),
            "asset_owner": "Company",
            "custodian": doc.get('employee'),
            "department": doc.get("department"),
            "asset_count": 1 if is_composite else doc.get("qty"),
            "qty": doc.get("qty"),
            "plant": doc.get("plant"),
            "item_name": frappe.db.get_value("Item", item_code, "item_name"),
            "asset_creation_request": doc.get("name")
        })
        
        asset.flags.ignore_validate = True
        asset.flags.ignore_mandatory = True
        asset.insert(ignore_permissions=True)
        asset.submit()
        created_assets.append({
            "asset_code": asset.name
        })
    
    frappe.db.commit()
    return created_assets


@frappe.whitelist()
def create_composite_erp_asset(acr_name):
    """
    Create a single ERPNext Asset for composite items.
    This asset will be used as the target in Asset Capitalization.
    """
    acr = frappe.get_doc("Asset Creation Request", acr_name)
    
    # Validation: Only for composite items
    if not acr.get("composite_asset"):
        frappe.throw(_("This function is only for composite items. Please check 'Composite Asset' checkbox."))
    
    # Check if asset already exists
    if acr.get("cwip_asset"):
        existing_asset = frappe.db.exists("Asset", acr.cwip_asset)
        if existing_asset:
            frappe.msgprint(
                f"Asset {acr.cwip_asset} already exists for this request.<br>"
                f"<a href='/app/asset/{acr.cwip_asset}'>Open Asset</a>",
                indicator="blue"
            )
            return acr.cwip_asset
    
    # Get target asset item from ACR form field
    target_item_code = acr.get("target_asset_item_code")
    
    if not target_item_code:
        frappe.throw(_("Target Asset Item Code is empty. Please select an item in the Asset Creation Request form."))
    
    # Validate item is a fixed asset
    item_doc = frappe.get_doc("Item", target_item_code)
    if not item_doc.is_fixed_asset:
        frappe.throw(_(f"Item {target_item_code} is not marked as a Fixed Asset. Please update the Item master."))
    
    if not item_doc.asset_category:
        frappe.throw(_(f"Item {target_item_code} does not have an Asset Category assigned. Please update the Item master."))
    
    # Get approximate cost
    approx_cost = flt(acr.get("approx_cost"))
    
    # Get CWIP Asset Category
    cwip_category = frappe.db.get_value(
        "Asset Category",
        {"enable_cwip_accounting": 1},
        "name"
    )
    
    if not cwip_category:
        cwip_category = item_doc.asset_category
        frappe.msgprint(
            _("No CWIP Asset Category found. Using item's asset category: {0}").format(cwip_category),
            indicator="orange"
        )
    
    # Create the Asset
    try:
        asset_doc = frappe.get_doc({
            "doctype": "Asset",
            "item_code": target_item_code,
            "asset_name": item_doc.item_name or target_item_code,
            "asset_category": cwip_category,
            "company": acr.entinty,
            "location": acr.location,
            "cost_center": acr.cost_centre,
            "department": acr.department,
            "custodian": acr.employee,
            "is_composite_asset": 1,
            "gross_purchase_amount": approx_cost,
            "purchase_date": nowdate(),
            "custom_asset_creation_request": acr_name,
            "calculate_depreciation": 0,
            "is_existing_asset": 0,
            "docstatus": 0
        })
        
        asset_doc.flags.ignore_validate = True
        asset_doc.flags.ignore_mandatory = True
        asset_doc.insert(ignore_permissions=True)
        
        # Update ACR with created asset reference
        acr.cwip_asset = asset_doc.name
        acr.flags.ignore_validate_update_after_submit = True
        acr.save(ignore_permissions=True)
        frappe.db.commit()
        
        frappe.msgprint(
            f"✅ <b>Asset Created Successfully!</b><br><br>"
            f"<b>Asset Details:</b><br>"
            f"• Asset Code: {asset_doc.name}<br>"
            f"• Asset Name: {asset_doc.asset_name}<br>"
            f"• Item Code: {target_item_code}<br>"
            f"• Category: {cwip_category}<br>"
            f"• Initial Value: ₹{approx_cost:,.2f}<br><br>"
            f"<a href='/app/asset/{asset_doc.name}'>Open Asset {asset_doc.name}</a>",
            title="Asset Created",
            indicator="green"
        )
        
        return asset_doc.name
        
    except Exception as e:
        frappe.log_error(
            title=f"Failed to create Asset for ACR {acr_name}",
            message=f"Error: {str(e)}\n\nTraceback: {frappe.get_traceback()}"
        )
        frappe.throw(_(f"Failed to create Asset: {str(e)}"))


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_default_warehouse(item_code, company):
    """Get default warehouse for item with fallback logic"""
    wh = frappe.db.get_value(
        "Item Default",
        {"parent": item_code, "company": company},
        "default_warehouse"
    )
    if wh:
        return wh

    wh = frappe.db.get_value(
        "Item Default",
        {"parent": item_code},
        "default_warehouse"
    )
    if wh:
        return wh

    wh = frappe.db.get_value("Company", company, "default_warehouse")
    if wh:
        return wh

    wh = frappe.db.get_value(
        "Warehouse",
        {"company": company, "disabled": 0},
        "name",
        order_by="creation"
    )
    if wh:
        return wh

    return None


def get_default_expense_account(item_code, company):
    """Get default expense account with fallback logic"""
    acc = frappe.db.get_value(
        "Item Default",
        {"parent": item_code, "company": company},
        "expense_account"
    )
    if acc:
        return acc

    acc = frappe.db.get_value(
        "Item Default",
        {"parent": item_code},
        "expense_account"
    )
    if acc:
        return acc

    acc = frappe.db.get_value("Company", company, "default_expense_account")
    if acc:
        return acc

    acc = frappe.db.get_value(
        "Account",
        {
            "company": company,
            "account_type": "Expense Account",
            "is_group": 0,
            "disabled": 0
        },
        "name"
    )
    if acc:
        return acc

    return None


def get_item_flags(item_code):
    """Get item flags to determine if it's a fixed asset or stock item"""
    return frappe.db.get_value(
        "Item",
        item_code,
        ["is_fixed_asset", "is_stock_item"],
        as_dict=True
    ) or {}


def get_cwip_asset_from_acr(acr_name):
    """Get the target CWIP asset from ACR"""
    acr = frappe.get_doc("Asset Creation Request", acr_name)
    
    # First check if cwip_asset field is set
    if acr.get("cwip_asset"):
        if frappe.db.exists("Asset", acr.cwip_asset):
            return acr.cwip_asset
    
    # Fallback: get first asset created from this ACR
    asset = frappe.db.sql(
        """
        SELECT name FROM `tabAsset`
        WHERE custom_asset_creation_request = %s
        ORDER BY creation ASC
        LIMIT 1
        """,
        acr_name,
        as_dict=True
    )
    
    if not asset:
        frappe.throw(
            f"No CWIP Asset found for Asset Creation Request {acr_name}.<br><br>"
            f"Please create the target asset first using 'Create Composite ERP Asset' button."
        )
    
    return asset[0].name

@frappe.whitelist()
def create_assets_from_cwip_prs(acr_name):
    """
    ✅ FIXED: Create Asset documents with proper purchase_receipt_item reference
    """
    acr = frappe.get_doc("Asset Creation Request", acr_name)

    if not acr.custom_cwip_purchase_receipts:
        frappe.throw("No CWIP Purchase Receipts found")

    created_assets = []
    skipped_items = []

    # Process ALL rows in child table
    for pr_row in acr.custom_cwip_purchase_receipts:
        if not pr_row.item_code:
            continue

        item_flags = get_item_flags(pr_row.item_code)

        # Only create assets for FIXED ASSET items
        if not item_flags.get("is_fixed_asset"):
            skipped_items.append({
                "item": pr_row.item_code,
                "reason": "Not a fixed asset (Stock/Service item)"
            })
            print(f"Skipping {pr_row.item_code} - not a fixed asset")
            continue

        # Check if asset already exists
        existing_asset = frappe.db.get_value(
            "Asset",
            {
                "item_code": pr_row.item_code,
                "purchase_receipt": pr_row.purchase_receipt,
                "custom_asset_creation_request": acr_name
            },
            "name"
        )

        if existing_asset:
            print(f"Asset already exists: {existing_asset} for {pr_row.item_code}")
            
            existing_asset_doc = frappe.get_doc("Asset", existing_asset)
            if not existing_asset_doc.available_for_use_date:
                existing_asset_doc.available_for_use_date = pr_row.pr_date or nowdate()
                existing_asset_doc.flags.ignore_validate_update_after_submit = True
                existing_asset_doc.save(ignore_permissions=True)
            print("Updated available_for_use_date for existing asset if it was missing.======",pr_row.amount,"rate=",pr_row.rate)
            created_assets.append({
                "asset_name": existing_asset,
                "item_code": pr_row.item_code,
                "amount": flt(pr_row.amount),
                "rate": flt(pr_row.rate),
                "qty": flt(pr_row.qty),
                "purchase_receipt": pr_row.purchase_receipt,
                "already_exists": True
            })
            continue

        # Get asset category from Item
        asset_category = frappe.db.get_value("Item", pr_row.item_code, "asset_category")

        if not asset_category:
            skipped_items.append({
                "item": pr_row.item_code,
                "reason": "No Asset Category in Item master"
            })
            frappe.msgprint(
                f"⚠️ Item {pr_row.item_code} has no Asset Category. Skipping.",
                indicator="orange"
            )
            continue

        # ✅ Get purchase_receipt_item from PR row or fetch from PR
        purchase_receipt_item = pr_row.get("purchase_receipt_item")
        
        if not purchase_receipt_item:
            # Fallback: Get from Purchase Receipt
            purchase_receipt_item = frappe.db.get_value(
                "Purchase Receipt Item",
                {
                    "parent": pr_row.purchase_receipt,
                    "item_code": pr_row.item_code
                },
                "name"
            )
        
        if not purchase_receipt_item:
            skipped_items.append({
                "item": pr_row.item_code,
                "reason": "Purchase Receipt Item not found"
            })
            frappe.msgprint(
                f"⚠️ Cannot find Purchase Receipt Item for {pr_row.item_code} in {pr_row.purchase_receipt}",
                indicator="red"
            )
            continue

        # Create new Asset
        try:
            asset_doc = frappe.get_doc({
                "doctype": "Asset",
                "item_code": pr_row.item_code,
                "asset_name": frappe.db.get_value("Item", pr_row.item_code, "item_name") or pr_row.item_code,
                "asset_category": asset_category,
                "company": acr.entinty,
                "location": acr.location,
                "cost_center": acr.cost_centre,
                "department": acr.department,
                "custodian": acr.employee,
                "purchase_receipt": pr_row.purchase_receipt,
                "purchase_receipt_item": purchase_receipt_item,  # ✅ CRITICAL: Add this field
                "gross_purchase_amount": flt(pr_row.amount),
                "purchase_date": pr_row.pr_date or nowdate(),
                "available_for_use_date": pr_row.pr_date or nowdate(),
                "custom_asset_creation_request": acr_name,
                "calculate_depreciation": 0,
                "is_existing_asset": 0,
                "docstatus": 0
            })

            asset_doc.flags.ignore_validate = True
            asset_doc.insert(ignore_permissions=True)

            created_assets.append({
                "asset_name": asset_doc.name,
                "item_code": pr_row.item_code,
                "amount": flt(pr_row.amount),
                "rate": flt(pr_row.rate),
                "qty": flt(pr_row.qty),
                "purchase_receipt": pr_row.purchase_receipt,
                "already_exists": False
            })

            print(f"✅ Created Asset {asset_doc.name} for {pr_row.item_code}")
            frappe.msgprint(
                f"✅ Created Asset {asset_doc.name} for {pr_row.item_code} (₹{flt(pr_row.rate):,.2f})",
                indicator="green"
            )

        except Exception as e:
            error_msg = str(e)
            skipped_items.append({
                "item": pr_row.item_code,
                "reason": f"Error: {error_msg}"
            })
            frappe.log_error(
                title=f"Failed to create Asset for {pr_row.item_code}",
                message=f"ACR: {acr_name}\nPR: {pr_row.purchase_receipt}\nError: {error_msg}\n\n{frappe.get_traceback()}"
            )
            frappe.msgprint(
                f"❌ Failed to create asset for {pr_row.item_code}: {error_msg}",
                indicator="red"
            )
            continue

    frappe.db.commit()
    
    # Show summary
    if skipped_items:
        skip_msg = "<br>".join([f"• {item['item']}: {item['reason']}" for item in skipped_items])
        frappe.msgprint(
            f"<b>Skipped Items:</b><br>{skip_msg}",
            title="Items Skipped",
            indicator="orange"
        )
    
    return created_assets

@frappe.whitelist()
def create_asset_capitalization_from_acr(acr_name):
    """
    ✅ FIXED: Create Asset Capitalization from CWIP Purchase Receipts
    With proper child table population for ACR Stock Items and Service Items
    """
    acr = frappe.get_doc("Asset Creation Request", acr_name)

    if not acr.custom_cwip_purchase_receipts:
        frappe.throw("No CWIP Purchase Receipts found")

    # -----------------------------------------------------------------------
    # STEP 1: Get target CWIP Asset
    # -----------------------------------------------------------------------
    target_asset = get_cwip_asset_from_acr(acr.name)
    print(f"Target Asset: {target_asset}")
    target_asset_doc = frappe.get_doc("Asset", target_asset)

    # Target asset must be in Draft
    if target_asset_doc.docstatus == 1:
        frappe.throw(
            f"Target Asset {target_asset} is already submitted. "
            f"Please cancel it first before creating Asset Capitalization.<br><br>"
            f"<a href='/app/asset/{target_asset}'>Open Asset {target_asset}</a>"
        )

    # Mark as composite if needed
    is_composite = acr.get("composite_item") or acr.get("composite_asset")
    if is_composite and not target_asset_doc.is_composite_asset:
        target_asset_doc.is_composite_asset = 1
        target_asset_doc.flags.ignore_validate = True
        target_asset_doc.save(ignore_permissions=True)
        frappe.db.commit()

    # -----------------------------------------------------------------------
    # STEP 2: Create assets for ALL fixed-asset items
    # -----------------------------------------------------------------------
    print("\n" + "="*80)
    print("Creating assets from CWIP PRs...")
    print("="*80)
    
    created_asset_items = create_assets_from_cwip_prs(acr_name)
    print(f"\nCreated {len(created_asset_items)} consumed assets")
    
    for asset in created_asset_items:
        print(f"  - {asset['asset_name']}: {asset['item_code']} (₹{asset['amount']:,.2f})")

    # -----------------------------------------------------------------------
    # STEP 3: Update ACR child tables (Created Assets, Stock Items, Service Items)
    # -----------------------------------------------------------------------
    try:
        # Clear all child tables
        if hasattr(acr, 'custom_created_assets'):
            acr.set("custom_created_assets", [])
        if hasattr(acr, 'acr_stock_items'):
            acr.set("acr_stock_items", [])
        if hasattr(acr, 'acr_service_items'):
            acr.set("acr_service_items", [])

        # Populate Created Assets (Fixed Asset items)
        for asset_item in created_asset_items:
            if hasattr(acr, 'custom_created_assets'):
                acr.append("custom_created_assets", {
                    "asset": asset_item["asset_name"],
                    "item_code": asset_item["item_code"],
                    "amount": asset_item["amount"],
                    "purchase_receipt": asset_item["purchase_receipt"],
                })

        # Populate Stock Items and Service Items from CWIP PR table
        for pr_row in acr.custom_cwip_purchase_receipts:
            if not pr_row.item_code:
                continue

            item_flags = get_item_flags(pr_row.item_code)

            # Stock Items
            if item_flags.get("is_stock_item") and not item_flags.get("is_fixed_asset"):
                if hasattr(acr, 'acr_stock_items'):
                    warehouse = get_default_warehouse(pr_row.item_code, acr.entinty)
                    acr.append("acr_stock_items", {
                        "item_code": pr_row.item_code,
                        "item_name": pr_row.item_name,
                        "qty": pr_row.qty,
                        "rate": pr_row.rate,
                        "amount": pr_row.amount,
                        "purchase_receipt": pr_row.purchase_receipt,
                        "warehouse": warehouse
                    })

            # Service Items
            elif pr_row.is_service_item:
                if hasattr(acr, 'acr_service_items'):
                    expense_account = get_default_expense_account(pr_row.item_code, acr.entinty)
                    acr.append("acr_service_items", {
                        "item_code": pr_row.item_code,
                        "item_name": pr_row.item_name,
                        "qty": pr_row.qty,
                        "rate": pr_row.rate,
                        "amount": pr_row.amount,
                        "purchase_receipt": pr_row.purchase_receipt,
                        "expense_account": expense_account
                    })

        acr.flags.ignore_validate_update_after_submit = True
        acr.save(ignore_permissions=True)
        frappe.db.commit()
        
        print(f"Updated ACR child tables:")
        print(f"  - Created Assets: {len(acr.custom_created_assets) if hasattr(acr, 'custom_created_assets') else 0}")
        print(f"  - Stock Items: {len(acr.acr_stock_items) if hasattr(acr, 'acr_stock_items') else 0}")
        print(f"  - Service Items: {len(acr.acr_service_items) if hasattr(acr, 'acr_service_items') else 0}")
    except Exception as e:
        print(f"Could not save to child tables: {str(e)}")
        frappe.log_error(
            title=f"Failed to update ACR child tables for {acr_name}",
            message=f"Error: {str(e)}\n\nTraceback: {frappe.get_traceback()}"
        )

    # -----------------------------------------------------------------------
    # STEP 4: Build Asset Capitalization document
    # -----------------------------------------------------------------------
    ac = frappe.new_doc("Asset Capitalization")
    ac.company = acr.entinty
    ac.posting_date = nowdate()

    if acr.employee:
        ac.employee = acr.employee

    ac.capitalization_method = "Choose a WIP composite asset"
    ac.target_asset = target_asset
    ac.target_asset_name = target_asset_doc.asset_name
    ac.target_asset_location = target_asset_doc.location
    ac.target_item_code = target_asset_doc.item_code
    ac.target_item_name = target_asset_doc.item_name or frappe.db.get_value(
        "Item", target_asset_doc.item_code, "item_name"
    )
    
    # Get target fixed asset account
    ac.target_fixed_asset_account = frappe.db.get_value(
        "Asset Category Account",
        {
            "parent": target_asset_doc.asset_category,
            "company_name": acr.entinty
        },
        "fixed_asset_account"
    )
    
    ac.total_value = flt(acr.custom_total_cwip_amount)
    
    total_amount = 0
    added_any_row = False

    # -----------------------------------------------------------------------
    # STEP 5: Process ALL rows from CWIP PR child table
    # -----------------------------------------------------------------------
    print("\n" + "="*80)
    print("Processing CWIP PR rows for Asset Capitalization...")
    print("="*80)
    
    for idx, row in enumerate(acr.custom_cwip_purchase_receipts, 1):
        if not row.item_code:
            continue

        item_flags = get_item_flags(row.item_code)
        amount = flt(row.amount)
        qty = flt(row.qty) or 1  # ✅ Get qty from CWIP PR table
        
        print(f"\nRow {idx}: {row.item_code}")
        print(f"  - Is Fixed Asset: {item_flags.get('is_fixed_asset')}")
        print(f"  - Is Stock Item: {item_flags.get('is_stock_item')}")
        print(f"  - Is Service: {row.is_service_item}")
        print(f"  - Qty: {qty}")
        print(f"  - Amount: ₹{amount:,.2f}")

        # --- FIXED ASSET ITEMS → Consumed Assets table ---
        if item_flags.get("is_fixed_asset"):
            # Find the asset we created for this row
            asset_name = None
            for created in created_asset_items:
                if (created["item_code"] == row.item_code and
                    created["purchase_receipt"] == row.purchase_receipt):
                    asset_name = created["asset_name"]
                    break

            if not asset_name:
                print(f"  ⚠️ No created asset found for {row.item_code} / {row.purchase_receipt}")
                continue

            # Safety: never add target asset as consumed
            if asset_name == target_asset:
                print(f"  ⚠️ Skipping target asset: {asset_name}")
                continue

            # Get fixed asset account
            asset_category = frappe.db.get_value("Asset", asset_name, "asset_category")
            fixed_asset_account = frappe.db.get_value(
                "Asset Category Account",
                {
                    "parent": asset_category,
                    "company_name": acr.entinty
                },
                "fixed_asset_account"
            )

            if not fixed_asset_account:
                print(f"  ⚠️ No Fixed Asset Account for category {asset_category}")
                frappe.msgprint(
                    f"No Fixed Asset Account for {asset_category}. Skipping {asset_name}",
                    indicator="orange"
                )
                continue

            print(f"  ✅ Adding to asset_items: {asset_name}")
            ac.append("asset_items", {
                "asset": asset_name,
                "asset_name": frappe.db.get_value("Asset", asset_name, "asset_name"),
                "fixed_asset_account": fixed_asset_account,
                "current_asset_value": amount
            })

            total_amount += amount
            added_any_row = True
            continue

        # --- SERVICE ITEMS → Service Items table ---
        if row.is_service_item:
            expense_account = get_default_expense_account(row.item_code, acr.entinty)

            if not expense_account:
                print(f"  ⚠️ No expense account for service item")
                continue

            print(f"  ✅ Adding to service_items")
            ac.append("service_items", {
                "item_code": row.item_code,
                "expense_account": expense_account,
                "qty": qty,  # ✅ Use qty from CWIP PR table
                "rate": row.rate,
                "amount": row.amount,
                "reference_type": "Purchase Receipt",
                "reference_name": row.purchase_receipt,
                "description": row.item_name or row.item_code
            })

            total_amount += amount
            added_any_row = True
            continue

        # --- STOCK ITEMS → Stock Items table ---
        if item_flags.get("is_stock_item"):
            warehouse = get_default_warehouse(row.item_code, acr.entinty)

            if not warehouse:
                # Fallback: treat as service item
                expense_account = get_default_expense_account(row.item_code, acr.entinty)
                if expense_account:
                    print(f"  ✅ Adding to service_items (no warehouse)")
                    ac.append("service_items", {
                        "item_code": row.item_code,
                        "expense_account": expense_account,
                        "qty": qty,  # ✅ Use qty from CWIP PR table
                        "rate": row.rate,
                        "amount": row.amount,
                        "reference_type": "Purchase Receipt",
                        "reference_name": row.purchase_receipt,
                        "description": f"{row.item_name or row.item_code} (No warehouse)"
                    })
                    total_amount += amount
                    added_any_row = True
                continue

            print(f"  ✅ Adding to stock_items")
            ac.append("stock_items", {
                "item_code": row.item_code,
                "warehouse": warehouse,
                "stock_qty": qty,  # ✅ Use qty from CWIP PR table
                "valuation_rate": amount / qty,  # ✅ Calculate valuation rate properly
                "amount": amount,
                "reference_type": "Purchase Receipt",
                "reference_name": row.purchase_receipt
            })

            total_amount += amount
            added_any_row = True

    if not added_any_row:
        frappe.throw("No valid items found to create Asset Capitalization.")

    # -----------------------------------------------------------------------
    # STEP 6: Set total_cost
    # -----------------------------------------------------------------------
    acr_total = flt(acr.custom_total_cwip_amount)
    if acr_total:
        ac.total_cost = acr_total
        print(f"\ntotal_cost set from ACR: ₹{acr_total:,.2f}")
    else:
        ac.total_cost = total_amount
        print(f"\ntotal_cost set from computed total: ₹{total_amount:,.2f}")

    # -----------------------------------------------------------------------
    # STEP 7: Insert Asset Capitalization
    # -----------------------------------------------------------------------
    try:
        ac.flags.ignore_permissions = True
        ac.flags.ignore_mandatory = False

        ac.insert()
        frappe.db.commit()

        print("\n" + "="*80)
        print(f"✅ Asset Capitalization {ac.name} created successfully!")
        print("="*80)

        frappe.msgprint(
            f"✅ <b>Asset Capitalization {ac.name} created!</b><br><br>"
            f"<b>Items Processed:</b><br>"
            f"• Consumed Assets: {len(ac.asset_items)}<br>"
            f"• Stock Items: {len(ac.stock_items)}<br>"
            f"• Service Items: {len(ac.service_items)}<br>"
            f"• <b>Total Cost: ₹{ac.total_cost:,.2f}</b><br><br>"
            f"Target Asset: {target_asset}<br><br>"
            f"<a href='/app/asset-capitalization/{ac.name}' style='font-weight: bold;'>Open Asset Capitalization {ac.name}</a>",
            title="Success",
            indicator="green"
        )

        return ac.name

    except Exception as e:
        error_message = str(e)
        print(f"\n❌ Failed to create Asset Capitalization: {error_message}")
        frappe.log_error(
            title="Asset Capitalization Failed",
            message=f"ACR: {acr_name}\nError: {error_message}\nTraceback: {frappe.get_traceback()}"
        )
        frappe.throw(f"Failed to create Asset Capitalization: {error_message}")




