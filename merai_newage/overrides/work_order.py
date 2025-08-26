
from merai_newage.merai_newage.doctype.batch_number_template.batch_number_template import create_batch_number

import frappe,json

def before_insert(doc, _method):
        item = doc.production_item
        batch_number = create_batch_number(doc)
  
        if not batch_number:
            frappe.log_error(
                f"Batch number generation failed for Work Order {doc.name}, item {item}. Skipping batch creation.",
                "Work Order Batch Creation"
            )
       
            return
        
        try:
            batch = frappe.new_doc("Batch")
            batch.batch_id = batch_number
            batch.custom_work_order = doc.name
            batch.custom_batch_number = batch_number.replace(item+"-", "")
            batch.item = item
            batch.save(ignore_permissions=True)
            batch.batch_qty = doc.qty

            doc.custom_batch_number = batch.batch_id
            
        except Exception as e:
            frappe.log_error(
                f"Error creating batch for Work Order {doc.name}: {str(e)}",
                "Work Order Batch Creation"
            )
            pass
