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


# import frappe
# from frappe.utils import today

# @frappe.whitelist()
# def create_purchase_invoice(source_name):
#     source = frappe.get_doc("Supplier Invoice", source_name)


#     if not source.name:
#         frappe.throw("Supplier Invoice No is required")

#     if not source.invoice_date:
#         frappe.throw("Invoice Date is required")

#     #Create Purchase Invoice
#     pi = frappe.new_doc("Purchase Invoice")

#     pi.supplier = source.vendor_id
#     pi.bill_no = source.invoice_no
#     pi.bill_date = source.invoice_date
#     pi.cost_center = source.cost_center
#     pi.plant = source.plant
#     pi.posting_date = today()
#     pi.company = source.company if hasattr(source, "company") else frappe.defaults.get_user_default("Company")

#     #  ITEM MAPPING (MAIN LOGIC)
#     if not source.non_po_items:
#         frappe.throw("No items found in Non PO Items")

#     for row in source.non_po_items:
#         pi.append("items", {
#             "item_code": row.item,
#             "description": row.item,
#             "qty": row.required_qty or 1,
#             "uom": row.uom,
#             "rate": row.rate,
#             "amount": row.amount,
#             # "expense_account": frappe.get_value("Company", pi.company, "default_expense_account"),
#             "cost_center": source.cost_center
#         })

#     # Save
#     #pi.insert(ignore_permissions=True)
#     return pi.as_dict()
#     #return pi.name


@frappe.whitelist()
def create_purchase_invoice(source_name):
    source = frappe.get_doc("Supplier Invoice", source_name)

    if not source.invoice_no:
        frappe.throw("Supplier Invoice No is required")
    if not source.invoice_date:
        frappe.throw("Invoice Date is required")
    if not source.non_po_items:
        frappe.throw("No items found in Non PO Items")

    company = getattr(source, "company", None) or frappe.defaults.get_user_default("Company")

    pi = frappe.new_doc("Purchase Invoice")
    pi.supplier = source.vendor_id
    pi.bill_no = source.invoice_no
    pi.bill_date = source.invoice_date
    pi.posting_date = today()
    pi.company = company
    pi.cost_center = source.cost_center
    if hasattr(source, "plant"):
        pi.plant = source.plant

    for row in source.non_po_items:
        stock_uom = frappe.db.get_value("Item", row.item, "stock_uom") or row.uom
        item_name = frappe.db.get_value("Item", row.item, "item_name") or row.item
        expense_account = frappe.db.get_value(
            "Item Default",
            {"parent": row.item, "company": company},
            "expense_account"
        )
        default_warehouse = frappe.db.get_value(
            "Item Default",
            {"parent": row.item, "company": company},
            "default_warehouse"
        )

        pi.append("items", {
            "item_code": row.item,
            "item_name": item_name,
            "description": item_name,
            "qty": flt(row.required_qty) or 1,
            "uom": stock_uom,
            "stock_uom": stock_uom,
            "conversion_factor": 1,
            "rate": flt(row.rate),
            "amount": flt(row.required_qty) * flt(row.rate),
            "base_rate": flt(row.rate),
            "base_amount": flt(row.required_qty) * flt(row.rate),
            "expense_account": expense_account,
            "warehouse": default_warehouse,
            "cost_center": source.cost_center,
        })

    pi.set_missing_values()          # fills all mandatory fields like expense_account, taxes
    pi.calculate_taxes_and_totals()  # calculates amounts, base amounts

    # return as dict — NOT saved to DB
    return pi.as_dict()