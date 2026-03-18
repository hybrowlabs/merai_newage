import frappe
import requests
from frappe.utils import add_days, today, flt


def cleanup_temporary_suppliers():
    """
    Delete Temporary suppliers older than configured duration
    if no RFQ exists for them.
    """

    duration = frappe.db.get_single_value(
        "Purchase And Selling Settings", "duration"
    )

    if not duration:
        frappe.logger().info("Duration not set. Skipping supplier cleanup.")
        return

    cutoff_date = add_days(today(), -int(duration))

    suppliers = frappe.get_all(
        "Supplier",
        filters={
            "supplier_status": "Temporary",
            "creation": ("<", cutoff_date)
        },
        pluck="name"
    )

    if not suppliers:
        return

    for supplier in suppliers:
        rfq_exists = frappe.db.exists(
            "Request for Quotation Supplier",
            {"supplier": supplier}
        )

        if not rfq_exists:
            try:
                frappe.delete_doc(
                    "Supplier",
                    supplier,
                    force=True,
                    ignore_permissions=True
                )
                frappe.logger().info(f"Deleted temporary supplier: {supplier}")

            except Exception:
                frappe.log_error(
                    frappe.get_traceback(),
                    f"Failed deleting supplier {supplier}"
                )


@frappe.whitelist()
def get_exchange_rate(from_currency=None, to_currency=None):

    if not from_currency or not to_currency:
        frappe.throw("Both From Currency and To Currency are required.")

    if from_currency == to_currency:
        return 1

    api_key = frappe.conf.get("exchange_api_key")
    if not api_key:
        frappe.throw("Exchange API Key not configured in site_config.json")

    url = f"https://v6.exchangerate-api.com/v6/{api_key}/pair/{from_currency}/{to_currency}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()

        if data.get("result") == "success":
            return flt(data.get("conversion_rate"))

        frappe.log_error(
            message=frappe.as_json(data),
            title="Exchange API Response Error"
        )
        return 0

    except requests.exceptions.RequestException as e:
        frappe.log_error(
            message=str(e),
            title="Exchange Rate API Request Error"
        )
        return 0



# import frappe

# @frappe.whitelist()
# def create_purchase_invoice(source_name):
#     source = frappe.get_doc("Supplier Invoice", source_name)

#     target = frappe.new_doc("Purchase Invoice")

#     target.supplier = source.supplier
#     target.bill_no = source.invoice_no
#     target.bill_date = source.invoice_date
#     target.company = source.company
#     target.cost_center = source.cost_center

#     for item in source.non_po_items:
#         target.append("items", {
#             "item_code": item.item,   # ✅ map correctly
#             "qty": item.required_qty or 1,
#             "rate": item.rate or 0,
#             "amount": item.amount or 0,
#             "cost_center": source.cost_center
#         })

#     target.insert(ignore_permissions=True)

#     return target.name



# import frappe
# from frappe.utils import today

# @frappe.whitelist()
# def create_purchase_invoice(source_name):
#     # Get Supplier Invoice
#     source = frappe.get_doc("Supplier Invoice", source_name)

#     # 🔴 Validation (important)
#     if not source.supplier:
#         frappe.throw("Supplier is required")

#     if not source.invoice_no:
#         frappe.throw("Supplier Invoice No is required")

#     if not source.invoice_date:
#         frappe.throw("Invoice Date is required")

#     # Create Purchase Invoice
#     pi = frappe.new_doc("Purchase Invoice")

#     # ✅ Map fields
#     pi.supplier = source.supplier
#     pi.bill_no = source.name        # Supplier Invoice No
#     pi.bill_date = source.invoice_date    # Supplier Invoice Date
#     pi.cost_center = source.cost_center
#     pi.posting_date = today()

#     # Company (important)
#     pi.company = source.company if hasattr(source, "company") else frappe.defaults.get_user_default("Company")

#     # ⚠️ Mandatory Item (VERY IMPORTANT)
#     pi.append("items", {
#         "item_name": "Service Item",
#         "description": "Auto created from Supplier Invoice",
#         "qty": 1,
#         "rate": source.amount if hasattr(source, "amount") else 100,
#         "expense_account": frappe.get_value("Company", pi.company, "default_expense_account")
#     })

#     # Save document
#     pi.insert(ignore_permissions=True)

#     return pi.name


import frappe
from frappe.utils import today

@frappe.whitelist()
def create_purchase_invoice(source_name):
    source = frappe.get_doc("Supplier Invoice", source_name)


    # if not source.name:
    #     frappe.throw("Supplier Invoice No is required")

    # if not source.invoice_date:
    #     frappe.throw("Invoice Date is required")

    # Create Purchase Invoice
    pi = frappe.new_doc("Purchase Invoice")

    # Header mapping
    pi.supplier = source.vendor_id
    pi.bill_no = source.invoice_no
    pi.bill_date = source.invoice_date
    pi.cost_center = source.cost_center
    pi.plant = source.plant
    pi.posting_date = today()
    pi.company = source.company if hasattr(source, "company") else frappe.defaults.get_user_default("Company")

    #  ITEM MAPPING (MAIN LOGIC)
    if not source.non_po_items:
        frappe.throw("No items found in Non PO Items")

    for row in source.non_po_items:
        pi.append("items", {
            "item_code": row.item,
            "description": row.item,
            "qty": row.required_qty or 1,
            "uom": row.uom,
            "rate": row.rate,
            "amount": row.amount,
            # "expense_account": frappe.get_value("Company", pi.company, "default_expense_account"),
            "cost_center": source.cost_center
        })

    # Save
    pi.insert(ignore_permissions=True)

    return pi.name


# #gate entry
# import frappe
# from frappe.utils import nowdate

# @frappe.whitelist()
# def create_gate_entry(source_name):

#     source = frappe.get_doc("Supplier Invoice", source_name)

#     ge = frappe.new_doc("Gate Entry")

    

#     # HEADER MAPPING
#     ge.supplier = source.vendor_id
#     ge.supplier_name = source.vendor_name

#     ge.bill_number = source.invoice_no
#     ge.bill_date = source.invoice_date

#      # PURCHASE ORDER TABLE FIXED
#     if source.po_number:
#         ge.append("purchase_order_in_gate_entry", {
#             "purchase_order": source.po_number
#         })

#     ge.company = source.company if hasattr(source, "company") else frappe.defaults.get_user_default("Company")
#     ge.gate_entry_date = nowdate()

#     # CHILD TABLE
#     # if not source.po_items:
#     #     frappe.throw("No items found in PO Items")

#     # for row in source.po_items:
#     #     ge.append("supplier_qty_details", {
#     #         "item_code": row.item_code,
#     #         "item_name": row.item_name,
#     #         "qty": row.qty,
#     #         "uom": row.uom
#     #     })

    
#     ge.insert(ignore_permissions=True)

#     return ge.name