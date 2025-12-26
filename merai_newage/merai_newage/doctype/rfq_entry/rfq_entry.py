
# Copyright (c) 2025, Siddhant Hybrowlabs and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from collections import defaultdict

class RFQEntry(Document):
    def validate(self):
        """Validate RFQ Entry before submission"""
        pass
    
    def on_submit(self):
        """Create multiple RFQs grouped by supplier"""
        self.create_request_for_quotations()
    
    def create_request_for_quotations(self):
        """Create separate RFQs for each supplier with proper linking"""
        
        # Group items by supplier
        supplier_items = defaultdict(list)
        
        for item in self.rfq_entry_details:
            supplier_items[item.supplier].append(item)
        
        # Create separate RFQ for each supplier
        created_rfqs = []
        
        for supplier, items in supplier_items.items():
            try:
                # Get supplier details
                supplier_doc = frappe.get_doc("Supplier", supplier)
                primary_email = supplier_doc.email_id
                
                # Get additional emails from the first item
                additional_emails = ""
                if hasattr(items[0], 'additional_emails') and items[0].additional_emails:
                    additional_emails = items[0].additional_emails
                
                # Get company
                company = frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company")
                
                # Get message for supplier
                message_for_supplier = "Please supply the specified items at the best possible rates"
                if hasattr(self, 'message_for_supplier') and self.message_for_supplier:
                    message_for_supplier = self.message_for_supplier
                
                # Create new RFQ
                rfq = frappe.get_doc({
                    "doctype": "Request for Quotation",
                    "transaction_date": frappe.utils.today(),
                    "schedule_date": self.required_by or frappe.utils.add_days(frappe.utils.today(), 7),
                    "company": company,
                    "message_for_supplier": message_for_supplier,
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
                    
                    # Get UOM and conversion factor
                    uom = item.uom or item_doc.stock_uom
                    conversion_factor = 1
                    
                    if uom != item_doc.stock_uom:
                        conversion_factor = frappe.db.get_value(
                            "UOM Conversion Detail",
                            {"parent": item.item_code, "uom": uom},
                            "conversion_factor"
                        ) or 1
                    
                    # Calculate stock qty
                    stock_qty = item.qty * conversion_factor
                    
                    # Get material request and material request item safely
                    material_request = getattr(item, 'material_request', None)
                    material_request_item = getattr(item, 'material_request_item', None)
                    
                    # Prepare RFQ item dict
                    rfq_item_dict = {
                        "item_code": item.item_code,
                        "item_name": item_doc.item_name,
                        "description": item_doc.description or item_doc.item_name,
                        "qty": item.qty,
                        "stock_qty": stock_qty,
                        "schedule_date": item.required_date or self.required_by or frappe.utils.add_days(frappe.utils.today(), 7),
                        "uom": uom,
                        "stock_uom": item_doc.stock_uom,
                        "conversion_factor": conversion_factor,
                        "item_group": item_doc.item_group,
                    }
                    
                    # Debug log
                    frappe.log_error(
                        message=f"""
                        Item Code: {item.item_code}
                        Material Request: {material_request}
                        Material Request Item: {material_request_item}
                        Item has material_request attr: {hasattr(item, 'material_request')}
                        Item has material_request_item attr: {hasattr(item, 'material_request_item')}
                        RFQ Item Dict: {rfq_item_dict}
                        """,
                        title=f"Debug RFQ Item Creation - {supplier}"
                    )
                    
                    # Add warehouse if present
                    if hasattr(item, 'warehouse') and item.warehouse:
                        rfq_item_dict["warehouse"] = item.warehouse
                    
                    # Add brand if present
                    if hasattr(item_doc, 'brand') and item_doc.brand:
                        rfq_item_dict["brand"] = item_doc.brand
                    
                    # CRITICAL: Add Material Request reference
                    if material_request:
                        rfq_item_dict["material_request"] = material_request
                        
                    # CRITICAL: Add Material Request Item reference
                    if material_request_item:
                        rfq_item_dict["material_request_item"] = material_request_item
                    
                    rfq.append("items", rfq_item_dict)
                
                # Save RFQ
                rfq.flags.ignore_permissions = True
                rfq.insert()
                
                # Submit RFQ
                rfq.submit()
                
                created_rfqs.append(rfq.name)
                
                # Success message
                frappe.msgprint(
                    _("Created RFQ <a href='/app/request-for-quotation/{0}'>{0}</a> for supplier <b>{1}</b>").format(
                        rfq.name, supplier
                    ),
                    indicator="green",
                    alert=True
                )
                
            except Exception as e:
                error_log = frappe.log_error(
                    message=frappe.get_traceback(),
                    title=f"RFQ Creation Failed for Supplier: {supplier}"
                )
                frappe.throw(
                    _("Failed to create RFQ for supplier {0}. Error: {1}<br>Check Error Log: {2}").format(
                        supplier, str(e), error_log.name
                    )
                )
        
        # Commit changes
        if created_rfqs:
            frappe.db.commit()
            
            # Show summary
            frappe.msgprint(
                _("Successfully created {0} Request for Quotation(s): {1}").format(
                    len(created_rfqs), 
                    ", ".join(created_rfqs)
                ),
                title=_("RFQs Created"),
                indicator="green"
            )


@frappe.whitelist()
def create_rfq_entry(source_name):
    """Create RFQ Entry from Material Request"""
    
    # Get source Material Request
    mr_doc = frappe.get_doc("Material Request", source_name)
    
    # Create new RFQ Entry
    rfq_entry = frappe.new_doc("RFQ Entry")
    
    # Set header fields
    rfq_entry.material_request = mr_doc.name
    rfq_entry.required_by = mr_doc.schedule_date
    rfq_entry.created_by = frappe.session.user
    
    # Copy message for supplier if exists
    if hasattr(mr_doc, 'message_for_supplier') and mr_doc.message_for_supplier:
        rfq_entry.message_for_supplier = mr_doc.message_for_supplier
    
    # Add items from Material Request
    for mr_item in mr_doc.items:
        rfq_entry.append("rfq_entry_details", {
            "item_code": mr_item.item_code,
            "qty": mr_item.qty,
            "uom": mr_item.uom,
            "warehouse": mr_item.warehouse,
            "required_date": mr_item.schedule_date,
            "supplier": mr_item.custom_supplier if hasattr(mr_item, 'custom_supplier') else None,
            "material_request": mr_doc.name,
            "material_request_item": mr_item.name
        })
    
    # Insert the document
    rfq_entry.insert()
    
    # Success message
    frappe.msgprint(
        _("RFQ Entry <a href='/app/rfq-entry/{0}'>{0}</a> created successfully from Material Request {1}").format(
            rfq_entry.name, mr_doc.name
        ),
        indicator="green",
        alert=True
    )
    
    return rfq_entry.name


# Hook this function in hooks.py
def allow_duplicate_suppliers_with_different_emails(doc, method):
    """
    Override duplicate supplier validation in Request for Quotation
    to allow same supplier with different email addresses
    """
    if doc.doctype != "Request for Quotation":
        return
    
    # Store original validation method
    if hasattr(doc, 'validate_duplicate_supplier'):
        original_validate = doc.validate_duplicate_supplier
        
        def custom_validate_duplicate_supplier():
            """Check for duplicate supplier-email combinations instead of just supplier"""
            supplier_email_combinations = []
            
            for supplier_row in doc.suppliers:
                # Create unique combination of supplier + email
                combination = f"{supplier_row.supplier}:::{supplier_row.email_id or 'NO_EMAIL'}"
                
                if combination in supplier_email_combinations:
                    frappe.throw(
                        _("Row #{0}: Supplier {1} with email {2} has been entered multiple times").format(
                            supplier_row.idx,
                            frappe.bold(supplier_row.supplier),
                            frappe.bold(supplier_row.email_id or "No Email")
                        )
                    )
                
                supplier_email_combinations.append(combination)
        
        # Replace the validation method
        doc.validate_duplicate_supplier = custom_validate_duplicate_supplier