import frappe

def get_context(context):
    pass

def validate(doc, method=None):
    for item in doc.po_items:
        # ✅ Fixed: use item.item not item.item_code
        if item.dispatch_qty > item.required_qty:
            frappe.throw(
                f"Dispatch Qty ({item.dispatch_qty}) cannot exceed "
                f"Required Qty ({item.required_qty}) for item {item.item}"
            )
        if item.dispatch_qty < 0:
            frappe.throw(f"Dispatch Qty cannot be negative for item {item.item}")