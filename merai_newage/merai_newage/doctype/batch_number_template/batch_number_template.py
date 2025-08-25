# Copyright (c) 2025, Siddhant Hybrowlabs and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class BatchNumberTemplate(Document):
	pass



import frappe
from frappe.utils.jinja import render_template

def generate_batch_number(doc, method=None):
    if not doc.production_item:
        return

    # Get the template linked in Item master
    template_name = frappe.get_value("Item", doc.production_item, "custom_batch_number_template")
    if not template_name:
        return

    # Fetch the actual template string
    template = frappe.get_value("Batch Number Template", template_name, "batch_number_logic")
    if not template:
        return

    # Context for Jinja rendering
    context = {"doc": doc, "frappe": frappe}

    try:
        result = render_template(template, context)
    except Exception as e:
        frappe.throw(f"Batch Number Template error: {e}")

    if result:
        doc.custom_batch_number = result.strip()