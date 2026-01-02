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
