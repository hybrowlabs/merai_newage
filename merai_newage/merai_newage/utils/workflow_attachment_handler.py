# from merai_newage.merai_newage.utils.sync_workflow_attachments_from_source import sync_workflow_attachments_from_source

# # 🔹 Global mapping (recommended)
# SOURCE_MAP = {
#     "custom_pickup_request": "Pickup Request",
#     "custom_supplier_quotation": "Supplier Quotation",
#     "custom_pre_alert": "Pre Alert",
#     "custom_pre_alert_check_list": "Pre-Alert Check List",
#     "custom_boe_entry": "BOE Entry",
# }


# def sync_workflow_attachments_for_logistics(doc, method):

#     if doc.custom_type != "Logistics":
#         return

#     for field, doctype in SOURCE_MAP.items():
#         source_name = getattr(doc, field, None)

#         if source_name:
#             sync_workflow_attachments_from_source(
#                 doc, doctype, source_name
#             )


from merai_newage.merai_newage.utils.sync_workflow_attachments_from_source import sync_workflow_attachments_from_source

# 🔹 Doctype-wise mapping (FLOW BASED)
DOCTYPE_SOURCE_MAP = {
    "Request for Quotation": {
        "custom_pickup_request": "Pickup Request",
    },
    "Supplier Quotation": {
        "custom_request_for_quotation": "Request for Quotation",
    },
    "Pre Alert": {
        "custom_supplier_quotation": "Supplier Quotation",
    },
}


def sync_workflow_attachments_for_logistics(doc, method):
    
    if getattr(doc, "custom_type", None) != "Logistics":
        return

    # Get mapping based on current doctype
    source_map = DOCTYPE_SOURCE_MAP.get(doc.doctype, {})

    for field, source_doctype in source_map.items():
        source_name = getattr(doc, field, None)
        
        if source_name:
            sync_workflow_attachments_from_source(
                target_doc=doc,
                source_doctype=source_doctype,
                source_name=source_name,
            )