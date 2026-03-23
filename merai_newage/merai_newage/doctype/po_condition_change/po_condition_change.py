import frappe
from frappe.model.document import Document


class POConditionChange(Document):
    pass


@frappe.whitelist()
def get_boe_all_details(boe_name):
    """
    BOE Entry se full data return karega
    (header + child table)
    """

    # 🔹 Full BOE document fetch
    boe = frappe.get_doc("BOE Entry", boe_name)

    return boe