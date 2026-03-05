// Copyright (c) 2026, Siddhant Hybrowlabs and contributors
// For license information, please see license.txt

frappe.ui.form.on("Supplier Invoice", {
	refresh: function(frm) {
        if (frm.doc.upload_file && !frm.is_new()) {
            frm.add_custom_button(__('Scan File'), function() {
                if (frm.is_dirty()) {
                    frappe.msgprint({
                        title: __('Save Required'),
                        message: __('Please save the document before scanning the file.'),
                        indicator: 'orange'
                    });
                    return;
                }

                // Show progress dialog with animated progress bar
                let progress_value = 0;
                let progress_dialog = new frappe.ui.Dialog({
                    title: __('Processing OCR'),
                    indicator: 'blue',
                    fields: [
                        {
                            fieldtype: 'HTML',
                            fieldname: 'progress_html',
                            options: `<div class="ocr-progress">
                                <p class="progress-status">Sending file to OCR server...</p>
                                <div class="progress" style="height: 20px;">
                                    <div class="progress-bar progress-bar-striped progress-bar-animated"
                                         role="progressbar"
                                         style="width: 0%; transition: width 0.3s ease;">
                                    </div>
                                </div>
                                <p class="progress-percent text-muted mt-2">0%</p>
                            </div>`
                        }
                    ]
                });
                progress_dialog.show();
                progress_dialog.$wrapper.find('.modal-footer').hide();

                // Animate progress bar
                let progress_interval = setInterval(function() {
                    if (progress_value < 90) {
                        progress_value += Math.random() * 10;
                        if (progress_value > 90) progress_value = 90;
                        progress_dialog.$wrapper.find('.progress-bar').css('width', progress_value + '%');
                        progress_dialog.$wrapper.find('.progress-percent').text(Math.round(progress_value) + '%');
                    }
                }, 500);

                // Update status messages
                let status_messages = [
                    'Sending file to OCR server...',
                    'Analyzing document...',
                    'Extracting text...',
                    'Processing data...',
                    'Almost done...'
                ];
                let status_index = 0;
                let status_interval = setInterval(function() {
                    status_index++;
                    if (status_index < status_messages.length) {
                        progress_dialog.$wrapper.find('.progress-status').text(status_messages[status_index]);
                    }
                }, 3000);

                frappe.call({
                    method: 'merai_newage.merai_newage.utils.api.supplier_invoice_api.send_file_to_external_api',
                    args: { docname: frm.doc.name },
                    callback: function(r) {
                        clearInterval(progress_interval);
                        clearInterval(status_interval);

                        if (r.message && r.message.status === 'error') {
                            progress_dialog.hide();
                            frappe.msgprint({
                                title: __('OCR Processing Error'),
                                message: r.message.message,
                                indicator: 'red'
                            });
                            return;
                        }

                        // Complete the progress bar
                        progress_dialog.$wrapper.find('.progress-bar')
                            .css('width', '100%')
                            .removeClass('progress-bar-animated progress-bar-striped')
                            .addClass('bg-success');
                        progress_dialog.$wrapper.find('.progress-percent').text('100%');
                        progress_dialog.$wrapper.find('.progress-status').text('OCR completed successfully!');

                        setTimeout(function() {
                            progress_dialog.hide();
                            frm.reload_doc();
                            frappe.msgprint({
                                title: __('OCR Processing Complete'),
                                message: __('OCR data has been extracted successfully.'),
                                indicator: 'green'
                            });
                        }, 1000);
                    },
                    error: function() {
                        clearInterval(progress_interval);
                        clearInterval(status_interval);
                        progress_dialog.hide();
                        frappe.msgprint({
                            title: __('OCR Processing Error'),
                            message: __('Failed to initiate OCR. Please try again or contact support.'),
                            indicator: 'red'
                        });
                    }
                });
            }).addClass('btn-primary');
        }

        // Button to send data to the api for decode the data in encrypted text
        if (frm.doc.workflow_state === "Open" && !frm.is_new()) {
        frm.add_custom_button("Decode", function() {
            if (!frm.doc.encrypted_data) {
                frappe.msgprint("Please add Encrypted Data first.");
                return;
            }

            frappe.call({
                method: "purchase_booking.purchase_booking_request.doctype.purchase_booking_request.purchase_booking_request.decode_irn",
                args: {
                    encrypted_data: frm.doc.encrypted_data
                },
                freeze: true,
                freeze_message: "Decoding, please wait...",
                callback: function(r) {
                    if (r.message) {
                        // Show nicely formatted response
                        frappe.msgprint({
                            title: "Decoder Response",
                            indicator: "green",
                            message: `<pre>${JSON.stringify(r.message, null, 2)}</pre>`
                        });
                    }
                }
            });
        });
    }

        // Button to assign PO User and Service Entry User in Pending For PO state
        if (frm.doc.workflow_state === "Pending For PO" && !frm.is_new()) {
            frm.add_custom_button(__('Assign PO User'), function() {
                if (frm.is_dirty()) {
                    frappe.msgprint({
                        title: __('Save Required'),
                        message: __('Please save the document before assigning users.'),
                        indicator: 'orange'
                    });
                    return;
                }

                if (!frm.doc.po_user) {
                    frappe.msgprint({
                        title: __('Users Required'),
                        message: __('Please select at least one of PO User'),
                        indicator: 'orange'
                    });
                    return;
                }

                frappe.confirm(
                    __('Are you sure you want to assign the PO User?'),
                    function() {
                        frappe.call({
                            method: "purchase_booking.purchase_booking_request.doctype.purchase_booking_request.purchase_booking_request.assign_po_and_service_entry_users",
                            args: {
                                docname: frm.doc.name
                            },
                            callback: function(r) {
                                if (!r.exc) {
                                    frm.reload_doc();
                                }
                            }
                        });
                    }
                );
            }).addClass('btn-primary');
        }

        // this is query regarding code for button and raise query
           if (frm.doc.workflow_state === "Proceed For Booking" || frm.doc.workflow_state === "Booked") {
                if (frappe.user.has_role("Booking User") || frappe.user.has_role("Booking Approver")) {   // 🔹 Role check here
                    frm.add_custom_button('Raise Query', function() {
                        frappe.prompt([
                            {
                                label: 'Query',
                                fieldname: 'query_text',
                                fieldtype: 'Small Text',
                                reqd: 1
                            },
                            {
                                label: 'Related Field',
                                fieldname: 'related_field',
                                fieldtype: 'Select',
                                options: [
                                    "Document Number",
                                    "Vendor ID",
                                    "Vendor Name",
                                    "GSTIN/UIN",
                                    "GST Category",
                                    "Invoice No",
                                    "Invoice Date",
                                    "Company Code",
                                    "Posting Date",
                                    "Period",
                                    "Amount",
                                    "Tax Amount",
                                    "Remark",
                                    "Email",
                                    "Mobile Number",
                                    "PAN",
                                    "Upload File"
                                ],
                                reqd: 1
                            }
                        ],
                        function(values) {
                            frappe.call({ 
                                method: "purchase_booking.purchase_booking_request.doctype.purchase_booking_request.purchase_booking_request.raise_query",
                                args: {
                                    docname: frm.doc.name,
                                    query_text: values.query_text,
                                    related_field: values.related_field
                                },
                                callback: function() {
                                    frm.reload_doc();
                                }
                            });
                        }, 'Raise Query');
                    });
                }
            }

            if (frm.doc.workflow_state === "Proceed For Booking" || frm.doc.workflow_state === "Open") {
                if (frappe.user.has_role("Scanning") || frappe.user.has_role("Booking User")) { 
                    frm.add_custom_button(__('Resolve Query'), function() {
                        let selected = frm.fields_dict["purchase_booking_query"].grid.get_selected();

                        if (!selected.length) {
                            frappe.msgprint("Please select query row first");
                            return;
                        }

                        // get row details
                        let row = frm.fields_dict["purchase_booking_query"].grid.grid_rows_by_docname[selected[0]].doc;

                        // validation: only allow if status is Open
                        if (row.status !== "Open") {
                            frappe.msgprint("Please select an Open query only");
                            return;
                        }

                        // Debug: check if row.name exists
                        if (!row.name) {
                            frappe.msgprint("Please save the document first before resolving the query");
                            return;
                        }

                        console.log("Resolving query with name:", row.name);

                        frappe.call({
                            method: "purchase_booking.purchase_booking_request.doctype.purchase_booking_request.purchase_booking_request.resolve_query",
                            args: {
                                query_name: row.name   // pass row.name, not idx
                            },
                            callback: function(r) {
                                if (!r.exc) {
                                    frappe.msgprint("Query Resolved Successfully");
                                    frm.reload_doc();
                                }
                            }
                        });
                    });
                }
            }
    },
    onload: function(frm) {
        // Show preview if file exists
        if (frm.doc.upload_file) show_preview(frm);

    },

    upload_file: function(frm) {
        if (frm.doc.upload_file) show_preview(frm);
    },
});


function show_preview(frm) {
    const file_url = frm.doc.upload_file;

    if (!file_url) {
        frm.fields_dict.preview_html.$wrapper.html('');
        frm.fields_dict.custom_file_preview.$wrapper.html('');
        return;
    }

    const lower_url = file_url.toLowerCase();
    let htmlContent;

    if (lower_url.endsWith('.pdf')) {
        htmlContent = `<iframe src="${file_url}" width="210%" height="700px" style="border:none;"></iframe>`;
    } else if (/\.(jpg|jpeg|png|gif|webp)$/.test(lower_url)) {
        htmlContent = `<img src="${file_url}" width="100%" style="max-height:600px;">`;
    } else {
        htmlContent = `<p>Preview not available for this file type.</p>`;
    }

    // Set HTML for both fields
    frm.fields_dict.preview_html.$wrapper.html(htmlContent);
    frm.fields_dict.custom_file_preview.$wrapper.html(htmlContent);
}