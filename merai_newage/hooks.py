app_name = "merai_newage"
app_title = "Merai Newage"
app_publisher = "Siddhant Hybrowlabs"
app_description = "Merai Newage"
app_email = "sidhant@mail.hybrowlabs.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "merai_newage",
# 		"logo": "/assets/merai_newage/logo.png",
# 		"title": "Merai Newage",
# 		"route": "/merai_newage",
# 		"has_permission": "merai_newage.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/merai_newage/css/merai_newage.css"
# app_include_js = "/assets/merai_newage/js/merai_newage.js"

# include js, css files in header of web template
# web_include_css = "/assets/merai_newage/css/merai_newage.css"
# web_include_js = "/assets/merai_newage/js/merai_newage.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "merai_newage/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "merai_newage/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "merai_newage.utils.jinja_methods",
# 	"filters": "merai_newage.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "merai_newage.install.before_install"
# after_install = "merai_newage.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "merai_newage.uninstall.before_uninstall"
# after_uninstall = "merai_newage.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "merai_newage.utils.before_app_install"
# after_app_install = "merai_newage.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "merai_newage.utils.before_app_uninstall"
# after_app_uninstall = "merai_newage.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "merai_newage.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"merai_newage.tasks.all"
# 	],
# 	"daily": [
# 		"merai_newage.tasks.daily"
# 	],
# 	"hourly": [
# 		"merai_newage.tasks.hourly"
# 	],
# 	"weekly": [
# 		"merai_newage.tasks.weekly"
# 	],
# 	"monthly": [
# 		"merai_newage.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "merai_newage.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "merai_newage.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "merai_newage.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["merai_newage.utils.before_request"]
# after_request = ["merai_newage.utils.after_request"]

# Job Events
# ----------
# before_job = ["merai_newage.utils.before_job"]
# after_job = ["merai_newage.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"merai_newage.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }



scheduler_events = {
    "weekly": [
        "merai_newage.merai_newage.utils.supplier_deletions.cleanup_temporary_suppliers"
    ]
}

override_whitelisted_methods = {
        # "erpnext.stock.doctype.material_request.material_request.make_stock_entry": "merai_newage.overrides..material_request_override.make_stock_entry",
        #     "erpnext.controllers.buying_controller.auto_make_assets": 
        # "merai_newage.overrides.purchase_receipt.auto_make_assets",
        "erpnext.controllers.buying_controller.auto_make_assets": 
        "merai_newage.overrides.purchase_receipt.auto_make_assets",
    
    # "erpnext.stock.doctype.purchase_receipt.purchase_receipt.make_asset": 
    #     "merai_newage.overrides.purchase_receipt.custom_make_asset",

    # "Stock Entry": "chatnext_manufacturing.config.py.stock_entry_override.StockEntry",
        # "erpnext.stock.doctype.material_request.material_request.make_stock_entry": "merai_newage.overrides.material_request_override.make_stock_entry",

}


doctype_js = {
    "Batch":"public/js/batch_script.js",
    "Job Card":"public/js/line_clearance.js",
    "Job Card":"public/js/job_card.js",
    "Quality Inspection":"public/js/quality_inspection.js",
    "Work Order":"public/js/work_order.js",
    "Stock Entry":"public/js/stock_entry.js",
    "Employee":"public/js/employee.js",
    "Material Request":"public/js/material_request.js",
    "Pre Alert": "public/js/pre_alert.js",
    "Purchase Order":"public/js/purchase_order.js",
}

# doc_events = {
#     "Batch": {
#         "before_insert": "merai_newage.merai_newage.doctype.custom_batch_number_template.custom_batch_number_template.generate_batch_number",
#         "validate": "merai_newage.merai_newage.doctype.custom_batch_number_template.custom_batch_number_template.generate_batch_number"
#     }
# }

doc_events = {
    "Work Order": {
        "before_insert": "merai_newage.overrides.work_order.before_insert",
        "on_submit": "merai_newage.overrides.work_order.on_submit",
        "autoname": "merai_newage.overrides.work_order.autoname",
        # "on_submit": "merai_newage.merai_newage.doctype.robot_tracker.robot_tracker.create_robot_tracker",

        # "on_update_after_submit": "merai_newage.merai_newage.doctype.robot_tracker.robot_tracker.create_robot_tracker",

    },
    "Job Card": {
        "before_submit": "merai_newage.overrides.job_card.before_submit",
        "on_submit": "merai_newage.overrides.job_card.on_submit",
        "before_insert": "merai_newage.overrides.job_card.before_insert",
        "before_save":"merai_newage.overrides.job_card.before_save",
		"before_validate": "merai_newage.overrides.apply_job_card_overrides"
    },
    "Quality Inspection": {
        "before_save": "merai_newage.overrides.quality_inspection.before_save",
        "on_submit": "merai_newage.overrides.quality_inspection.on_submit",        
    },
    "Request for Quotation": {
        "before_validate": "merai_newage.merai_newage.doctype.rfq_entry.rfq_entry.allow_duplicate_suppliers_with_different_emails",
        "validate": "merai_newage.overrides.request_for_quotation.copy_workflow_attachments_from_pickup_request",
        "before_save": "merai_newage.overrides.rfq.before_save_request_for_quotation",
        "validate": "merai_newage.overrides.rfq.validate_request_for_quotation",
    },
    "Pre Alert": {
        "validate": "merai_newage.overrides.pre_alert.validate_igcr_category"
    },
     "Material Request": {
        "validate": "merai_newage.overrides.material_request.validate_material_request",
        "on_submit": "merai_newage.overrides.material_request.on_submit_material_request",
        "on_cancel": "merai_newage.overrides.material_request.on_cancel_material_request",
    },
    "Supplier Quotation": {
        "before_save": "merai_newage.overrides.supplier_quotation.before_save_supplier_quotation",
        "validate": "merai_newage.overrides.supplier_quotation.validate_supplier_quotation",
    },
    "Purchase Order": {
        "before_save": "merai_newage.overrides.purchase_order.before_save_purchase_order",
        "validate": "merai_newage.overrides.purchase_order.validate_purchase_order",
        "on_submit": "merai_newage.overrides.purchase_order.on_submit_purchase_order",
        "on_cancel": "merai_newage.overrides.purchase_order.on_cancel_purchase_order",
    },
    "Purchase Receipt": {
        "before_save": "merai_newage.overrides.purchase_receipt.before_save_purchase_receipt",
        "validate": "merai_newage.overrides.purchase_receipt.validate_purchase_receipt",
        "on_submit": "merai_newage.overrides.purchase_receipt.on_submit_purchase_receipt",
        "on_cancel": "merai_newage.overrides.purchase_receipt.on_cancel_purchase_receipt",
    },
     "Gate Entry": {
        "before_save": "merai_newage.overrides.gate_entry_override.before_save_gate_entry",
        "validate": "merai_newage.overrides.gate_entry_override.validate_gate_entry",
        "on_submit": "merai_newage.overrides.gate_entry_override.on_submit_gate_entry",
        "on_cancel": "merai_newage.overrides.gate_entry_override.on_cancel_gate_entry",
    },

}
# In your custom app's hooks.py

fixtures = [
    {"dt": "Batch Number Template"},
    # {
    #     "dt": "Workflow",
    # },
    {
        "dt": "Web Page",
    },
    #  {
    #     "dt": "Workflow State",
    # },
# {"dt": "Property Setter",  "filters": [ ["name", "=", "Work Order-use_multi_level_bom-Check"]] }
    # {"dt": "Property Setter",  "filters": [ ["name", "=", "Material Request-material_request_type-options"]] }


]
page_js = {"print": "public/js/print.js"}


override_doctype_class = {
    # "Job Card": "merai_newage.overrides.job_card.CustomJobCard",
    # "Work Order":"merai_newage.overrides.work_order.CustomWorkOrder"
}
app_include_css = [
    "merai_newage.public.css.safety_check_custom.css"
]

app_include_js = [
    "/assets/merai_newage/js/dimension_calculation.js",
    "/assets/merai_newage/js/pickup_request.js",
    "/assets/merai_newage/js/workflow_attachment.js"
]