import frappe, json

DUMMY_PASSWORD = "Merai@123"

# @frappe.whitelist()
# def create_user_with_roles(doc):

#     doc = frappe._dict(json.loads(doc))

#     print("doc-----------43", doc)

#     if not doc.custom_generate_user:
#         return

#     if not doc.custom_user_email_for_creation:
#         frappe.throw("User Email is required")

#     user_email = doc.custom_user_email_for_creation

#     if frappe.db.exists("User", user_email):
#         frappe.db.set_value(
#             "Employee",
#             doc.name,
#             "user_id",
#             user_email
#         )
#         return f"User already exists: {user_email}"

#     role_profile = doc.get("custom_role_profile")  
#     user_doc = frappe.get_doc({
#         "doctype": "User",
#         "email": user_email,
#         "first_name": doc.first_name,
#         "send_welcome_email": 1,
#         "gender": doc.gender,
#         "birth_date": doc.date_of_birth,
#         "enabled": 1,
#         "role_profile_name": role_profile or None
#     })

#     user_doc.new_password = DUMMY_PASSWORD

#     user_doc.insert(ignore_permissions=True)

#     user_doc.add_roles("Employee")

#     frappe.db.set_value(
#         "Employee",
#         doc.name,
#         "user_id",
#         user_email
#     )

#     return user_email


@frappe.whitelist()
def create_user_with_roles(doc):
    doc = frappe._dict(json.loads(doc))

    if not doc.custom_generate_user:
        return

    user_email = doc.custom_user_email_for_creation

    if not user_email:
        frappe.throw("User Email is required")

    if frappe.db.exists("User", user_email):
        return user_email

    user_doc = frappe.get_doc({
        "doctype": "User",
        "email": user_email,
        "first_name": doc.first_name,
        # "send_welcome_email": 1,
        "gender": doc.gender,
        "birth_date": doc.date_of_birth,
        "enabled": 1
    })

    user_doc.new_password = DUMMY_PASSWORD
    user_doc.insert(ignore_permissions=True)
    user_doc.add_roles("Employee")

    return user_email
