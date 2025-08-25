
from merai_newage.merai_newage.doctype.batch_number_template.batch_number_template import create_batch_number

import frappe,json

def before_insert(doc, _method):
    # print("===========30",doc.custom_manual_batch_no)
    # if doc.custom_manual_batch_no==0:
        # print("doc==",doc.as_dict())
        item = doc.production_item
        batch_number = create_batch_number(doc)
        # print("batch_number====>32",batch_number)
        # Handle case where batch number generation returns None
        if not batch_number:
            frappe.log_error(
                f"Batch number generation failed for Work Order {doc.name}, item {item}. Skipping batch creation.",
                "Work Order Batch Creation"
            )
            # Optionally, you can generate a fallback batch number or skip batch creation
            # For now, we'll skip batch creation entirely
            return
        
        # Create batch only if batch_number is generated successfully
        try:
            batch = frappe.new_doc("Batch")
            batch.batch_id = batch_number
            batch.custom_work_order = doc.name
            batch.custom_batch_number = batch_number.replace(item+"-", "")
            batch.item = item
            batch.save(ignore_permissions=True)

            doc.custom_batch_number = batch.batch_id
            
        except Exception as e:
            frappe.log_error(
                f"Error creating batch for Work Order {doc.name}: {str(e)}",
                "Work Order Batch Creation"
            )
            # Don't fail the Work Order creation if batch creation fails
            pass
