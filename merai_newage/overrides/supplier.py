import frappe

def supplier_quotation_has_website_permission(doc, ptype, user, verbose=False):
    print(doc,ptype,"llllllllllllllllllllllllllllllllllllllllllllllllllllllllll")
    # Allow supplier to edit their own DRAFT quotations
    if ptype == "Supplier":
        if doc.docstatus == 0 and doc.supplier == frappe.db.get_value(
            "User", user, "supplier"
        ):
            return True

    # fallback to default behavior
    return False
