# Copyright (c) 2025, Siddhant Hybrowlabs and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class AssetCreationRequest(Document):
	pass

import frappe
import random
from frappe.model.document import Document

@frappe.whitelist()
def create_serial_nos(doc):
    doc = frappe.parse_json(doc)

    item_code = doc.get("item")
    qty = int(doc.get("qty") or 0)
    print("item_code-----",item_code,"qty========",qty)
    if not item_code or qty <= 0:
        frappe.throw("Item Code and Qty are mandatory")

    created_serials = []

    for _ in range(qty):
        serial_no = generate_unique_serial_no()

        serial_doc = frappe.get_doc({
            "doctype": "Serial No",
            "serial_no": serial_no,
            "item_code": item_code,
            "employee":doc.get("employee"),
            "item_group":frappe.db.get_value("Item",item_code,"item_group"),
            # "custom_asset_creation_request_reference":doc.get("name"),
            "status":"Active"
        })
        serial_doc.insert(ignore_permissions=True)

        created_serials.append({
            "item_code": item_code,
            "serial_no": serial_no
        })

    frappe.db.commit()
    return created_serials


def generate_unique_serial_no():
    while True:
        serial_no = str(random.randint(10**9, 10**10 - 1))
        if not frappe.db.exists("Serial No", serial_no):
            return serial_no
