import frappe
from frappe.utils import add_days, today

@frappe.whitelist()
def cleanup_temporary_suppliers():
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
            "custom_supplier_status": "Temporary",
            "disabled": 0
        },
        pluck="name"
    )

    if not suppliers:
        return

    for supplier in suppliers:
        recent_rfq_exists = frappe.db.exists(
            "Request for Quotation Supplier",
            {
                "supplier": supplier,
                "creation": (">=", cutoff_date)
            }
        )

        if not recent_rfq_exists:
            try:
                supplier_doc = frappe.get_doc("Supplier", supplier)
                supplier_doc.disabled = 1
                supplier_doc.custom_supplier_status = "Expired"
                supplier_doc.flags.ignore_permissions = True
                supplier_doc.save()

                frappe.logger().info(
                    f"Disabled temporary supplier {supplier} (no RFQ in last {duration} days)"
                )

            except Exception:
                frappe.log_error(
                    frappe.get_traceback(),
                    f"Failed disabling supplier {supplier}"
                )

    frappe.db.commit()
