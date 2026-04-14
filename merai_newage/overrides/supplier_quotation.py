# your_app/controllers/supplier_quotation.py

import frappe
from frappe import _ 
from frappe.utils import now_datetime, getdate


def before_save_supplier_quotation(doc, method):
    """Populate ACR from Material Request"""
    
    # Check if created from Material Request
    for item in doc.items:
        if item.material_request:
            mr = frappe.get_doc("Material Request", item.material_request)
            if mr.custom_asset_creation_request:
                doc.custom_asset_creation_request = mr.custom_asset_creation_request
                break
            
    #Set shipment details from RFQ
    set_shipment_details_from_rfq(doc)

def validate_supplier_quotation(doc, method):
    """Validate Supplier Quotation for Asset items"""
    
    if doc.custom_asset_creation_request:
        acr = frappe.get_doc("Asset Creation Request", doc.custom_asset_creation_request)
        
        # Validate items
        # for item in doc.items:
        #     if item.item_code != acr.item:
        #         frappe.throw(_("Row {0}: Item {1} does not match Asset Creation Request").format(
        #             item.idx, item.item_code))
                

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
    
# quotation deadline validation moved to validate event to prevent submission of expired quotations.
def Expire_validate_supplier_quotation(doc, method=None):
    if not doc.custom_request_for_quotation:
        return

    deadline = frappe.db.get_value(
        "Request for Quotation",
        doc.custom_request_for_quotation,
        "custom_quotation_deadline1"
    )

    if deadline and deadline <= now_datetime():
        frappe.throw("This RFQ has expired. You cannot submit quotation.")
        
        
def set_shipment_details_from_rfq(doc, method=None):
    """
    Fetch shipment details from RFQ to Supplier Quotation
    """

    # Avoid overwrite if already set
    if doc.custom_shipment_mode:
        return

    rfq_name = None

    for item in doc.items:
        if item.request_for_quotation:
            rfq_name = item.request_for_quotation
            break

    if not rfq_name:
        return

    rfq = frappe.get_doc("Request for Quotation", rfq_name)

    doc.custom_shipment_mode = rfq.custom_mode_of_shipment
    doc.custom_shipment_type = rfq.custom_shipment_type
    doc.custom_vol_weightkg = rfq.custom_vol_weight
    doc.custom_no_of_pkg_unit = rfq.custom_no_of_pkg_units
    doc.custom_actual_weight = rfq.custom_actual_weights
    doc.custom_pickup_request = rfq.custom_pickup_request
    doc.custom_package_type = rfq.custom_package_type
    doc.custom_port_of_loading = rfq.custom_port_of_loading
    doc.custom_port_of_destination = rfq.custom_port_of_destination
    doc.custom_product_category = rfq.custom_product_category
    doc.custom_eda = rfq.custom_eda
    
    
@frappe.whitelist()
def get_po_numbers(pr_name):
    pr = frappe.get_doc("Pickup Request", pr_name)

    data = []

    for row in pr.purchase_order_details:
        if row.po_number:
            data.append({
                "po_number": row.po_number
            })

    return data


@frappe.whitelist()
def get_po_details(po_name):

    po = frappe.get_doc("Purchase Order", po_name)

    item = po.items[0] if po.items else None

    return {
        "cost_center": po.cost_center, 
        "plant": po.plant
    }