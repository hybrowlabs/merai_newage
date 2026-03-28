import frappe

def validate_igcr_category(doc, method):
    for item in doc.item_details:
        if item.igcr:
            # Force category 9
            item.category = "9"
            

@frappe.whitelist()
def get_latest_supplier_quotation(rfq, supplier=None):
    if not rfq:
        return None

    filters = {
        "request_for_quotation": rfq,
    }

    if supplier:
        filters["supplier"] = supplier

    sq = frappe.get_all(
        "Supplier Quotation",
        filters=filters,
        fields=["name"],
        order_by="`tabSupplier Quotation`.creation desc", # latest first
        limit=1
    )

    return sq[0].name if sq else None