# your_app/controllers/supplier_quotation.py

import frappe
from frappe import _

def before_save_supplier_quotation(doc, method):
    """Populate ACR from Material Request"""
    
    # Check if created from Material Request
    for item in doc.items:
        if item.material_request:
            mr = frappe.get_doc("Material Request", item.material_request)
            if mr.custom_asset_creation_request:
                doc.custom_asset_creation_request = mr.custom_asset_creation_request
                break


def validate_supplier_quotation(doc, method):
    """Validate Supplier Quotation for Asset items"""
    
    if doc.custom_asset_creation_request:
        acr = frappe.get_doc("Asset Creation Request", doc.custom_asset_creation_request)
        
        # Validate items
        # for item in doc.items:
        #     if item.item_code != acr.item:
        #         frappe.throw(_("Row {0}: Item {1} does not match Asset Creation Request").format(
        #             item.idx, item.item_code))
                
                
                
# def assign_ranking_by_rfq(doc):
#     """
#     Auto assign L1–L4 ranking based on base_grand_total (INR)
#     ERPNext v15 safe & optimized
#     """

#     rfq = get_rfq_from_supplier_quotation(doc)
#     if not rfq:
#         return

#     # Fetch all submitted Supplier Quotations
#     quotations = frappe.get_all(
#         "Supplier Quotation",
#         filters={"docstatus": 1},
#         fields=["name", "base_grand_total"]
#     )

#     ranking_data = []

#     for q in quotations:
#         # Fetch RFQ directly from child table (NO get_doc)
#         sq_rfq = frappe.get_value(
#             "Supplier Quotation Item",
#             {"parent": q.name, "request_for_quotation": rfq},
#             "request_for_quotation"
#         )

#         if not sq_rfq:
#             continue

#         ranking_data.append({
#             "name": q.name,
#             "amount": q.base_grand_total or 0
#         })

#     # ❗ Ranking only meaningful if 2+ quotations
#     if len(ranking_data) < 2:
#         return

#     ranking_data.sort(key=lambda x: x["amount"])

#     levels = ["L1", "L2", "L3", "L4"]

#     for idx, row in enumerate(ranking_data):
#         level = levels[idx] if idx < len(levels) else None

#         frappe.db.set_value(
#             "Supplier Quotation",
#             row["name"],
#             {
#                 "custom_ranking_amount": row["amount"],
#                 "custom_ranking": level
#             },
#             update_modified=False  # avoids loop / noise
#         )

def assign_ranking_by_rfq(doc):
    """
    Auto assign L1–L4 ranking based on custom_total_landing_pricecinr
    """

    rfq = get_rfq_from_supplier_quotation(doc)
    if not rfq:
        return

    # Get all Supplier Quotations linked to this RFQ (optimized)
    quotation_names = frappe.get_all(
        "Supplier Quotation Item",
        filters={"request_for_quotation": rfq},
        pluck="parent"
    )

    if not quotation_names:
        return

    quotations = frappe.get_all(
        "Supplier Quotation",
        filters={
            "docstatus": 1,
            "name": ["in", quotation_names]
        },
        fields=["name", "custom_total_landing_pricecinr"]
    )

    ranking_data = []

    for q in quotations:
        ranking_data.append({
            "name": q.name,
            "amount": float(q.custom_total_landing_pricecinr or 0)
        })

    # Ranking only if 2+ quotations
    if len(ranking_data) < 2:
        return

    # Sort by landing price
    ranking_data.sort(key=lambda x: x["amount"])

    # Dynamic ranking (L1, L2, L3...)
    for idx, row in enumerate(ranking_data):
        level = f"L{idx + 1}"

        frappe.db.set_value(
            "Supplier Quotation",
            row["name"],
            {
                "custom_ranking_amount": row["amount"],
                "custom_ranking": level
            },
            update_modified=False
        )
        

def get_rfq_from_supplier_quotation(doc):
    """
    Extract RFQ from Supplier Quotation Items
    """
    for item in doc.items:
        if item.request_for_quotation:
            return item.request_for_quotation
    return None


def on_submit_supplier_quotation(doc, method):
    assign_ranking_by_rfq(doc)