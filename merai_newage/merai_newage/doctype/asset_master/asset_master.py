# Copyright (c) 2026, Siddhant Hybrowlabs and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class AssetMaster(Document):
    def autoname(self):
        # Manual naming
        if self.is_manual_asset == 1:
            if not self.manual_asset_no:
                frappe.throw("Manual Asset No is required when Manual Asset is enabled")

            if not self.company_code or not self.asset_code:
                frappe.throw("Company Code and Asset Code are required")

            # IMPORTANT: Do NOT use make_autoname here
            self.name = f"{self.company_code}{self.asset_code}{self.manual_asset_no}"

        # Auto naming
        else:
            if not self.company_code or not self.asset_code:
                frappe.throw("Company Code and Asset Code are required for auto naming")

            series = f"{self.company_code}{self.asset_code}.#####"
            self.name = frappe.model.naming.make_autoname(series)
