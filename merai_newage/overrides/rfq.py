import frappe
from frappe import _
from frappe.utils import now_datetime, get_datetime,get_url


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

# @frappe.whitelist()
# def send_supplier_quotation_to_supplier(doc, method):
#     mail_to_supplier_for_logisitics = frappe.db.get_single_value("Purchase And Selling Settings", "mail_to_supplier_for_logisitics")
#     print("is_mail_required========",mail_to_supplier_for_logisitics)
#     if mail_to_supplier_for_logisitics and doc.custom_type == "Logistics":
#         for supplier_row in doc.suppliers:
#             supplier_email = None

#             # 1. Try direct email on Supplier master
#             supplier_email = frappe.db.get_value(
#                 "Supplier", supplier_row.supplier, "email_id"
#             )

#             # 2. Fallback: get email via Contact → Dynamic Link
#             if not supplier_email:
#                 contact_name = frappe.db.get_value("Dynamic Link", {
#                     "parenttype": "Contact",
#                     "link_doctype": "Supplier",
#                     "link_name": supplier_row.supplier
#                 }, "parent")

#                 if contact_name:
#                     supplier_email = frappe.db.get_value(
#                         "Contact", contact_name, "email_id"
#                     )

#             if supplier_email:
#                 form_url = "{}/supplier-quotation-logistics/new?rfq={}&supplier={}".format(
#                     frappe.utils.get_url(),
#                     doc.name,
#                     supplier_row.supplier
#                 )

#                 items_html = _build_items_table_html(doc.items)

#                 frappe.sendmail(
#                     recipients=[supplier_email],
#                     subject="Request for Quotation - {} | {}".format(
#                         doc.name, doc.company
#                     ),
#                     message="""
#                         <p>Dear Sir/Madam,</p>

#                         <p>Kindly arrange to pickup the shipment as per the details given below.</p>

#                         <table style="border-collapse:collapse;width:700px;font-family:Calibri;font-size:14px" border="1" cellpadding="6">
#                             <tr><td><b>RFQ Reference Number</b></td><td>{}</td></tr>
#                             <tr><td><b>RFQ Date</b></td><td>{}</td></tr>
#                             <tr><td><b>Freight Forwarder</b></td><td>{}</td></tr>
#                             <tr><td><b>FF Ref No</b></td><td>{}</td></tr>
#                             <tr><td><b>Frieght Mode</b></td><td>{}</td></tr>
#                             <tr><td><b>Origin Country</b></td><td>{}</td></tr>
#                             <tr><td><b>Destination Port</b></td><td>{}</td></tr>
#                             <tr><td><b>Port Code</b></td><td>{}</td></tr>
#                             <tr><td><b>Freight Basis</b></td><td>{}</td></tr>
#                             <tr><td><b>Meril Invoice No</b></td><td>{}</td></tr>
#                             <tr><td><b>Invoice Date</b></td><td>{}</td></tr>
#                             <tr><td><b>Shipper Name</b></td><td>{}</td></tr>
#                             <tr><td><b>Shipment Type</b></td><td>{}</td></tr>
#                             <tr><td><b>Package Type</b></td><td>{}</td></tr>
#                             <tr><td><b>PKG Units</b></td><td>{}</td></tr>
#                             <tr><td><b>Product Category</b></td><td>{}</td></tr>
#                             <tr><td><b>Vol Weight</b></td><td>{}</td></tr>
#                             <tr><td><b>Actual Weight (Kg)</b></td><td>{} Kg</td></tr>
#                             <tr><td><b>Shipment Date Meril</b></td><td>{} Kg</td></tr>
#                             <tr><td><b>Consignee Name</b></td><td>{}</td></tr>
#                             <tr><td><b>Remarks</b></td><td>{}</td></tr>
#                             <tr><td><b>Meril Contact Person</b></td><td>{}</td></tr>
#                         </table>

#                         <br/>

#                         <p>We request you to submit your quotation for the following items:</p>

#                         {}

#                         <p>Please click the link below to submit your quotation:</p>

#                         <p>
#                             <a href="{}" style="padding:10px 20px;background:#4CAF50;
#                                 color:white;text-decoration:none;border-radius:4px;">
#                                 Submit Quotation
#                             </a>
#                         </p>

#                         <br/>

#                         <p>Thanking you,</p>

#                         <br/>

#                         <p><b>{}</b><br/>
#                         Meril Supply Chain (EXIM)</p>
#                         """.format(
#                             rfq=doc.name,
#                             rfq_date=doc.transaction_date,
#                             ff=doc.custom_adhoc_partner or "",
#                             ff_ref=doc.custom_pickup_request or "",
#                             mode=doc.custom_mode_of_shipment or "",
#                             country=doc.custom_country or "",
#                             port=doc.custom_port_of_loading or "",
#                             port_code=doc.custom_port_code or "",
#                             incoterm=doc.incoterm or "",
#                             invoice=doc.custom_supplier_purchase_invoice_no or "",
#                             invoice_date=doc.custom_invoice_date or "",
#                             shipper=doc.custom_pickup_supplier_name or "",
#                             shipment_type=doc.custom_shipment_type or "",
#                             package_type=doc.custom_package_type or "",
#                             pkg_units=doc.custom_no_of_pkg_units or "",
#                             category=doc.custom_product_category or "",
#                             vol_weight=doc.custom_vol_weight or 0,
#                             actual_weight=doc.custom_actual_weights or 0,
#                             shipment_date=doc.custom_shipment_date or "",
#                             consignee=doc.custom_shipment_address_details or "",
#                             remarks=doc.custom_remarks or "",
#                             contact="Binita Panchal",
#                         )
#                 )
#                 frappe.msgprint(
#                     "Email sent to {} ({})".format(
#                         supplier_row.supplier, supplier_email
#                     ), 
#                     alert=True
#                 )
#             else:
#                 frappe.msgprint(
#                     "No email found for supplier: {}".format(supplier_row.supplier),
#                     alert=True,
#                     indicator="orange"
#                 )

@frappe.whitelist()
def send_supplier_quotation_to_supplier(doc, method):
    is_enabled = frappe.db.get_single_value(
        "Purchase And Selling Settings",
        "mail_to_supplier_for_logisitics"
    )

    if not (is_enabled and doc.custom_type == "Logistics"):
        return

    for supplier_row in doc.suppliers:
        supplier_email = None

        # ----------------------------
        # 1. Direct email from Supplier
        # ----------------------------
        supplier_email = frappe.db.get_value(
            "Supplier",
            supplier_row.supplier,
            "email_id"
        )

        # ----------------------------
        # 2. Fallback → Contact
        # ----------------------------
        if not supplier_email:
            contact_name = frappe.db.get_value(
                "Dynamic Link",
                {
                    "parenttype": "Contact",
                    "link_doctype": "Supplier",
                    "link_name": supplier_row.supplier,
                },
                "parent",
            )

            if contact_name:
                supplier_email = frappe.db.get_value(
                    "Contact", contact_name, "email_id"
                )

        if not supplier_email:
            frappe.msgprint(
                f"No email found for supplier: {supplier_row.supplier}",
                indicator="orange",
                alert=True,
            )
            continue

        # ----------------------------
        # URL
        # ----------------------------
        form_url = "{}/supplier-quotation-logistics/new?rfq={}&supplier={}".format(
            frappe.utils.get_url(),
            doc.name,
            supplier_row.supplier,
        )

        # ----------------------------
        # Items Table
        # ----------------------------
        items_html = _build_items_table_html(doc.items)

        # ----------------------------
        # Email Message (FIXED)
        # ----------------------------
        message = f"""
        <p>Dear Sir/Madam,</p>

        <p>Kindly arrange to pickup the shipment as per the details given below.</p>

        <table style="border-collapse:collapse;width:700px;font-family:Calibri;font-size:14px" border="1" cellpadding="6">
            <tr><td><b>RFQ Reference Number</b></td><td>{doc.name}</td></tr>
            <tr><td><b>RFQ Date</b></td><td>{doc.transaction_date}</td></tr>
            <tr><td><b>Freight Forwarder</b></td><td>{supplier_row.supplier_name or supplier_row.supplier}</td></tr>
            <tr><td><b>FF Ref No</b></td><td>{doc.custom_pickup_request or ""}</td></tr>
            <tr><td><b>Freight Mode</b></td><td>{doc.custom_mode_of_shipment or ""}</td></tr>
            <tr><td><b>Origin Country</b></td><td>{doc.custom_country or ""}</td></tr>
            <tr><td><b>Destination Port</b></td><td>{doc.custom_port_of_loading or ""}</td></tr>
            <tr><td><b>Port Code</b></td><td>{doc.custom_port_code or ""}</td></tr>
            <tr><td><b>Freight Basis</b></td><td>{doc.incoterm or ""}</td></tr>
            <tr><td><b>Meril Invoice No</b></td><td>{doc.custom_supplier_purchase_invoice_no or ""}</td></tr>
            <tr><td><b>Invoice Date</b></td><td>{doc.custom_invoice_date or ""}</td></tr>
            <tr><td><b>Shipper Name</b></td><td>{doc.custom_pickup_supplier_name or ""}</td></tr>
            <tr><td><b>Shipment Type</b></td><td>{doc.custom_shipment_type or ""}</td></tr>
            <tr><td><b>Package Type</b></td><td>{doc.custom_package_type or ""}</td></tr>
            <tr><td><b>PKG Units</b></td><td>{doc.custom_no_of_pkg_units or ""}</td></tr>
            <tr><td><b>Product Category</b></td><td>{doc.custom_product_category or ""}</td></tr>
            <tr><td><b>Vol Weight</b></td><td>{doc.custom_vol_weight or 0}</td></tr>
            <tr><td><b>Actual Weight (Kg)</b></td><td>{doc.custom_actual_weights or 0} Kg</td></tr>
            <tr><td><b>Shipment Date Meril</b></td><td>{doc.custom_shipment_date or ""}</td></tr>
            <tr><td><b>Consignee Name</b></td><td>{doc.custom_consinee_name or ""}</td></tr>
            <tr><td><b>Remarks</b></td><td>{doc.custom_remarks or ""}</td></tr>
            <tr><td><b>Meril Contact Person</b></td><td>Binita Panchal</td></tr>
        </table>
    
        <br/>

        <p>We request you to submit your quotation for the following items:</p>

        {items_html}

        <p>Please click the link below to submit your quotation:</p>

        <p>
            <a href="{form_url}" style="padding:10px 20px;background:#4CAF50;
                color:white;text-decoration:none;border-radius:4px;">
                Submit Quotation
            </a>
        </p>

        <br/>

        <p>Thanking you,</p>

        <br/>

        <p><b>{doc.company}</b><br/>
        Meril Supply Chain (EXIM)</p>
        """

        # ----------------------------
        # Send Email
        # ----------------------------
        frappe.sendmail(
            recipients=[supplier_email],
            subject=f"Request for Quotation - {doc.name} | {doc.company}",
            message=message,
        )

        frappe.msgprint(
            f"Email sent to {supplier_row.supplier} ({supplier_email})",
            alert=True,
        )
        
def _build_items_table_html(items):
    rows = ""
    for item in items:
        rows += """
            <tr>
                <td style="border:1px solid #ddd;padding:8px">{}</td>
                <td style="border:1px solid #ddd;padding:8px">{}</td>
            </tr>
        """.format(
            item.item_code,
            item.item_name or "",
        )

    return """
        <table style="border-collapse:collapse;width:100%;margin:15px 0">
            <thead>
                <tr style="background:#f2f2f2">
                    <th style="border:1px solid #ddd;padding:8px;text-align:left">Item Code</th>
                    <th style="border:1px solid #ddd;padding:8px;text-align:left">Item Name</th>
                </tr>
            </thead>
            <tbody>{}</tbody>
        </table>
    """.format(rows)
    
# def _build_items_table_html(items):
#     rows = ""
#     for item in items:
#         rows += """
#             <tr>
#                 <td style="border:1px solid #ddd;padding:8px">{}</td>
#                 <td style="border:1px solid #ddd;padding:8px">{}</td>
#                 <td style="border:1px solid #ddd;padding:8px">{}</td>
#                 <td style="border:1px solid #ddd;padding:8px">{}</td>
#                 <td style="border:1px solid #ddd;padding:8px">{}</td>
#             </tr>
#         """.format(
#             item.item_code,
#             item.item_name or "",
#             item.qty,
#             item.custom_rate,
#             item.uom or ""
#         )

#     return """
#         <table style="border-collapse:collapse;width:100%;margin:15px 0">
#             <thead>
#                 <tr style="background:#f2f2f2">
#                     <th style="border:1px solid #ddd;padding:8px;text-align:left">Item Code</th>
#                     <th style="border:1px solid #ddd;padding:8px;text-align:left">Item Name</th>
#                     <th style="border:1px solid #ddd;padding:8px;text-align:left">Quantity</th>
#                     <th style="border:1px solid #ddd;padding:8px;text-align:left">Rate</th>
#                     <th style="border:1px solid #ddd;padding:8px;text-align:left">UOM</th>
#                 </tr>
#             </thead>
#             <tbody>{}</tbody>
#         </table>
#     """.format(rows)


@frappe.whitelist(allow_guest=True)
def check_auction_eligibility(rfq, supplier):
    """
    Check if supplier is eligible to submit/revise quotation.
    Returns: { eligible: bool, is_last_hour: bool, has_existing_bid: bool, message: str }
    """
    rfq_doc = frappe.get_doc("Request for Quotation", rfq)
    deadline = get_datetime(rfq_doc.custom_quotation_deadline1)
    now = now_datetime()

    diff_seconds = (deadline - now).total_seconds()

    # Auction already closed
    if diff_seconds <= 0:
        return {
            "eligible": False,
            "is_last_hour": False,
            "has_existing_bid": False,
            "message": "Auction has closed. No more submissions allowed."
        }

    is_last_hour = diff_seconds <= 3600  # last 60 minutes

    # Check if supplier has already submitted a bid
    existing_bid = frappe.db.exists("Supplier Quotation", {
        "quotation_number": rfq,
        "supplier": supplier,
        "docstatus": ["in", [0, 1]]  # draft or submitted
    })
    print("existing_bid=======261",existing_bid)

    has_existing_bid = bool(existing_bid)

    # Last hour restriction
    if is_last_hour and not has_existing_bid:
        return {
            "eligible": False,
            "is_last_hour": True,
            "has_existing_bid": False,
            "message": "The auction is in its final hour. Only existing bidders can revise their quotation. New submissions are not allowed."
        }

    return {
        "eligible": True,
        "is_last_hour": is_last_hour,
        "has_existing_bid": has_existing_bid,
        "message": "You can revise your quotation." if has_existing_bid else "You can submit your quotation.",
        "time_left_seconds": int(diff_seconds)
    }

@frappe.whitelist(allow_guest=True)
def get_existing_bid(rfq, supplier):
    """Fetch supplier's last submitted bid for pre-filling."""
    # ✅ Get most recent bid (order by creation desc)
    existing_name = frappe.db.get_value(
        "Supplier Quotation",
        {
            "quotation_number": rfq,
            "supplier": supplier,
            "docstatus": ["in", [0, 1]]
        },
        "name",
        order_by="creation desc"  # ✅ get latest bid
    )

    if not existing_name:
        return None

    sq_doc = frappe.get_doc("Supplier Quotation", existing_name)

    # ✅ Always return items even if rate is 0
    return {
        "name": sq_doc.name,
        "items": [
            {
                "item_code": i.item_code,
                "qty": i.qty,
                "uom": i.uom or "",
                "rate": i.rate or 0,
                "amount": i.amount or 0,
                "warehouse": i.warehouse or ""
            }
            for i in sq_doc.items
        ] if sq_doc.items else [],
    "custom_shipment_mode": sq_doc.custom_shipment_mode or "",
    "custom_airline_name": sq_doc.custom_airline_name or "",
    "custom_cw": sq_doc.custom_cw or 0,
    "custom_rate_kg": sq_doc.custom_rate_kg or 0,
    "custom_fsc": sq_doc.custom_fsc or 0,
    "custom_sc": sq_doc.custom_sc or 0,
    "custom_xray": sq_doc.custom_xray or 0,
    "custom_pick_uporigin": sq_doc.custom_pick_uporigin or "",
    "custom_ex_words": sq_doc.custom_ex_words or 0,
    "custom_total_freight": sq_doc.custom_total_freight or 0,
    "custom_cfs_charges": sq_doc.custom_cfs_charges or 0,
    "custom_shipping_line_charges": sq_doc.custom_shipping_line_charges or 0,
    "custom_from_currency": sq_doc.custom_from_currency or "",
    "custom_to_currency": sq_doc.custom_to_currency or "",
    "custom_xrxe_com": sq_doc.custom_xrxe_com or 0,
    "custom_total_freight_inr": sq_doc.custom_total_freight_inr or 0,
    "custom_total_landing_pricecinr": sq_doc.custom_total_landing_pricecinr or 0,
    "custom_dc_inr":sq_doc.custom_dc_inr or 0,
    "custom_transit_day":sq_doc.custom_transit_day or 0,
    "custom_pickup_location":sq_doc.custom_pickup_location or 0
    }