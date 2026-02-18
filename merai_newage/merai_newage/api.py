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
