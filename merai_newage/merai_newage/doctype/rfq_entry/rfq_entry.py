

# # Copyright (c) 2025, Siddhant Hybrowlabs and contributors
# # For license information, please see license.txt

# import frappe
# from frappe.model.document import Document
# from frappe import _
# from collections import defaultdict

# class RFQEntry(Document):
#     def on_submit(self):
#         """Create multiple RFQs grouped by supplier"""
#         self.create_request_for_quotations()
    
#     def create_request_for_quotations(self):
#         """Create separate RFQs for each supplier with proper email handling"""
        
#         # Group items by supplier
#         supplier_items = defaultdict(list)
        
#         for item in self.rfq_entry_details:
#             if not item.supplier:
#                 frappe.throw(_("Row {0}: Supplier is mandatory for item {1}").format(
#                     item.idx, item.item_code
#                 ))
            
#             supplier_items[item.supplier].append(item)
        
#         # Create separate RFQ for each supplier
#         created_rfqs = []
        
#         for supplier, items in supplier_items.items():
#             try:
#                 # Get supplier primary email
#                 primary_email = frappe.db.get_value("Supplier", supplier, "email_id")
                
#                 # Get additional emails from the first item (they should be same for all items of same supplier)
#                 additional_emails = items[0].additional_emails if hasattr(items[0], 'additional_emails') and items[0].additional_emails else ""
                
#                 # Create new RFQ
#                 rfq = frappe.get_doc({
#                     "doctype": "Request for Quotation",
#                     "transaction_date": frappe.utils.today(),
#                     "schedule_date": self.required_by or frappe.utils.add_days(frappe.utils.today(), 7),
#                     "company": frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company"),
#                     "message_for_supplier": self.message_for_supplier if hasattr(self, 'message_for_supplier') else "",
#                     "email_template": self.email_template if hasattr(self, 'email_template') else None,
#                     "message_for_supplier":"Please supply the specified items at the best possible rates"
#                 })
                
#                 # Add primary supplier with primary email
#                 if primary_email:
#                     rfq.append("suppliers", {
#                         "supplier": supplier,
#                         "email_id": primary_email.strip(),
#                         "send_email": 1
#                     })
#                 else:
#                     # Add supplier without email
#                     rfq.append("suppliers", {
#                         "supplier": supplier,
#                         "send_email": 0
#                     })
                
#                 # Add additional emails as separate supplier rows (same supplier, different emails)
#                 if additional_emails:
#                     # Split by comma and process each email
#                     email_list = [email.strip() for email in additional_emails.split(',') if email.strip()]
                    
#                     for email in email_list:
#                         if email and email != primary_email:  # Avoid duplicate primary email
#                             rfq.append("suppliers", {
#                                 "supplier": supplier,
#                                 "email_id": email,
#                                 "send_email": 1
#                             })
                
#                 # Add items for this supplier
#                 for item in items:
#                     conversion_factor = frappe.db.get_value(
# 						"UOM Conversion Detail",
# 						{"parent": item.item_code, "uom": item.uom},
# 						"conversion_factor"
# 					) or 1
#                     rfq.append("items", {
#                         "item_code": item.item_code,
#                         "qty": item.qty,
#                         "schedule_date": item.required_date or self.required_by,
#                         "warehouse": item.warehouse,
#                         "uom": item.uom,
#                         "conversion_factor": conversion_factor,
#                         "material_request": item.material_request if hasattr(item, 'material_request') else None,
#                         "material_request_item": item.material_request_item if hasattr(item, 'material_request_item') else None,
#                         "description": frappe.db.get_value("Item", item.item_code, "description") or ""
#                     })
                
#                 # Insert RFQ
#                 rfq.insert(ignore_permissions=True)
                
#                 # Submit RFQ (this will trigger email sending based on email_template)
#                 rfq.submit()
                
#                 created_rfqs.append(rfq.name)
                
#                 # Success message with link
#                 frappe.msgprint(
#                     _("Created RFQ <a href='/app/request-for-quotation/{0}'>{0}</a> for supplier <b>{1}</b>").format(
#                         rfq.name, supplier
#                     ),
#                     indicator="green",
#                     alert=True
#                 )
                
#             except Exception as e:
#                 frappe.log_error(
#                     message=frappe.get_traceback(),
#                     title=f"RFQ Creation Failed for Supplier: {supplier}"
#                 )
#                 frappe.throw(
#                     _("Failed to create RFQ for supplier {0}. Error: {1}").format(
#                         supplier, str(e)
#                     )
#                 )
        
#         # Store created RFQs reference
#         if created_rfqs:
#             # self.db_set('custom_created_rfqs', ','.join(created_rfqs), update_modified=False)
#             frappe.db.commit()
            
#             # Show summary message
#             frappe.msgprint(
#                 _("Successfully created {0} Request for Quotation(s)").format(len(created_rfqs)),
#                 title=_("RFQs Created"),
#                 indicator="green"
#             )


# @frappe.whitelist()
# def create_rfq_entry(source_name):
#     """Create RFQ Entry from Material Request"""
#     doc = frappe.get_doc("Material Request", source_name)
#     new_doc = frappe.new_doc("RFQ Entry")
    
#     # Set header fields
#     new_doc.required_by = doc.schedule_date
#     new_doc.created_by = frappe.session.user
#     new_doc.material_request = doc.name
    
#     # Add items from Material Request
#     for row in doc.items:
#         new_doc.append("rfq_entry_details", {
#             "item_code": row.item_code,
#             "qty": row.qty,
#             "warehouse": row.warehouse,
#             "required_date": row.schedule_date,
#             "supplier": row.custom_supplier if hasattr(row, 'custom_supplier') else None,
#             "uom": row.uom,
#             "material_request": doc.name,
#             "material_request_item": row.name
#         })
    
#     new_doc.insert()
    
#     frappe.msgprint(
#         _("RFQ Entry <a href='/app/rfq-entry/{0}'>{0}</a> created successfully").format(new_doc.name),
#         indicator="green",
#         alert=True
#     )
    
#     return new_doc.name


# import frappe
# from frappe import _

# def allow_duplicate_suppliers_with_different_emails(doc, method):
#     """
#     Override duplicate supplier validation to allow same supplier 
#     with different email addresses
#     """
#     # Replace the validation method
#     original_validate = doc.validate_duplicate_supplier
    
#     def custom_validate():
#         """Check for duplicate supplier-email combinations"""
#         suppliers_emails = []
        
#         for supplier in doc.suppliers:
#             combination = f"{supplier.supplier}|||{supplier.email_id or ''}"
            
#             if combination in suppliers_emails:
#                 frappe.throw(
#                     _("Supplier {0} with email {1} has been entered multiple times").format(
#                         frappe.bold(supplier.supplier),
#                         frappe.bold(supplier.email_id or "No Email")
#                     )
#                 )
            
#             suppliers_emails.append(combination)
    
#     # Replace with custom validation
#     doc.validate_duplicate_supplier = custom_validate



# Copyright (c) 2025, Siddhant Hybrowlabs and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from collections import defaultdict

class RFQEntry(Document):
    def on_submit(self):
        """Create multiple RFQs grouped by supplier"""
        self.create_request_for_quotations()
    
    def create_request_for_quotations(self):
        """Create separate RFQs for each supplier with proper linking"""
        
        # Group items by supplier
        supplier_items = defaultdict(list)
        
        for item in self.rfq_entry_details:
            if not item.supplier:
                frappe.throw(_("Row {0}: Supplier is mandatory for item {1}").format(
                    item.idx, item.item_code
                ))
            
            supplier_items[item.supplier].append(item)
        
        # Create separate RFQ for each supplier
        created_rfqs = []
        
        for supplier, items in supplier_items.items():
            try:
                # Get supplier details
                supplier_doc = frappe.get_doc("Supplier", supplier)
                primary_email = supplier_doc.email_id
                print("primary_email=============",primary_email)
                # Get additional emails from the first item
                additional_emails = items[0].additional_emails if hasattr(items[0], 'additional_emails') and items[0].additional_emails else ""
                
                # Get company
                company = frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company")
                
                # Create new RFQ
                rfq = frappe.get_doc({
                    "doctype": "Request for Quotation",
                    "transaction_date": frappe.utils.today(),
                    "schedule_date": self.required_by or frappe.utils.add_days(frappe.utils.today(), 7),
                    "company": company,
                    "message_for_supplier": self.message_for_supplier if hasattr(self, 'message_for_supplier') else "Please supply the specified items at the best possible rates",
                })
                
                # Add email template if exists
                if hasattr(self, 'email_template') and self.email_template:
                    rfq.email_template = self.email_template
                
                # Add suppliers FIRST
                if primary_email:
                    rfq.append("suppliers", {
                        "supplier": supplier,
                        "supplier_name": supplier_doc.supplier_name,
                        "email_id": primary_email.strip(),
                        "send_email": 1
                    })
                else:
                    rfq.append("suppliers", {
                        "supplier": supplier,
                        "supplier_name": supplier_doc.supplier_name,
                        "send_email": 0
                    })
                
                # Add additional emails as separate supplier rows
                if additional_emails:
                    email_list = [email.strip() for email in additional_emails.split(',') if email.strip()]
                    
                    for email in email_list:
                        if email and email != primary_email:
                            rfq.append("suppliers", {
                                "supplier": supplier,
                                "supplier_name": supplier_doc.supplier_name,
                                "email_id": email,
                                "send_email": 1
                            })
                
                # Add items SECOND
                for item in items:
                    # Get item details
                    item_doc = frappe.get_doc("Item", item.item_code)
                    
                    # Get conversion factor
                    conversion_factor = frappe.db.get_value(
                        "UOM Conversion Detail",
                        {"parent": item.item_code, "uom": item.uom},
                        "conversion_factor"
                    ) or 1
                    
                    # Get stock qty
                    stock_qty = item.qty * conversion_factor
                    
                    rfq.append("items", {
                        "item_code": item.item_code,
                        "item_name": item_doc.item_name,
                        "description": item_doc.description or item_doc.item_name,
                        "qty": item.qty,
                        "stock_qty": stock_qty,
                        "schedule_date": item.required_date or self.required_by or frappe.utils.add_days(frappe.utils.today(), 7),
                        "warehouse": item.warehouse,
                        "uom": item.uom,
                        "stock_uom": item_doc.stock_uom,
                        "conversion_factor": conversion_factor,
                        "material_request": item.material_request if hasattr(item, 'material_request') else None,
                        "material_request_item": item.material_request_item if hasattr(item, 'material_request_item') else None,
                        "item_group": item_doc.item_group,
                        "brand": item_doc.brand if hasattr(item_doc, 'brand') else None
                    })
                
                # Insert and save the RFQ
                rfq.insert(ignore_permissions=True)
                
                # Submit RFQ - this will trigger email sending
                rfq.submit()
                
                created_rfqs.append(rfq.name)
                
                # Success message with link
                frappe.msgprint(
                    _("Created RFQ <a href='/app/request-for-quotation/{0}'>{0}</a> for supplier <b>{1}</b>").format(
                        rfq.name, supplier
                    ),
                    indicator="green",
                    alert=True
                )
                
            except Exception as e:
                frappe.log_error(
                    message=frappe.get_traceback(),
                    title=f"RFQ Creation Failed for Supplier: {supplier}"
                )
                frappe.throw(
                    _("Failed to create RFQ for supplier {0}. Error: {1}").format(
                        supplier, str(e)
                    )
                )
        
        # Store created RFQs reference and commit
        if created_rfqs:
            frappe.db.commit()
            
            # Show summary message
            frappe.msgprint(
                _("Successfully created {0} Request for Quotation(s)").format(len(created_rfqs)),
                title=_("RFQs Created"),
                indicator="green"
            )


@frappe.whitelist()
def create_rfq_entry(source_name):
    """Create RFQ Entry from Material Request"""
    doc = frappe.get_doc("Material Request", source_name)
    new_doc = frappe.new_doc("RFQ Entry")
    
    # Set header fields
    new_doc.required_by = doc.schedule_date
    new_doc.created_by = frappe.session.user
    new_doc.material_request = doc.name
    
    # Add items from Material Request
    for row in doc.items:
        new_doc.append("rfq_entry_details", {
            "item_code": row.item_code,
            "qty": row.qty,
            "warehouse": row.warehouse,
            "required_date": row.schedule_date,
            "supplier": row.custom_supplier if hasattr(row, 'custom_supplier') else None,
            "uom": row.uom,
            "material_request": doc.name,
            "material_request_item": row.name
        })
    
    new_doc.insert()
    
    frappe.msgprint(
        _("RFQ Entry <a href='/app/rfq-entry/{0}'>{0}</a> created successfully").format(new_doc.name),
        indicator="green",
        alert=True
    )
    
    return new_doc.name


def allow_duplicate_suppliers_with_different_emails(doc, method):
    """
    Override duplicate supplier validation to allow same supplier 
    with different email addresses
    """
    # Replace the validation method
    original_validate = doc.validate_duplicate_supplier
    
    def custom_validate():
        """Check for duplicate supplier-email combinations"""
        suppliers_emails = []
        
        for supplier in doc.suppliers:
            combination = f"{supplier.supplier}|||{supplier.email_id or ''}"
            
            if combination in suppliers_emails:
                frappe.throw(
                    _("Supplier {0} with email {1} has been entered multiple times").format(
                        frappe.bold(supplier.supplier),
                        frappe.bold(supplier.email_id or "No Email")
                    )
                )
            
            suppliers_emails.append(combination)
    
    # Replace with custom validation
    doc.validate_duplicate_supplier = custom_validate