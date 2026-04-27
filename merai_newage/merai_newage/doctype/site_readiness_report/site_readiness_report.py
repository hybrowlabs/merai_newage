# # Copyright (c) 2026, Siddhant Hybrowlabs and contributors
# # For license information, please see license.txt

import frappe
from frappe.model.document import Document

class SiteReadinessReport(Document):
    def before_insert(self):
        self.set_default_rows()

    def set_default_rows(self):
        # ---------- POWER TESTING ----------
        if not self.power_testing:
            power_rows = [
                {"test_parameters": "B/W Phase & Neutral", "standard_limit": "230 ± 10 volts"},
                {"test_parameters": "B/W Phase & Earthing", "standard_limit": "230 ± 10 volts"},
                {"test_parameters": "B/W Neutral & Earthing", "standard_limit": "Less than 2 Volts"}
            ]
            for row in power_rows:
                self.append("power_testing", row)

        # ---------- PRE-INSTALLATION ----------
        if not self.pre_installation_table:
            pre_rows = [
                {
                    "activity": "Confirmation of Biomedical Staff Availability",
                    "responsible": "Sales Team",
                    "remarks": "To be informed before delivery"
                },
                {
                    "activity": "Opening Meeting with Biomedical Team",
                    "responsible": "Sales + TAS",
                    "remarks": "Time to be blocked"
                },
                {
                    "activity": "Packaging Material Verification",
                    "responsible": "TAS",
                    "remarks": "As per dispatch list"
                },
                {
                    "activity": "Required Resources (OT, Power Supply) Confirmed",
                    "responsible": "Sales Team + TAS",
                    "remarks": "To be ready before departure of installation team from Vapi"
                }
            ]
            for row in pre_rows:
                self.append("pre_installation_table", row)

        # ---------- SAWBONE TESTING ----------
        if not self.sawbone_testing:
            sawbone_rows = [
                {
                    "activity": "Saw bone Testing",
                    "responsible": "Installation Team",
                    "remarks": "Ensure required setup is available"
                },
                {
                    "activity": "Opening Meeting with Surgeon",
                    "responsible": "Sales + Installation Team + TAS",
                    "remarks": "To be coordinated in advance by local team"
                },
                {
                    "activity": "Saw bone Demo to Surgeon",
                    "responsible": "Installation Team",
                    "remarks": "Photos & surgeon feedback to be recorded and sent to Vapi"
                }
            ]
            for row in sawbone_rows:
                self.append("sawbone_testing", row)

        # ---------- CLOSURE ----------
        if not self.closure_activity:
            closure_rows = [
                {
                    "activity": "Final Meeting & Sign-off",
                    "responsible": "Sales + TAS + Installation Team",
                    "remarks": "Installation sign-off to be taken from customer"
                }
            ]
            for row in closure_rows:
                self.append("closure_activity", row)


@frappe.whitelist()
def get_default_rows(doc):
    doc = frappe.get_doc(frappe.parse_json(doc))
    doc.set_default_rows()
    return doc