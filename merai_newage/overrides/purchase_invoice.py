# import frappe
# from frappe import _

# def before_save_purchase_invoice(doc, method):
#     populate_asset_codes(doc)

# def on_submit_purchase_invoice(doc, method):
#     populate_asset_codes(doc)


# def populate_asset_codes(doc):
#     """
#     PI Item has pr_detail = PR Item row name.
#     Asset has purchase_receipt_item = PR Item row name (core ERPNext field).
#     These match directly — exact 1-to-1 per row.
#     """
#     for item in doc.items:
#         if not item.get("pr_detail"):
#             continue

#         if item.get("custom_asset_code"):
#             continue  # already set, skip

#         asset_name = frappe.db.get_value(
#             "Asset",
#             {
#                 "purchase_receipt_item": item.pr_detail,
#                 "docstatus": ["<", 2]
#             },
#             "name"
#         )

#         if asset_name:
#             item.custom_asset = asset_name


# @frappe.whitelist()
# def fetch_asset_codes_for_invoice(purchase_invoice_name):
#     """Manual refresh via button in case PI was saved before assets were created"""
#     doc = frappe.get_doc("Purchase Invoice", purchase_invoice_name)
#     updated = []

#     for item in doc.items:
#         if not item.get("pr_detail"):
#             continue

#         asset_name = frappe.db.get_value(
#             "Asset",
#             {
#                 "purchase_receipt_item": item.pr_detail,
#                 "docstatus": ["<", 2]
#             },
#             "name"
#         )

#         if asset_name:
#             frappe.db.set_value(
#                 "Purchase Invoice Item",
#                 item.name,
#                 "custom_asset",
#                 asset_name,
#                 update_modified=False
#             )
#             updated.append({"row": item.idx, "item": item.item_code, "asset": asset_name})

#     frappe.db.commit()
#     return updated





import frappe
from frappe import _

def before_save_purchase_invoice(doc, method):
    populate_asset_codes(doc)

def on_submit_purchase_invoice(doc, method):
    populate_asset_codes(doc)


def populate_asset_codes(doc):
    """
    For each PI Item:
    - pr_detail = PR Item row name
    - Asset.purchase_receipt_item = PR Item row name
    """

    parent_creation_request = None  # to set in parent

    for item in doc.items:

        if not item.get("pr_detail"):
            continue

        # Fetch complete Asset document
        asset = frappe.get_doc("Asset", {
            "purchase_receipt_item": item.pr_detail,
            "docstatus": ["<", 2]
        }) if frappe.db.exists("Asset", {
            "purchase_receipt_item": item.pr_detail,
            "docstatus": ["<", 2]
        }) else None

        if not asset:
            continue

        # -----------------------------
        # CHILD TABLE UPDATES
        # -----------------------------

        # 1️⃣ Set Asset Name
        if not item.get("custom_asset"):
            item.custom_asset = asset.name

        # 2️⃣ Set Asset Master (field from Asset doctype)
        if not item.get("custom_asset_master"):
            item.custom_asset_master = asset.get("custom_asset_master")

        # -----------------------------
        # PARENT FIELD UPDATE
        # -----------------------------

        if not parent_creation_request:
            parent_creation_request = asset.get("custom_asset_creation_request"
            "")

    # Set parent field once
    if parent_creation_request:
        doc.custom_asset_creation_request = parent_creation_request
