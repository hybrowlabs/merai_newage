


from merai_newage.merai_newage.doctype.batch_number_template.batch_number_template import create_batch_number

import frappe, json, uuid
import http
import math
from io import BytesIO

import frappe
from dateutil.relativedelta import relativedelta
from erpnext.manufacturing.doctype.bom.bom import (
    get_bom_item_rate,
    validate_bom_no,
)
from erpnext.manufacturing.doctype.manufacturing_settings.manufacturing_settings import (
    get_mins_between_operations,
)
from erpnext.stock.doctype.batch.batch import make_batch
from erpnext.stock.doctype.item.item import get_item_defaults, validate_end_of_life
from erpnext.stock.doctype.serial_no.serial_no import (
    get_available_serial_nos,
    get_serial_nos,
)
from erpnext.stock.stock_balance import get_planned_qty, update_bin_qty
from erpnext.stock.utils import (
    get_bin,
    get_latest_stock_qty,
    validate_warehouse_company,
)
from erpnext.utilities.transaction_base import validate_uom_is_integer
from frappe import _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.query_builder import Case
from frappe.query_builder.functions import Sum
from frappe.utils import (
    cint,
    date_diff,
    flt,
    get_datetime,
    get_link_to_form,
    getdate,
    now,
    nowdate,
    time_diff_in_hours,
)
from pypdf import PdfWriter
from pypika import functions as fn

def before_insert(doc, _method):
    # Check for back-dated transaction permission
    validate_back_dated_transaction(doc)
    item = doc.production_item
    batch_number = create_batch_number(doc)

    if not batch_number:
        frappe.log_error(
            f"Batch number generation failed for Work Order {doc.name}, item {item}. Skipping batch creation.",
            "Work Order Batch Creation"
        )
        return

    try:
        batch = frappe.new_doc("Batch")
        batch.batch_id = batch_number
        batch.custom_work_order = doc.name
        batch.custom_batch_number = batch_number.replace(item+"-", "")
        batch.item = item
        if doc.planned_start_date:
            batch.manufacturing_date = frappe.utils.getdate(doc.planned_start_date)
        batch.save(ignore_permissions=True)
        batch.batch_qty = doc.qty

        doc.custom_batch = batch.batch_id
        doc.custom_batch_number = batch_number.replace(item+"-", "")

    except Exception as e:
        frappe.log_error(
            f"Error creating batch for Work Order {doc.name}: {str(e)}",
            "Work Order Batch Creation"
        )
        pass

def validate_back_dated_transaction(doc):
    """
    Validates if the user has permission to create back-dated Work Orders
    based on Stock Settings configuration

    Time Complexity: O(1) for most cases, O(n) worst case where n = number of user roles
    """
    if not doc.planned_start_date:
        return

    planned_date = frappe.utils.getdate(doc.planned_start_date)
    today = frappe.utils.getdate(frappe.utils.today())

    if planned_date >= today:
        return

    stock_settings = frappe.get_single("Stock Settings")
    allowed_role = stock_settings.role_allowed_to_create_edit_back_dated_transactions

    if not allowed_role:
        return

    user_roles = frappe.get_roles(frappe.session.user)

    if allowed_role not in user_roles:
        frappe.throw(
            f"You do not have permission to create back-dated Work Orders. "
            f"Only users with the '{allowed_role}' role can create Work Orders "
            f"with a planned start date earlier than today.",
            title="Permission Denied",
        )


@frappe.whitelist()
def print_work_order_async(name):
    task_id = str(uuid.uuid4())
    return _print_work_order(name, task_id)

def _print_work_order(name, task_id=None):
    work_order_doc = frappe.get_doc("Work Order", name)
    pdf_writer = PdfWriter()

    default_letter_head = frappe.get_all(
        "Letter Head",
        filters={"is_default": 1},
        fields=["name"],
        limit=1
    )

    frappe.publish_progress(
        percent=1,
        title="Generating PDF",
        description=_("Preparing to generate PDF"),
        task_id=task_id,
    )

    # Print documents in sequence
    print_documents_in_sequence(
        work_order_doc, pdf_writer, task_id=task_id, default_letter_head=default_letter_head
    )

    with BytesIO() as merged_pdf:
        pdf_writer.write(merged_pdf)
        if task_id:
            _file = frappe.get_doc(
                {
                    "doctype": "File",
                    "file_name": f"{name}-{task_id}.pdf",
                    "content": merged_pdf.getvalue(),
                    "is_private": 1,
                }
            )
            frappe.local.response.filename = f"work_order_{name}.pdf"
            _file.save()
            frappe.local.response.filecontent = _file.unique_url
            frappe.publish_realtime(
                f"task_complete:{task_id}", message={"file_url": _file.unique_url}
            )
        else:
            frappe.local.response.filecontent = merged_pdf.getvalue()
            frappe.local.response.filetype = "PDF"

def print_documents_in_sequence(work_order_doc, pdf_writer, task_id=None, default_letter_head=None):
    """Print all documents in the correct sequence"""

    # Step 1: Print Work Order first (if custom_work_order_print_format is specified)
    if hasattr(work_order_doc, 'custom_work_order_print_format') and work_order_doc.custom_work_order_print_format:
        try:
            frappe.logger("print").info(f"Printing Work Order {work_order_doc.name} with custom format")
            pdf_writer = frappe.get_print(
                "Work Order",
                work_order_doc.name,
                print_format=work_order_doc.custom_work_order_print_format,
                as_pdf=True,
                no_letterhead=0,
                letterhead=default_letter_head[0].name if default_letter_head else None,
                output=pdf_writer,
                pdf_options={"page-size": "A4", "encoding": "UTF-8"},
            )
            frappe.logger("print").info(f"Successfully printed Work Order: {work_order_doc.name}")
        except Exception as e:
            frappe.log_error(
                f"Error printing Work Order {work_order_doc.name}: {str(e)}",
                "Work Order Print Error"
            )
    print_workorder_attachments(work_order_doc.name,pdf_writer, task_id)
    # Step 2: Print Stock Entries for the Work Order
    # print_stock_entries_for_work_order(work_order_doc, pdf_writer, default_letter_head)

    # Step 3: Print Job Cards and their respective QI documents in sequence
    job_cards = frappe.get_list(
        "Job Card",
        filters=[
            ["Job Card", "docstatus", "=", 1],
            ["Job Card", "work_order", "=", work_order_doc.name],
        ],
        fields=["name", "sequence_id"],
        order_by="sequence_id asc",
    )

    total_docs = len(job_cards) + 2  # +2 for Work Order and Stock Entries
    current_step = 3  # We've already done WO and Stock Entries

    for job_card_data in job_cards:
        try:
            job_card_doc = frappe.get_doc("Job Card", job_card_data.name)
            frappe.logger("print").info(f"Processing Job Card {job_card_doc.name} (Sequence: {job_card_data.sequence_id})")

            # Print Job Card
            print_single_job_card(job_card_doc, pdf_writer, default_letter_head)

            # Print Quality Inspections for this specific Job Card
            print_quality_inspections_for_job_card(job_card_doc, pdf_writer, default_letter_head)

        except Exception as e:
            if task_id:
                frappe.publish_realtime(task_id=task_id, message={"message": "Failed"})
            frappe.log_error(
                f"Error processing Job Card {job_card_data.name}: {str(e)}",
                "Work Order Print Job Card Error"
            )

        current_step += 1
        if task_id:
            frappe.publish_progress(
                percent=(current_step / total_docs) * 100,
                title="Generating PDF",
                description=_(
                    "Processing Job Card {0} of {1}".format(current_step - 2, len(job_cards))
                ),
                task_id=task_id,
            )

    if task_id:
        frappe.publish_realtime(task_id=task_id, message={"message": "Success"})

def print_single_job_card(job_card_doc, pdf_writer, default_letter_head):
    """Print a single Job Card"""
    try:
        # Use custom print format if available, otherwise use default
        print_format = job_card_doc.custom_print_format if hasattr(job_card_doc, 'custom_print_format') and job_card_doc.custom_print_format else None

        frappe.logger("print").info(f"Printing Job Card {job_card_doc.name} with print format: {print_format}")

        pdf_writer = frappe.get_print(
            "Job Card",
            job_card_doc.name,
            print_format=print_format,
            as_pdf=True,
            no_letterhead=0,
            letterhead=default_letter_head[0].name if default_letter_head else None,
            output=pdf_writer,
            pdf_options={"page-size": "A4", "encoding": "UTF-8"},
        )

        frappe.logger("print").info(f"Successfully printed Job Card: {job_card_doc.name}")

    except Exception as e:
        frappe.log_error(
            f"Error printing Job Card {job_card_doc.name}: {str(e)}",
            "Job Card Print Error"
        )

def print_stock_entries_for_work_order(work_order_doc, pdf_writer, default_letter_head):
    """Print all Stock Entry documents of type 'Material Transfer for Manufacture' for the Work Order"""

    try:
        # Get Stock Entries of type 'Material Transfer for Manufacture' linked to this Work Order
        stock_entries = frappe.get_all(
            "Stock Entry",
            filters={
                "stock_entry_type": "Material Transfer for Manufacture",
                "work_order": work_order_doc.name,
                "docstatus": 1  # Only submitted stock entries
            },
            fields=["name"],
            order_by="posting_date, posting_time"
        )

        frappe.logger("print").info(f"Found {len(stock_entries)} Material Transfer Stock Entries for Work Order {work_order_doc.name}")

        for stock_entry in stock_entries:
            print_single_stock_entry(
                stock_entry.name,
                pdf_writer,
                default_letter_head,
                work_order_doc
            )

    except Exception as e:
        frappe.log_error(
            f"Error getting Stock Entries for Work Order {work_order_doc.name}: {str(e)}",
            "Work Order Print Stock Entry Error"
        )

def print_quality_inspections_for_job_card(job_card_doc, pdf_writer, default_letter_head):
    """Print all Quality Inspection documents linked to this specific Job Card"""

    # Get the operation to check for QI print format
    operation_doc = None
    if job_card_doc.operation:
        try:
            operation_doc = frappe.get_doc("Operation", job_card_doc.operation)
        except:
            pass

    # Main Quality Inspection
    if job_card_doc.quality_inspection:
        print_single_quality_inspection(
            job_card_doc.quality_inspection,
            pdf_writer,
            default_letter_head,
            operation_doc
        )

    # Additional Quality Inspections
    additional_qis = [
        getattr(job_card_doc, 'custom_quality_inspection_3', None),
        getattr(job_card_doc, 'custom_quality_inspection_4', None),
        getattr(job_card_doc, 'custom_quality_inspection_5', None),
        getattr(job_card_doc, 'custom_quality_inspection_6', None)
    ]

    for qi_name in additional_qis:
        if qi_name:
            print_single_quality_inspection(
                qi_name,
                pdf_writer,
                default_letter_head,
                operation_doc
            )

    # Bio Burden QC
    if hasattr(job_card_doc, 'custom_bio_burden_qc') and job_card_doc.custom_bio_burden_qc:
        print_single_quality_inspection(
            job_card_doc.custom_bio_burden_qc,
            pdf_writer,
            default_letter_head,
            operation_doc
        )

def print_single_quality_inspection(qi_name, pdf_writer, default_letter_head, operation_doc=None):
    """Print a single Quality Inspection document"""
    try:
        qi_doc = frappe.get_doc("Quality Inspection", qi_name)

        # Log for debugging
        frappe.logger("print").info(f"Attempting to print Quality Inspection: {qi_name}")

        # Determine print format priority:
        # 1. From QI document's custom_print_format
        # 2. From Operation's custom_qi_print_format
        # 3. Use default Quality Inspection print format if none specified

        print_format = None

        if hasattr(qi_doc, 'custom_print_format') and qi_doc.custom_print_format:
            print_format = qi_doc.custom_print_format
            frappe.logger("print").info(f"Using QI custom print format: {print_format}")
        elif operation_doc and hasattr(operation_doc, 'custom_qi_print_format') and operation_doc.custom_qi_print_format:
            print_format = operation_doc.custom_qi_print_format
            frappe.logger("print").info(f"Using Operation custom print format: {print_format}")
        else:
            # Try to find a default Quality Inspection print format
            default_formats = frappe.get_list(
                "Print Format",
                filters={"doc_type": "Quality Inspection", "disabled": 0},
                pluck="name",
                limit=1
            )
            if default_formats:
                print_format = default_formats[0]
                frappe.logger("print").info(f"Using default QI print format: {print_format}")

        # Print the QI
        pdf_writer = frappe.get_print(
            "Quality Inspection",
            qi_doc.name,
            print_format=print_format,
            as_pdf=True,
            no_letterhead=0,
            letterhead=default_letter_head[0].name if default_letter_head else None,
            output=pdf_writer,
            pdf_options={"page-size": "A4", "encoding": "UTF-8"},
        )
        frappe.logger("print").info(f"Successfully printed Quality Inspection: {qi_name}")

    except Exception as e:
        frappe.log_error(
            f"Error printing Quality Inspection {qi_name}: {str(e)}",
            "Work Order Print QI Error"
        )

def print_single_stock_entry(stock_entry_name, pdf_writer, default_letter_head, work_order_doc=None):
    """Print a single Stock Entry document"""
    try:
        stock_entry_doc = frappe.get_doc("Stock Entry", stock_entry_name)

        # Log for debugging
        frappe.logger("print").info(f"Attempting to print Stock Entry: {stock_entry_name}")



        print_format = None

        if hasattr(stock_entry_doc, 'custom_print_format') and stock_entry_doc.custom_print_format:
            print_format = stock_entry_doc.custom_print_format
            frappe.logger("print").info(f"Using Stock Entry custom print format: {print_format}")
        elif work_order_doc and hasattr(work_order_doc, 'custom_stock_entry_print_format') and work_order_doc.custom_stock_entry_print_format:
            print_format = work_order_doc.custom_stock_entry_print_format
            frappe.logger("print").info(f"Using Work Order Stock Entry print format: {print_format}")

        if not print_format:
            # Try to find a default Stock Entry print format
            default_formats = frappe.get_list(
                "Print Format",
                filters={"doc_type": "Stock Entry", "disabled": 0},
                pluck="name",
                limit=1
            )
            if default_formats:
                print_format = default_formats[0]
                frappe.logger("print").info(f"Using default Stock Entry print format: {print_format}")

        # Print the Stock Entry
        pdf_writer = frappe.get_print(
            "Stock Entry",
            stock_entry_doc.name,
            print_format=print_format,
            as_pdf=True,
            no_letterhead=0,
            letterhead=default_letter_head[0].name if default_letter_head else None,
            output=pdf_writer,
            pdf_options={"page-size": "A4", "encoding": "UTF-8"},
        )

        frappe.logger("print").info(f"Successfully printed Stock Entry: {stock_entry_name}")

    except Exception as e:
        frappe.log_error(
            f"Error printing Stock Entry {stock_entry_name}: {str(e)}",
            "Work Order Print Stock Entry Error"
        )




@frappe.whitelist()
def print_full_bmr(name):
    """Print BMRs for all linked work orders, then print current work order BMR at the end"""
    # print("------------474--------", name)

    work_order_doc = frappe.get_doc("Work Order", name)
    pdf_writer = PdfWriter()

    # Get default letterhead
    default_letter_head = frappe.get_all(
        "Letter Head",
        filters={"is_default": 1},
        fields=["name"],
        limit=1
    )

    # Get all job cards for current work order (only draft ones, docstatus=0)
    job_cards = frappe.db.sql(
        "SELECT name FROM `tabJob Card` WHERE work_order = %s ",
        name,
        as_dict=1
    )
    # print("======job_card======475", job_cards)

    # Collect unique linked work orders (excluding current work order)
    linked_work_orders = set()

    for job_card in job_cards:
        job_card_doc = frappe.get_doc("Job Card", job_card.get('name'))
        print("jobcard_doc=====", job_card_doc.name)

        # Loop through custom_jobcard_operation_details child table
        for detail in job_card_doc.custom_jobcard_opeartion_deatils:
            print("detail---", detail)

            # Check if work_order_reference exists and is different from current work order
            if detail.work_order_reference and detail.work_order_reference != name:
                linked_work_orders.add(detail.work_order_reference)

    # print("linked_work_orders--------", list(linked_work_orders))

    # Step 1: Print all linked work orders first
    for linked_wo_name in sorted(linked_work_orders):  # Sort for consistent order
        try:
            print(f"Printing linked Work Order: {linked_wo_name}")
            linked_wo_doc = frappe.get_doc("Work Order", linked_wo_name)

            # Print documents for linked work order
            print_documents_in_sequence(
                linked_wo_doc,
                pdf_writer,
                task_id=None,
                default_letter_head=default_letter_head
            )

        except Exception as e:
            frappe.log_error(
                f"Error printing linked Work Order {linked_wo_name}: {str(e)}",
                "Print Full BMR - Linked Work Order Error"
            )

    # Step 2: Print current work order BMR at the end
    try:
        # print(f"Printing current Work Order: {name}")
        print_documents_in_sequence(
            work_order_doc,
            pdf_writer,
            task_id=None,
            default_letter_head=default_letter_head
        )
    except Exception as e:
        frappe.log_error(
            f"Error printing current Work Order {name}: {str(e)}",
            "Print Full BMR - Current Work Order Error"
        )

    # Step 3: Save PDF as a File document and return URL (same format as print_work_order_async)
    with BytesIO() as merged_pdf:
        pdf_writer.write(merged_pdf)

        # Create a File document
        _file = frappe.get_doc({
            "doctype": "File",
            "file_name": f"full_dhr_{name}.pdf",
            "content": merged_pdf.getvalue(),
            "is_private": 1,
        })
        _file.save()

        # Set response exactly like print_work_order_async does
        frappe.local.response.filename = f"full_dhr_{name}.pdf"
        frappe.local.response.filecontent = _file.unique_url

        print(f"Successfully generated Full DHR for Work Order: {name}")



@frappe.whitelist()
def print_workorder_attachments(work_order_name, pdf_writer, task_id=None):
    """Print attachments from Work Order  if any exist"""
    # print("==================2266--------------------------", work_order_name)

    if not work_order_name:
        raise Exception("Work order name is empty for attachments")

    attachments = frappe.get_all(
        "File",
        filters={
            "attached_to_doctype": "Work Order",
            "attached_to_name": work_order_name,
        },
        fields=["name", "file_name", "file_url"]
    )
    # print("attachments======pp=====2276", attachments)

    # Import required libraries for PDF handling
    from pypdf import PdfReader
    import os
    import requests
    from io import BytesIO

    for attachment in attachments:
        if attachment.file_name.lower().endswith('.pdf'):
            try:
                file_doc = frappe.get_doc("File", attachment.name)
                print(f"Adding attachment: {attachment.file_name}")

                # Get the file content
                file_content = None

                # Method 1: Try to get file content directly from file_doc
                if hasattr(file_doc, 'get_content'):
                    file_content = file_doc.get_content()
                elif file_doc.content:
                    file_content = file_doc.content
                else:
                    # Method 2: Try to read from file_url if available
                    if file_doc.file_url:
                        # Check if it's a local file path
                        if file_doc.file_url.startswith('/files/'):
                            # Construct full file path
                            site_path = frappe.utils.get_site_path()
                            file_path = os.path.join(site_path, 'public', file_doc.file_url.lstrip('/'))

                            if os.path.exists(file_path):
                                with open(file_path, 'rb') as f:
                                    file_content = f.read()
                            else:
                                print(f"File not found at path: {file_path}")
                                continue
                        else:
                            # If it's a full URL, try to download it
                            try:
                                response = requests.get(file_doc.file_url, timeout=30)
                                if response.status_code == 200:
                                    file_content = response.content
                                else:
                                    print(f"Failed to download file: {file_doc.file_url}")
                                    continue
                            except requests.RequestException as e:
                                print(f"Error downloading file {file_doc.file_url}: {str(e)}")
                                continue

                # If we have file content, merge it with the main PDF
                if file_content:
                    try:
                        # Create a PdfReader from the attachment content
                        attachment_pdf = PdfReader(BytesIO(file_content))

                        # Add all pages from the attachment to the main PDF writer
                        for page_num in range(len(attachment_pdf.pages)):
                            page = attachment_pdf.pages[page_num]
                            pdf_writer.add_page(page)

                        print(f"Successfully added {len(attachment_pdf.pages)} pages from {attachment.file_name}")

                    except Exception as pdf_error:
                        print(f"Error processing PDF attachment {attachment.file_name}: {str(pdf_error)}")
                        frappe.log_error(f"Error processing PDF attachment {attachment.file_name}: {str(pdf_error)}", "Work order Attachment PDF Processing")
                else:
                    print(f"Could not retrieve content for attachment: {attachment.file_name}")

            except Exception as e:
                print(f"Error adding attachment {attachment.file_name}: {str(e)}")
                frappe.log_error(f"Error processing attachment {attachment.file_name}: {str(e)}", "Work Order Attachment")

    frappe.publish_progress(
        percent=15,
        title="Generating PDF",
        description=_("Added Work Order attachments"),
        task_id=task_id,
    )










@frappe.whitelist()
def create_stock_entry_for_received_material_on_submit(doc_name):
    doc = frappe.get_doc("Work Order", doc_name)

    stock_entry = frappe.new_doc("Stock Entry")
    stock_entry.stock_entry_type = "Material Receipt"
    stock_entry.posting_date = frappe.utils.nowdate()
    stock_entry.posting_time = frappe.utils.nowtime()
    stock_entry.company = "Merai Newage Pvt. Ltd."

    for item in doc.required_items:
        batch = frappe.get_value("Item", item.item_code, "has_batch_no")
        batch_no = ""
        if batch:
            batch_list = frappe.get_all("Batch", filters={"item": item.item_code}, pluck="name")
            count = len(batch_list) + 1
            new_batch_name = f"{item.item_code}-{count}"

            batch_doc = frappe.new_doc("Batch")
            batch_doc.item = item.item_code
            batch_doc.batch_id = new_batch_name
            batch_doc.batch_qty = item.required_qty
            batch_doc.insert(ignore_permissions=True)
            batch_doc.submit()
            batch_no = new_batch_name

        stock_entry_item = stock_entry.append("items", {})
        stock_entry_item.item_code = item.item_code
        stock_entry_item.item_name = item.item_name
        stock_entry_item.uom = item.stock_uom
        stock_entry_item.qty = item.required_qty
        stock_entry_item.t_warehouse = item.source_warehouse
        stock_entry_item.basic_rate = item.rate
        stock_entry_item.basic_amount = item.amount
        stock_entry_item.batch_no = batch_no if batch else None

    stock_entry.insert()
    stock_entry.submit()
    frappe.db.commit()
    return {
        "status": "success",
        "stock_entry": stock_entry.name,
        "message": f"Stock Entry {stock_entry.name} created successfully."
    }




@frappe.whitelist()
def create_stock_entry_on_submit(doc_name):
    doc = frappe.get_doc("Work Order", doc_name)

    stock_entry = frappe.new_doc("Stock Entry")
    stock_entry.stock_entry_type = "Material Transfer for Manufacture"
    stock_entry.work_order = doc_name
    stock_entry.posting_date = frappe.utils.nowdate()
    stock_entry.posting_time = frappe.utils.nowtime()
    stock_entry.company = "Merai Newage Pvt. Ltd."
    stock_entry.from_bom = 1
    stock_entry.use_multi_level_bom = 1
    stock_entry.bom_no = doc.bom_no
    stock_entry.fg_completed_qty = doc.qty
    stock_entry.to_warehouse = doc.wip_warehouse

    total_amount = 0
    for item in doc.required_items:
        stock_entry_item = stock_entry.append("items", {})
        stock_entry_item.item_code = item.item_code
        stock_entry_item.item_name = item.item_name
        stock_entry_item.uom = item.stock_uom
        stock_entry_item.qty = item.required_qty
        stock_entry_item.s_warehouse = item.source_warehouse
        stock_entry_item.t_warehouse = doc.wip_warehouse
        stock_entry_item.basic_rate = item.rate
        stock_entry_item.basic_amount = item.amount

        total_amount += item.amount

    stock_entry.total_incoming_value = total_amount
    stock_entry.insert()
    stock_entry.submit()
    frappe.db.commit()
    return {
        "status": "success",
        "stock_entry": stock_entry.name,
        "message": f"Stock Entry {stock_entry.name} created successfully."
    }



@frappe.whitelist()
def complete_work_order(doc_name):
    doc = frappe.get_doc("Work Order", doc_name)

    stock_entry = frappe.new_doc("Stock Entry")
    stock_entry.stock_entry_type = "Manufacture"
    stock_entry.work_order = doc_name
    stock_entry.posting_date = frappe.utils.nowdate()
    stock_entry.posting_time = frappe.utils.nowtime()
    stock_entry.company = "Merai Newage Pvt. Ltd."
    stock_entry.from_bom = 1
    stock_entry.use_multi_level_bom = 1
    stock_entry.bom_no = doc.bom_no
    stock_entry.fg_completed_qty = doc.qty

    for item in doc.required_items:
        stock_entry_item = stock_entry.append("items", {})
        stock_entry_item.item_code = item.item_code
        stock_entry_item.item_name = item.item_name
        stock_entry_item.uom = item.stock_uom
        stock_entry_item.qty = item.required_qty
        stock_entry_item.s_warehouse = doc.wip_warehouse
        stock_entry_item.basic_rate = item.rate
        stock_entry_item.basic_amount = item.amount


    batch_no = ""
    batch = frappe.get_value("Item", doc.production_item, "has_batch_no")
    if batch:
        batch_list = frappe.get_all("Batch", filters={"item": doc.production_item}, pluck="name")
        count = len(batch_list) + 1
        new_batch_name = f"{doc.production_item}-{count}"

        batch_doc = frappe.new_doc("Batch")
        batch_doc.item = doc.production_item
        batch_doc.batch_id = new_batch_name
        batch_doc.batch_qty = doc.qty
        batch_doc.insert(ignore_permissions=True)
        batch_doc.submit()
        batch_no = new_batch_name

    stock_entry_item = stock_entry.append("items", {})
    stock_entry_item.item_code = doc.production_item
    stock_entry_item.item_name = doc.item_name
    stock_entry_item.uom = doc.stock_uom
    stock_entry_item.qty = doc.qty
    stock_entry_item.t_warehouse = doc.fg_warehouse
    stock_entry_item.is_finished_item = 1
    stock_entry_item.use_serial_batch_fields = 1
    stock_entry_item.batch_no = batch_no if batch else None

    stock_entry.insert()
    stock_entry.submit()
    frappe.db.commit()

    return {
        "status": "success",
        "stock_entry": stock_entry.name,
        "batch_no": batch_no,
        "message": f"Stock Entry {stock_entry.name} created successfully."
    }

# from erpnext.manufacturing.doctype.work_order.work_order import WorkOrder


# class CustomWorkOrder(WorkOrder):
@frappe.whitelist()
def on_submit(doc, method=None):
    create_stock_entry_for_received_material_on_submit(doc.name)
    create_stock_entry_on_submit(doc.name)
    frappe.msgprint(f"{doc.name} work order has been released")



@frappe.whitelist()
def create_fg_consumption_entry(doc_name, batch_no):
    doc = frappe.get_doc("Work Order", doc_name)

    stock_entry = frappe.new_doc("Stock Entry")

    stock_entry.stock_entry_type = "Material Issue"
    stock_entry.t_warehouse = doc.fg_warehouse
    stock_entry.company = "Merai Newage Pvt. Ltd."
    stock_entry.posting_date = frappe.utils.nowdate()
    stock_entry.posting_time = frappe.utils.nowtime()


    stock_entry_item = stock_entry.append("items", {})
    stock_entry_item.item_code = doc.production_item
    stock_entry_item.item_name = doc.item_name
    stock_entry_item.uom = doc.stock_uom
    stock_entry_item.qty = doc.qty
    stock_entry_item.s_warehouse = doc.fg_warehouse
    stock_entry.use_serial_batch_fields = 1
    stock_entry.batch_no = batch_no

    stock_entry.insert()
    stock_entry.submit()
    frappe.db.commit()
