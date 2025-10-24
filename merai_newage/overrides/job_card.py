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
        check_the_values_set_r_not(self.name)
        check_full_dhr_rqd(self)
    # def after_insert(self):
    #     print("------34---in merai-",self.custom_software_reqd)
    #     if self.custom_software_reqd==1:
    #         self.custom_software = frappe.db.get_value("Operation",self.operation,"description")

    def before_insert(self):
        print("------39---in merai-",self.custom_software_reqd)
        if self.custom_software_reqd==1:
            self.custom_software = frappe.db.get_value("Operation",self.operation,"description")



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
def check_the_values_set_r_not(docname):
    """
    Check if required checklist values are filled before proceeding.
    Raises an exception if any mandatory responses are missing.
    """

    doc = frappe.get_doc("Job Card", docname)


    incomplete = []
    for row in doc.custom_line_clearance_checklist_details or []:
        if not row.yesno:
            incomplete.append(row.line_clearance_checklist)

    if incomplete:
        frappe.throw(
            f"Please complete Line Clearance Checklist before proceeding. Missing responses for: {', '.join(incomplete)}"
        )

    incomplete = []
    for row in doc.custom_feasibility_testing or []:
        if not row.verified:
            incomplete.append(row.feasibility_testing)

    if incomplete:
        frappe.throw(
            f"Please complete Feasibility Testings before proceeding. Missing responses for: {', '.join(incomplete)}"
        )
    incomplete = []
    for row in doc.custom_jobcard_opeartion_deatils or []:
        if not row.verified:
            incomplete.append(row.item_code)

    if incomplete:
        frappe.throw(
            f"Please complete Operation Testings before proceeding. Missing responses for: {', '.join(incomplete)}"
        )

    # return "✅ All required checks are complete."
def check_full_dhr_rqd(doc):
    full_dhr = 0
    print("------------257==============")

    for i in doc.custom_jobcard_opeartion_deatils:
        print("Row -------", i.name, "| Batch:", i.batch_number)
        if i.batch_number:
            full_dhr = 1
            break  

    if full_dhr > 0 and doc.work_order:
        workorder_doc = frappe.get_doc("Work Order", doc.work_order)
        workorder_doc.custom_is_full_dhr = 1
        workorder_doc.flags.ignore_permissions = True
        workorder_doc.save(ignore_permissions=True)
        frappe.db.commit()
        print("✅ Work Order updated with full DHR = 1")

    else:
        print("⚠️ No batch number found, skipping update.")
