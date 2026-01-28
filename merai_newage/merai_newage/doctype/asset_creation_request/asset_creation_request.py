# Copyright (c) 2025, Siddhant Hybrowlabs and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class AssetCreationRequest(Document):
	pass

import frappe
import random
from frappe.model.document import Document
import frappe
from frappe import _
import json
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
            "asset_owner":"Company",
            "custodian":doc.get('employee'),
            "department":doc.get("department"),
            "asset_count": 1 if is_composite else doc.get("qty"),
            "qty":doc.get("qty"),
            "plant":doc.get("plant"),
            "item_name":frappe.db.get_value("Item",item_code,"item_name"),
            "asset_creation_request":doc.get("name")
        })

        # asset.insert(ignore_permissions=True)
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
def convert_cwip_to_fixed_asset(acr_name):
    '''Update CWIP Asset with total accumulated amount from all PRs'''
    from frappe.utils import flt, get_link_to_form
    
    acr = frappe.get_doc("Asset Creation Request", acr_name)
    
    if not acr.custom_cwip_asset:
        frappe.throw(_("No CWIP Asset found for this ACR"))
    
    if not acr.custom_cwip_purchase_receipts:
        frappe.throw(_("No Purchase Receipts found in ACR"))
    
    # Get CWIP Asset
    cwip_asset = frappe.get_doc("Asset", acr.custom_cwip_asset)
    
    # Calculate totals
    total_amount = sum(flt(row.rate) for row in acr.custom_cwip_purchase_receipts)
    main_items = [r for r in acr.custom_cwip_purchase_receipts if not r.is_service_item]
    service_items = [r for r in acr.custom_cwip_purchase_receipts if r.is_service_item]
    
    main_amount = sum(flt(r.rate) for r in main_items)
    service_amount = sum(flt(r.rate) for r in service_items)
    
    # Update asset amount
    cwip_asset.gross_purchase_amount = total_amount
    cwip_asset.flags.ignore_validate_update_after_submit = True
    cwip_asset.save(ignore_permissions=True)
    
    frappe.db.commit()
    
    return f'''CWIP Asset {cwip_asset.name} updated successfully!<br><br>
              <b>Cost Breakdown:</b><br>
              • Main Asset Items: ₹{main_amount:,.2f} ({len(main_items)} PRs)<br>
              • Service/Additional Items: ₹{service_amount:,.2f} ({len(service_items)} PRs)<br>
              • <b>Total Amount: ₹{total_amount:,.2f}</b><br>
              • <b>Total PRs: {len(acr.custom_cwip_purchase_receipts)}</b><br><br>
              <b>Next Steps:</b><br>
              1. Open Asset: {get_link_to_form("Asset", cwip_asset.name)}<br>
              2. Click <b>"Capitalize Asset"</b> button (core ERPNext feature)<br>
              3. In capitalization form:<br>
              &nbsp;&nbsp;&nbsp;- Change category to regular (non-CWIP) category<br>
              &nbsp;&nbsp;&nbsp;- Set available for use date<br>
              &nbsp;&nbsp;&nbsp;- Enable depreciation<br>
              4. Submit to finalize the asset
           '''
