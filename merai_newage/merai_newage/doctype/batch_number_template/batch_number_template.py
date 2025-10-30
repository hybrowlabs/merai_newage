# Copyright (c) 2025, Siddhant Hybrowlabs and contributors
# For license information, please see license.txt

# import frappe


import frappe
from frappe.core.doctype.server_script.server_script import ServerScript
from frappe.model.document import Document
from frappe.utils.safe_exec import safe_exec
# import frappe
# from frappe.model.document import Document
# from frappe.utils.safe_exec import safe_exec

from frappe.utils.jinja import render_template

class BatchNumberTemplate(Document):
	pass




# def generate_batch_number(doc, method=None):
#     if not doc.production_item:
#         return

#     # Get the template linked in Item master
#     template_name = frappe.get_value("Item", doc.production_item, "custom_batch_number_template")
#     if not template_name:
#         return

#     # Fetch the actual template string
#     template = frappe.get_value("Batch Number Template", template_name, "batch_number_logic")
#     if not template:
#         return

#     # Context for Jinja rendering
#     context = {"doc": doc, "frappe": frappe}

#     try:
#         result = render_template(template, context)
#     except Exception as e:
#         frappe.throw(f"Batch Number Template error: {e}")

#     if result:
#         doc.custom_batch_number = result.strip()



def exec_py_exp(py_exp, variables):
	# Handle null or empty py_exp
	if not py_exp or not py_exp.strip():
		return None

	py_exp = py_exp.replace('\n', '\n  ')
	py_exp = "def returned_function(variables):\n  " + py_exp
	_g, _l = safe_exec(py_exp)
	returned_function = _g.get("returned_function")
	return returned_function(variables)



@frappe.whitelist(allow_guest=True)
def create_batch_number(doc, variables={}):
	print("---33---enyered")
	try:
		variables["doc"] = doc
		print("36----",doc)

		item_code = doc.production_item
		# print("item_code====46",item_code)
		item_data = frappe.get_doc("Item",item_code)
		# print("itemdata========",item_data)

		batch_number_template = frappe.get_doc("Batch Number Template", item_data.custom_batch_number_template)
		print("batch_number_template======",batch_number_template)

		if not hasattr(batch_number_template, 'batch_number_logic') or not batch_number_template.batch_number_logic:
			print("59---")
			frappe.log_error(
				f"No batch_number_logic found in Batch Number Template {batch_number_template.name}",
				"Batch Number Generation"
			)
			return None

		# Execute the logic
		result = exec_py_exp(batch_number_template.batch_number_logic, variables)
		print("result===>64",result)
		if result is None:
			frappe.log_error(
				f"Batch number logic returned None for template {batch_number_template.name}",
				"Batch Number Generation"
			)

		return result

	except frappe.DoesNotExistError as e:
		frappe.log_error(
			f"Document not found during batch number generation: {str(e)}",
			"Batch Number Generation"
		)
		return None

	except Exception as e:
		frappe.log_error(
			f"Error in batch number generation: {str(e)}\nDocument: {doc.doctype} - {doc.name}",
			"Batch Number Generation"
		)
		return None


