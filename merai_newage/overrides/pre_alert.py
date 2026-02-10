import frappe

def validate_igcr_category(doc, method):
    for item in doc.item_details:
        if item.igcr:
            # Force category 9
            item.category = "9"