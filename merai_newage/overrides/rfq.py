import frappe
from frappe import _


def validate_request_for_quotation(doc, method):
    """Validate RFQ for asset items"""

    if doc.custom_asset_creation_request:
        acr = frappe.get_doc(
            "Asset Creation Request", doc.custom_asset_creation_request
        )

        # Validate items match ACR
        for item in doc.items:
            if item.material_request:
                mr_item_code = frappe.db.get_value(
                    "Material Request Item",
                    {"parent": item.material_request},
                    "item_code",
                )
                if mr_item_code != acr.item:
                    frappe.throw(
                        _(
                            "Row {0}: Item {1} does not match Asset Creation Request"
                        ).format(item.idx, item.item_code)
                    )


def before_save_request_for_quotation(doc, method):
    """Populate ACR from Material Request"""

    # Get ACR from linked Material Requests
    for item in doc.items:
        if item.material_request:
            mr = frappe.get_doc("Material Request", item.material_request)
            if mr.custom_asset_creation_request:
                doc.custom_asset_creation_request = mr.custom_asset_creation_request
                break


def validate_request_for_quotation(doc, method):
    """Validate RFQ for asset items"""

    if doc.custom_asset_creation_request:
        acr = frappe.get_doc(
            "Asset Creation Request", doc.custom_asset_creation_request
        )

        # Validate items match ACR
        for item in doc.items:
            if item.material_request:
                mr_item_code = frappe.db.get_value(
                    "Material Request Item",
                    {"parent": item.material_request},
                    "item_code",
                )
                # if mr_item_code != acr.item:
                #     frappe.throw(_("Row {0}: Item {1} does not match Asset Creation Request").format(
                #         item.idx, item.item_code))


@frappe.whitelist()
def revise_rfq(rfq_name: str):

    rfq = frappe.get_doc("Request for Quotation", rfq_name)

    if rfq.docstatus != 1:
        frappe.throw("Only Submitted RFQ can be revised.")

    original_rfq = rfq.custom_original_rfq or rfq.name

    # Count how many revisions already exist
    revision_count = frappe.db.count(
        "Request for Quotation", {"custom_original_rfq": original_rfq}
    )

    new_revision_no = revision_count + 1

    rfq_number_part = original_rfq.split("-")[-1]

    revision_code = f"PUR-RFQ-REV-{rfq_number_part}-001"

    new_rfq = frappe.copy_doc(rfq)
    new_rfq.docstatus = 0
    new_rfq.status = "Draft"

    new_rfq.custom_original_rfq = original_rfq
    new_rfq.custom_revision_no = new_revision_no
    new_rfq.custom_revision_code = revision_code

    new_rfq.insert(ignore_permissions=True)

    # Update original RFQ revision count
    frappe.db.set_value(
        "Request for Quotation",
        original_rfq,
        {"custom_revision_no": new_revision_no, "custom_revision_code": revision_code},
    )

    return new_rfq.name


@frappe.whitelist()
def get_rfq_revisions(rfq_name):

    rfq = frappe.get_doc("Request for Quotation", rfq_name)

    original = rfq.custom_original_rfq or rfq.name

    revisions = frappe.get_all(
        "Request for Quotation",
        filters={"custom_original_rfq": original},
        fields=["name", "custom_revision_no", "custom_revision_code", "creation"],
        order_by="custom_revision_no asc",
    )

    return {"original_rfq": original, "revisions": revisions}

import frappe
from frappe.utils import get_url
@frappe.whitelist()
def send_supplier_quotation_to_supplier(doc, method):
    mail_to_supplier_for_logisitics = frappe.db.get_single_value("Purchase And Selling Settings", "mail_to_supplier_for_logisitics")
    print("is_mail_required========",mail_to_supplier_for_logisitics)
    if mail_to_supplier_for_logisitics and doc.custom_type == "Logistics":
        for supplier_row in doc.suppliers:
            supplier_email = None

            # 1. Try direct email on Supplier master
            supplier_email = frappe.db.get_value(
                "Supplier", supplier_row.supplier, "email_id"
            )

            # 2. Fallback: get email via Contact → Dynamic Link
            if not supplier_email:
                contact_name = frappe.db.get_value("Dynamic Link", {
                    "parenttype": "Contact",
                    "link_doctype": "Supplier",
                    "link_name": supplier_row.supplier
                }, "parent")

                if contact_name:
                    supplier_email = frappe.db.get_value(
                        "Contact", contact_name, "email_id"
                    )

            if supplier_email:
                form_url = "{}/supplier-quotation-logistics/new?rfq={}&supplier={}".format(
                    frappe.utils.get_url(),
                    doc.name,
                    supplier_row.supplier
                )

                items_html = _build_items_table_html(doc.items)

                frappe.sendmail(
                    recipients=[supplier_email],
                    subject="Request for Quotation - {} | {}".format(
                        doc.name, doc.company
                    ),
                    message="""
                        <p>Dear {},</p>
                        <p>We request you to submit your quotation for the following items:</p>
                        {}
                        <p>Please click the link below to submit your quotation:</p>
                        <p><a href="{}" style="padding:10px 20px;background:#4CAF50;
                           color:white;text-decoration:none;border-radius:4px;">
                           Submit Quotation</a></p>
                        <br/>
                        <p>Company: {}</p>
                        <p>RFQ Reference: {}</p>
                        <br/>
                        <p>Regards,<br/>{}</p>
                    """.format(
                        supplier_row.supplier_name or supplier_row.supplier,
                        items_html,
                        form_url,
                        doc.company,
                        doc.name,
                        doc.company
                    )
                )
                frappe.msgprint(
                    "Email sent to {} ({})".format(
                        supplier_row.supplier, supplier_email
                    ), 
                    alert=True
                )
            else:
                frappe.msgprint(
                    "No email found for supplier: {}".format(supplier_row.supplier),
                    alert=True,
                    indicator="orange"
                )


def _build_items_table_html(items):
    rows = ""
    for item in items:
        rows += """
            <tr>
                <td style="border:1px solid #ddd;padding:8px">{}</td>
                <td style="border:1px solid #ddd;padding:8px">{}</td>
                <td style="border:1px solid #ddd;padding:8px">{}</td>
                <td style="border:1px solid #ddd;padding:8px">{}</td>
            </tr>
        """.format(
            item.item_code,
            item.item_name or "",
            item.qty,
            item.uom or ""
        )

    return """
        <table style="border-collapse:collapse;width:100%;margin:15px 0">
            <thead>
                <tr style="background:#f2f2f2">
                    <th style="border:1px solid #ddd;padding:8px;text-align:left">Item Code</th>
                    <th style="border:1px solid #ddd;padding:8px;text-align:left">Item Name</th>
                    <th style="border:1px solid #ddd;padding:8px;text-align:left">Quantity</th>
                    <th style="border:1px solid #ddd;padding:8px;text-align:left">UOM</th>
                </tr>
            </thead>
            <tbody>{}</tbody>
        </table>
    """.format(rows)