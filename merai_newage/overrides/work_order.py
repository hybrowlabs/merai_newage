

# from merai_newage.merai_newage.doctype.batch_number_template.batch_number_template import create_batch_number

# import frappe, json, uuid
# import http
# import math
# from io import BytesIO

# import frappe
# from dateutil.relativedelta import relativedelta
# from erpnext.manufacturing.doctype.bom.bom import (
#     get_bom_item_rate,
#     validate_bom_no,
# )
# from erpnext.manufacturing.doctype.manufacturing_settings.manufacturing_settings import (
#     get_mins_between_operations,
# )
# from erpnext.stock.doctype.batch.batch import make_batch
# from erpnext.stock.doctype.item.item import get_item_defaults, validate_end_of_life
# from erpnext.stock.doctype.serial_no.serial_no import (
#     get_available_serial_nos,
#     get_serial_nos,
# )
# from erpnext.stock.stock_balance import get_planned_qty, update_bin_qty
# from erpnext.stock.utils import (
#     get_bin,
#     get_latest_stock_qty,
#     validate_warehouse_company,
# )
# from erpnext.utilities.transaction_base import validate_uom_is_integer
# from frappe import _
# from frappe.model.document import Document
# from frappe.model.mapper import get_mapped_doc
# from frappe.query_builder import Case
# from frappe.query_builder.functions import Sum
# from frappe.utils import (
#     cint,
#     date_diff,
#     flt,
#     get_datetime,
#     get_link_to_form,
#     getdate,
#     now,
#     nowdate,
#     time_diff_in_hours,
# )
# from pypdf import PdfWriter
# from pypika import functions as fn


# def before_insert(doc, _method):
#     item = doc.production_item
#     batch_number = create_batch_number(doc)
  
#     if not batch_number:
#         frappe.log_error(
#             f"Batch number generation failed for Work Order {doc.name}, item {item}. Skipping batch creation.",
#             "Work Order Batch Creation"
#         )
#         return
    
#     try:
#         batch = frappe.new_doc("Batch")
#         batch.batch_id = batch_number
#         batch.custom_work_order = doc.name
#         batch.custom_batch_number = batch_number.replace(item+"-", "")
#         batch.item = item
#         batch.save(ignore_permissions=True)
#         batch.batch_qty = doc.qty

#         doc.custom_batch = batch.batch_id
#         doc.custom_batch_number = batch_number.replace(item+"-", "")
        
#     except Exception as e:
#         frappe.log_error(
#             f"Error creating batch for Work Order {doc.name}: {str(e)}",
#             "Work Order Batch Creation"
#         )
#         pass


# @frappe.whitelist()
# def print_work_order_async(name):
#     task_id = str(uuid.uuid4())
#     return _print_work_order(name, task_id)


# def _print_work_order(name, task_id=None):
#     work_order_doc = frappe.get_doc("Work Order", name)
#     pdf_writer = PdfWriter()
    
#     default_letter_head = frappe.get_all(
#         "Letter Head",
#         filters={"is_default": 1},
#         fields=["name"],
#         limit=1
#     )

#     frappe.publish_progress(
#         percent=1,
#         title="Generating PDF",
#         description=_("Preparing to generate PDF"),
#         task_id=task_id,
#     )

#     # Print job cards with quality inspections
#     print_job_cards(
#         name, pdf_writer, task_id=task_id, default_letter_head=default_letter_head
#     )

#     with BytesIO() as merged_pdf:
#         pdf_writer.write(merged_pdf)
#         if task_id:
#             _file = frappe.get_doc(
#                 {
#                     "doctype": "File",
#                     "file_name": f"{name}-{task_id}.pdf",
#                     "content": merged_pdf.getvalue(),
#                     "is_private": 1,
#                 }
#             )
#             frappe.local.response.filename = f"work_order_{name}.pdf"
#             _file.save()
#             frappe.local.response.filecontent = _file.unique_url
#             frappe.publish_realtime(
#                 f"task_complete:{task_id}", message={"file_url": _file.unique_url}
#             )
#         else:
#             frappe.local.response.filecontent = merged_pdf.getvalue()
#             frappe.local.response.filetype = "PDF"


# def print_job_cards(name, pdf_writer, task_id=None, default_letter_head=None):
#     job_cards = frappe.get_list(
#         "Job Card",
#         filters=[
#             ["Job Card", "docstatus", "=", 1],
#             ["Job Card", "work_order", "=", name],
#         ],
#         pluck="name",
#         order_by="sequence_id asc",
#     )
    
#     total_docs = len(job_cards)
#     count = 1
    
#     for job_card in job_cards:
#         try:
#             frappe.logger("print").info(f"Generating PDF for Job Card {job_card}")
#             job_card_doc = frappe.get_doc("Job Card", job_card)

#             # Print Job Card - use custom print format if available, otherwise use default
#             print_format = job_card_doc.custom_print_format if job_card_doc.custom_print_format else None
            
#             pdf_writer = frappe.get_print(
#                 "Job Card",
#                 job_card_doc.name,
#                 print_format=print_format,
#                 as_pdf=True,
#                 no_letterhead=0,
#                 letterhead=default_letter_head[0].name if default_letter_head else None,
#                 output=pdf_writer,
#                 pdf_options={"page-size": "A4", "encoding": "UTF-8"},
#             )

#             # Print Quality Inspections for this Job Card
#             print_quality_inspections_for_job_card(job_card_doc, pdf_writer, default_letter_head)

#         except Exception as e:
#             if task_id:
#                 frappe.publish_realtime(task_id=task_id, message={"message": "Failed"})
#             frappe.throw(e.__str__(), exc=frappe.PrintFormatError)
        
#         count += 1
#         if task_id:
#             frappe.publish_progress(
#                 percent=(count / total_docs) * 100,
#                 title="Generating PDF",
#                 description=_(
#                     "Generating PDF for Job Card {0} of {1}".format(count, total_docs)
#                 ),
#                 task_id=task_id,
#             )
    
#     if task_id:
#         frappe.publish_realtime(task_id=task_id, message={"message": "Success"})


# def print_quality_inspections_for_job_card(job_card_doc, pdf_writer, default_letter_head):
#     """Print all Quality Inspection documents linked to this Job Card"""
    
#     # Get the operation to check for QI print format
#     operation_doc = None
#     if job_card_doc.operation:
#         try:
#             operation_doc = frappe.get_doc("Operation", job_card_doc.operation)
#         except:
#             pass

#     # Main Quality Inspection
#     if job_card_doc.quality_inspection:
#         print_single_quality_inspection(
#             job_card_doc.quality_inspection, 
#             pdf_writer, 
#             default_letter_head, 
#             operation_doc
#         )

#     # Additional Quality Inspections - removing company specific check
#     additional_qis = [
#         getattr(job_card_doc, 'custom_quality_inspection_3', None),
#         getattr(job_card_doc, 'custom_quality_inspection_4', None),
#         getattr(job_card_doc, 'custom_quality_inspection_5', None),
#         getattr(job_card_doc, 'custom_quality_inspection_6', None)
#     ]
    
#     for qi_name in additional_qis:
#         if qi_name:
#             print_single_quality_inspection(
#                 qi_name, 
#                 pdf_writer, 
#                 default_letter_head, 
#                 operation_doc
#             )

#     # Bio Burden QC
#     if hasattr(job_card_doc, 'custom_bio_burden_qc') and job_card_doc.custom_bio_burden_qc:
#         print_single_quality_inspection(
#             job_card_doc.custom_bio_burden_qc, 
#             pdf_writer, 
#             default_letter_head, 
#             operation_doc
#         )


# def print_single_quality_inspection(qi_name, pdf_writer, default_letter_head, operation_doc=None):
#     """Print a single Quality Inspection document"""
#     try:
#         qi_doc = frappe.get_doc("Quality Inspection", qi_name)
        
#         # Log for debugging
#         frappe.logger("print").info(f"Attempting to print Quality Inspection: {qi_name}")
        
#         # Determine print format priority:
#         # 1. From QI document's custom_print_format
#         # 2. From Operation's qi_print_format (if you add this field)
#         # 3. Use default Quality Inspection print format if none specified
        
#         print_format = None
        
#         if hasattr(qi_doc, 'custom_print_format') and qi_doc.custom_print_format:
#             print_format = qi_doc.custom_print_format
#             frappe.logger("print").info(f"Using QI custom print format: {print_format}")
#         elif operation_doc and hasattr(operation_doc, 'custom_qi_print_format') and operation_doc.custom_qi_print_format:
#             print_format = operation_doc.custom_qi_print_format
#             frappe.logger("print").info(f"Using Operation custom print format: {print_format}")
#         else:
#             # Try to find a default Quality Inspection print format
#             default_formats = frappe.get_list(
#                 "Print Format",
#                 filters={"doc_type": "Quality Inspection", "disabled": 0},
#                 pluck="name",
#                 limit=1
#             )
#             if default_formats:
#                 print_format = default_formats[0]
#                 frappe.logger("print").info(f"Using default QI print format: {print_format}")
        
#         # Always try to print the QI, even without a custom format
#         pdf_writer = frappe.get_print(
#             "Quality Inspection",
#             qi_doc.name,
#             print_format=print_format,
#             as_pdf=True,
#             no_letterhead=0,
#             letterhead=default_letter_head[0].name if default_letter_head else None,
#             output=pdf_writer,
#             pdf_options={"page-size": "A4", "encoding": "UTF-8"},
#         )
#         frappe.logger("print").info(f"Successfully printed Quality Inspection: {qi_name}")
            
#     except Exception as e:
#         frappe.log_error(
#             f"Error printing Quality Inspection {qi_name}: {str(e)}",
#             "Work Order Print QI Error"
#         )


# def print_meril_specific_documents(job_card_doc, pdf_writer):
#     """Print Meril Life Sciences specific documents"""
    
#     # Intimation For Label Printing
#     intimation_list = frappe.get_all(
#         "Intimation For Label Printing", 
#         filters={"job_card_reference": job_card_doc.name, "docstatus": 0}, 
#         pluck="name"
#     )
#     for intimation_name in intimation_list:
#         intimation_doc = frappe.get_doc("Intimation For Label Printing", intimation_name)
#         pdf_writer = frappe.get_print(
#             "Intimation For Label Printing",
#             intimation_doc.name,
#             print_format="INTIMATION FOR LABEL PRINITNG",
#             as_pdf=True,
#             output=pdf_writer,
#             pdf_options={"page-size": "A4", "encoding": "UTF-8"},
#         )

#     # Label Printing
#     label_printing_list = frappe.get_all(
#         "Label Printing", 
#         filters={"job_card_reference": job_card_doc.name, "docstatus": 1}, 
#         pluck="name"
#     )
#     for label_printing_name in label_printing_list:
#         label_printing_doc = frappe.get_doc("Label Printing", label_printing_name)
#         pdf_writer = frappe.get_print(
#             "Label Printing",
#             label_printing_doc.name,
#             print_format="LABEL PRINTING",
#             as_pdf=True,
#             output=pdf_writer,
#             pdf_options={"page-size": "A4", "encoding": "UTF-8"},
#         )

#     # BMR For Packing Material
#     bmr_for_packing_material = frappe.get_all(
#         "BMR For Packing Material", 
#         filters={"job_card_reference": job_card_doc.name, "docstatus": 1}, 
#         pluck="name"
#     )
#     for bmr_name in bmr_for_packing_material:
#         bmr_doc = frappe.get_doc("BMR For Packing Material", bmr_name)
#         pdf_writer = frappe.get_print(
#             "BMR For Packing Material",
#             bmr_doc.name,
#             print_format="BMR - For Packing Material",
#             as_pdf=True,
#             output=pdf_writer,
#             pdf_options={"page-size": "A4", "encoding": "UTF-8"},
#         )




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


    # Print job cards with quality inspections and stock entries
    print_job_cards(
        name, pdf_writer, task_id=task_id, default_letter_head=default_letter_head
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



def print_job_cards(name, pdf_writer, task_id=None, default_letter_head=None):
    job_cards = frappe.get_list(
        "Job Card",
        filters=[
            ["Job Card", "docstatus", "=", 1],
            ["Job Card", "work_order", "=", name],
        ],
        pluck="name",
        order_by="sequence_id asc",
    )
    
    total_docs = len(job_cards)
    count = 1
    
    for job_card in job_cards:
        try:
            frappe.logger("print").info(f"Generating PDF for Job Card {job_card}")
            job_card_doc = frappe.get_doc("Job Card", job_card)


            # Print Job Card - use custom print format if available, otherwise use default
            print_format = job_card_doc.custom_print_format if job_card_doc.custom_print_format else None
            
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


            # Print Quality Inspections for this Job Card
            print_quality_inspections_for_job_card(job_card_doc, pdf_writer, default_letter_head)

            # Print Stock Entries for this Job Card
            print_stock_entries_for_job_card(job_card_doc, pdf_writer, default_letter_head)


        except Exception as e:
            if task_id:
                frappe.publish_realtime(task_id=task_id, message={"message": "Failed"})
            frappe.throw(e.__str__(), exc=frappe.PrintFormatError)
        
        count += 1
        if task_id:
            frappe.publish_progress(
                percent=(count / total_docs) * 100,
                title="Generating PDF",
                description=_(
                    "Generating PDF for Job Card {0} of {1}".format(count, total_docs)
                ),
                task_id=task_id,
            )
    
    if task_id:
        frappe.publish_realtime(task_id=task_id, message={"message": "Success"})



def print_quality_inspections_for_job_card(job_card_doc, pdf_writer, default_letter_head):
    """Print all Quality Inspection documents linked to this Job Card"""
    
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


    # Additional Quality Inspections - removing company specific check
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
        # 2. From Operation's qi_print_format (if you add this field)
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
        
        # Always try to print the QI, even without a custom format
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



def print_stock_entries_for_job_card(job_card_doc, pdf_writer, default_letter_head):
    """Print all Stock Entry documents of type 'Material Transfer for Manufacture' linked to this Job Card"""
    
    try:
        # Get Stock Entries of type 'Material Transfer for Manufacture' linked to this Job Card
        # print("")
        stock_entries = frappe.get_all(
            "Stock Entry",
            filters={
                "stock_entry_type": "Material Transfer for Manufacture",
                "work_order": job_card_doc.work_order,
                "docstatus": 1  # Only submitted stock entries
            },
            fields=["name"],
            order_by="posting_date, posting_time"
        )
        print("stockentries===============",stock_entries)
        frappe.logger("print").info(f"Found {len(stock_entries)} Material Transfer for Manufacture Stock Entries for Job Card {job_card_doc.name}")
        
        for stock_entry in stock_entries:
            print_single_stock_entry(
                stock_entry.name,
                pdf_writer,
                default_letter_head,
                job_card_doc
            )
            
    except Exception as e:
        frappe.log_error(
            f"Error getting Stock Entries for Job Card {job_card_doc.name}: {str(e)}",
            "Work Order Print Stock Entry Error"
        )



def print_single_stock_entry(stock_entry_name, pdf_writer, default_letter_head, job_card_doc=None):
    """Print a single Stock Entry document"""
    try:
        stock_entry_doc = frappe.get_doc("Stock Entry", stock_entry_name)
        
        # Log for debugging
        frappe.logger("print").info(f"Attempting to print Stock Entry: {stock_entry_name}")
        
        # Determine print format priority:
        # 1. From Stock Entry document's custom_print_format (if exists)
        # 2. From Job Card's operation's custom_stock_entry_print_format (if you add this field)
        # 3. Use default Stock Entry print format if none specified
        
        print_format = None
        
        if hasattr(stock_entry_doc, 'custom_print_format') and stock_entry_doc.custom_print_format:
            print_format = stock_entry_doc.custom_print_format
            frappe.logger("print").info(f"Using Stock Entry custom print format: {print_format}")
        elif job_card_doc and job_card_doc.operation:
            # Try to get print format from operation
            try:
                operation_doc = frappe.get_doc("Operation", job_card_doc.operation)
                if hasattr(operation_doc, 'custom_stock_entry_print_format') and operation_doc.custom_stock_entry_print_format:
                    print_format = operation_doc.custom_stock_entry_print_format
                    frappe.logger("print").info(f"Using Operation Stock Entry print format: {print_format}")
            except:
                pass
        
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



def print_meril_specific_documents(job_card_doc, pdf_writer):
    """Print Meril Life Sciences specific documents"""
    
    # Intimation For Label Printing
    intimation_list = frappe.get_all(
        "Intimation For Label Printing", 
        filters={"job_card_reference": job_card_doc.name, "docstatus": 0}, 
        pluck="name"
    )
    for intimation_name in intimation_list:
        intimation_doc = frappe.get_doc("Intimation For Label Printing", intimation_name)
        pdf_writer = frappe.get_print(
            "Intimation For Label Printing",
            intimation_doc.name,
            print_format="INTIMATION FOR LABEL PRINITNG",
            as_pdf=True,
            output=pdf_writer,
            pdf_options={"page-size": "A4", "encoding": "UTF-8"},
        )


    # Label Printing
    label_printing_list = frappe.get_all(
        "Label Printing", 
        filters={"job_card_reference": job_card_doc.name, "docstatus": 1}, 
        pluck="name"
    )
    for label_printing_name in label_printing_list:
        label_printing_doc = frappe.get_doc("Label Printing", label_printing_name)
        pdf_writer = frappe.get_print(
            "Label Printing",
            label_printing_doc.name,
            print_format="LABEL PRINTING",
            as_pdf=True,
            output=pdf_writer,
            pdf_options={"page-size": "A4", "encoding": "UTF-8"},
        )


    # BMR For Packing Material
    bmr_for_packing_material = frappe.get_all(
        "BMR For Packing Material", 
        filters={"job_card_reference": job_card_doc.name, "docstatus": 1}, 
        pluck="name"
    )
    for bmr_name in bmr_for_packing_material:
        bmr_doc = frappe.get_doc("BMR For Packing Material", bmr_name)
        pdf_writer = frappe.get_print(
            "BMR For Packing Material",
            bmr_doc.name,
            print_format="BMR - For Packing Material",
            as_pdf=True,
            output=pdf_writer,
            pdf_options={"page-size": "A4", "encoding": "UTF-8"},
        )