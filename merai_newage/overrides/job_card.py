import frappe
from erpnext.manufacturing.doctype.job_card.job_card import JobCard
import json
from frappe.utils import nowdate

class CustomJobCard(JobCard):
    def before_submit(self):
        # is_qi_reqd = frappe.db.get_value("Opeartion",self.operation,"custom_quality_inspection_required")
        is_qi_reqd = frappe.db.get_value(
            "Operation", 
            self.operation,  # assuming self.operation stores Operation name
            "custom_quality_inspection_required"
        )
        if self.operation and "soft" in self.operation.lower():
            self.custom_software = self.operation

        # print("is_qi_reqd========7===",is_qi_reqd)
        if is_qi_reqd:
            if not self.quality_inspection:
                frappe.throw("Please create and submit a Quality Inspection before submitting the Job Card.")

            qi_doc = frappe.get_doc("Quality Inspection", self.quality_inspection)

            if qi_doc.docstatus != 1:
                frappe.throw(f"Quality Inspection {qi_doc.name} must be submitted before submitting the Job Card.")

        # super().before_submit()
    def on_submit(self):
        employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
        self.custom_authorised_by = employee


@frappe.whitelist()
def update_user_detail_in_sign_table(doc):
    doc = frappe.get_doc(json.loads(doc))
    cur_user = frappe.session.user
    today = nowdate()
    user_id = frappe.session.user
    user_info = frappe.db.get_value(
        "User",
        {"name": user_id},
        ["full_name", "username"],
        as_dict=True
    )

    if not user_info:
        frappe.throw(f"No User found for {user_id}")
    print("role_type==========101------job card-----",)
    full_name = user_info.full_name
    username = user_info.username
    print("doc.eorkflowstate==   in job crad====",doc.workflow_state)
    if doc.workflow_state == "Feasibility Test Pending":
        duplicate = any(row.get("line_clearance_username") == cur_user for row in doc.custom_job_card_signature_details)
        if not duplicate:
            doc.append("custom_job_card_signature_details", {
                "line_clearance_user_fullname": full_name,
                "line_clearance_date": today,
                "line_clearance_username":cur_user,
                "line_clearance_userid":username
            })
    
    elif doc.workflow_state == "Feasibility Verification Pending":
        duplicate = any(row.get("feasibility_test_username") == cur_user for row in doc.custom_job_card_signature_details)
        if not duplicate:
            doc.append("custom_job_card_signature_details", {
                "feasibility_test_username": cur_user,
                "feasibility_test_date": today,
                "feasibility_test_user_fullname":full_name,
                "feasibility_test_userid":username

            })
    elif doc.workflow_state == "Feasibility Test Verified":
        duplicate = any(row.get("feasibility_test_approved_username") == cur_user for row in doc.custom_job_card_signature_details)
        if not duplicate:
            doc.append("custom_job_card_signature_details", {
                "feasibility_test_approved_username": cur_user,
                "feasibility_test_approved__date": today,
                "feasibility_test__approved_user_fullname":full_name,
                "feasibility_test__approved_userid":username

            })

    elif doc.workflow_state == "Software Test":
        duplicate = any(row.get("software_checked_by") == cur_user for row in doc.custom_job_card_signature_details)
        if not duplicate:
            doc.append("custom_job_card_signature_details", {
                "software_checked_by": cur_user,
                "software_checked_by_date": today,
                "software_checked_by_fullname":cur_user,
                "softtware_checked_by_userid":username

            })
    elif doc.workflow_state == "Software Verified":
        duplicate = any(row.get("software_verified_by") == cur_user for row in doc.custom_job_card_signature_details)
        if not duplicate:
            doc.append("custom_job_card_signature_details", {
                "software_verified_by": cur_user,
                "software_verified_by_date": today,
                "software_verified_by_fullname":cur_user,
                "software_verified_by_userid":username

            })


    # Save changes
    doc.flags.ignore_permissions = True
    doc.flags.ignore_validate_update_after_submit = True
    doc.save(ignore_permissions=True)
    frappe.db.commit()









@frappe.whitelist()
def get_employee_by_user():
    print("frappe.session.uer------120---",frappe.session.user)
    employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
    print("employe----------",employee)
    return employee





@frappe.whitelist()
def set_value_to_user_table(doc_name, user_id, document_state=None):
    doc = frappe.get_doc("Job Card", doc_name)
    print("=====doc=========124",document_state)
    user_info = frappe.db.get_value(
        "User",
        {"name": user_id},
        ["full_name", "username"],
        as_dict=True
    )
    today = nowdate()
    if not user_info:
        frappe.throw(f"No User found for {user_id}")

    full_name = user_info.full_name
    username = user_info.username

    row_data = {}
    cur_user = user_id
    if document_state == "Line Clearance Approved":
        # duplicate = any(row.get("line_clearance_username") == cur_user for row in doc.custom_job_card_signature_details)
     
        row_data.update({
                "line_clearance_user_fullname": full_name,
                "line_clearance_date": today,
                "line_clearance_username":cur_user,
                "line_clearance_userid":username
        })
    elif document_state == "Software Test" or doc.custom__job_card_status=="Software Tested":
        row_data.update({
                "software_checked_by": cur_user,
                "software_checked_by_date": today,
                "software_checked_by_fullname":cur_user,
                "softtware_checked_by_userid":username
        })
    elif document_state == "Software Verified" or doc.custom__job_card_status=="Software Verified":
        row_data.update({
                "software_verified_by": cur_user,
                "software_verified_by_date": today,
                "software_verified_by_fullname":cur_user,
                "software_verified_by_userid":username
        })
    elif document_state == "Feasibility Test Verified":
        row_data.update({
            "feasibility_test_approved_username": cur_user,
                "feasibility_test_approved__date": today,
                "feasibility_test__approved_user_fullname":full_name,
                "feasibility_test__approved_userid":username
        })
    elif document_state == "Feasibility Verification Pending":
        row_data.update({
                "feasibility_test_username": cur_user,
                "feasibility_test_date": today,
                "feasibility_test_user_fullname":full_name,
                "feasibility_test_userid":username

            })

    # Append the row
    doc.append("custom_job_card_signature_details", row_data)

    doc.flags.ignore_permissions = True
    doc.save()
    frappe.db.commit()

    # return {
    #     "status": "success",
    #     "employee_full_name": full_name,
    #     "employee_username": username,
    #     "role": role_type
    # }


@frappe.whitelist()
def set_value(doctype,name,fieldname,value):
    print("value====",value)
    frappe.db.set_value(doctype,name,fieldname,value)
    # save(ignore_permissions=1)
    frappe.db.commit()


import frappe

@frappe.whitelist()
def check_the_values_set_r_not(docname,job_card_status):
    """
    Check if required checklist values are filled before proceeding.
    Raises an exception if any mandatory responses are missing.
    """

    # Fetch the Job Card document
    doc = frappe.get_doc("Job Card", docname)

    # 🔹 1. Line Clearance Check — when in "Draft"
    if job_card_status == "Draft":
        incomplete = []
        for row in doc.custom_line_clearance_checklist_details or []:
            if not row.yesno:
                incomplete.append(row.line_clearance_checklist)

        if incomplete:
            frappe.throw(
                f"Please complete Line Clearance Checklist before proceeding. Missing responses for: {', '.join(incomplete)}"
            )

    # 🔹 2. Feasibility Verification / Test Verified — when in those statuses
    elif job_card_status in ["Feasibility Verification Pending", "Feasibility Test Verified"]:
        incomplete = []
        for row in doc.custom_feasibility_testing or []:
            if not row.verified:
                incomplete.append(row.feasibility_testing)

        if incomplete:
            frappe.throw(
                f"Please complete Feasibility Testings before proceeding. Missing responses for: {', '.join(incomplete)}"
            )

    return "✅ All required checks are complete."

