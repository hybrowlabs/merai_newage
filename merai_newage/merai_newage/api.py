import frappe
from frappe.utils import add_days, today


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
