# Copyright (c) 2026, Siddhant Hybrowlabs and contributors
# For license information, please see license.txt

# import frappe
import frappe
from frappe.model.document import Document


class SupplierInvoice(Document):

    def autoname(self):
        if self.invoice_type == "Non PO":
            self.name = frappe.model.naming.make_autoname("Non PO-.YYYY.-.#####")

        elif self.invoice_type == "PO":

            if not self.po_number:
                frappe.throw("PO Number is required")

            count = frappe.db.count("Supplier Invoice", {
                "po_number": self.po_number
            })

            suffix = str(count + 1).zfill(2)

            self.name = f"{self.po_number}-{suffix}"

        else:
            self.name = frappe.model.naming.make_autoname("SUP-INV-.YYYY.-.#####")