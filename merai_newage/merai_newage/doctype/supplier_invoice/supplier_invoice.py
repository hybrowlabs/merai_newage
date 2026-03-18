# Copyright (c) 2026, Siddhant Hybrowlabs and contributors
# For license information, please see license.txt

# import frappe
import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname


class SupplierInvoice(Document):

    def autoname(self):
        if self.invoice_type == "Non PO":
            self.name = make_autoname("Non PO-.YYYY.-.#####")

        elif self.invoice_type == "PO":
            
            base_name = make_autoname("PUR-ORD-.YYYY.-.#####")

            count = frappe.db.count("Supplier Invoice", {
                "name": ["like", f"{base_name}%"]
            })

            suffix = str(count + 1).zfill(2)

            self.name = f"{base_name}-{suffix}"

        else:
            self.name = make_autoname("SUP-INV-.YYYY.-.#####")