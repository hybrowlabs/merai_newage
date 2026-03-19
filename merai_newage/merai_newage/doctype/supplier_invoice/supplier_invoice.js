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

                let progress_value = 0;
                let progress_dialog = new frappe.ui.Dialog({
                    title: __('Processing OCR'),
                    indicator: 'blue',
                    fields: [{
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
                    }]
                });

                progress_dialog.show();
                progress_dialog.$wrapper.find('.modal-footer').hide();

                let progress_interval = setInterval(function() {
                    if (progress_value < 90) {
                        progress_value += Math.random() * 10;
                        if (progress_value > 90) progress_value = 90;
                        progress_dialog.$wrapper.find('.progress-bar').css('width', progress_value + '%');
                        progress_dialog.$wrapper.find('.progress-percent').text(Math.round(progress_value) + '%');
                    }
                }, 500);

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

        // Decode button
        if (frm.doc.workflow_state === "Open" && !frm.is_new()) {
            frm.add_custom_button("Decode", function() {
                if (!frm.doc.encrypted_data) {
                    frappe.msgprint("Please add Encrypted Data first.");
                    return;
                }

                frappe.call({
                    method: "purchase_booking.purchase_booking_request.doctype.purchase_booking_request.purchase_booking_request.decode_irn",
                    args: { encrypted_data: frm.doc.encrypted_data },
                    freeze: true,
                    freeze_message: "Decoding, please wait...",
                    callback: function(r) {
                        if (r.message) {
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

        // Purchase Invoice button
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button('Create Purchase Invoice', function() {
                frappe.call({
                    method: 'merai_newage.merai_newage.api.create_purchase_invoice',
                    args: { source_name: frm.doc.name },
                    callback: function(r) {
                        if (r.message) {
                            frappe.msgprint("Purchase Invoice Created: " + r.message);
                            frappe.set_route('Form', 'Purchase Invoice', r.message);
                        }
                    }
                });
            }, 'Create');

            // Gate Entry for PO only
            // if (frm.doc.invoice_type === "PO") {
            //     frm.add_custom_button('Create Gate Entry', function() {
            //         frappe.call({
            //             method: 'merai_newage.merai_newage.api.create_gate_entry',
            //             args: { source_name: frm.doc.name },
            //             callback: function(r) {
            //                 if (r.message) {
            //                     frappe.msgprint("Gate Entry Created: " + r.message);
            //                     frappe.set_route('Form', 'Gate Entry', r.message);
            //                 }
            //             }
            //         });
            //     }, 'Create');
            // }
        }
    },

    onload: function(frm) {
        if (frm.doc.invoice_type === "PO" && frm.doc.po_number) {
        frm.trigger("po_number");
     }


        if (frm.doc.upload_file) show_preview(frm);
    },

    upload_file: function(frm) {
        if (frm.doc.upload_file) show_preview(frm);
    },

    po_number: function(frm) {

    if (frm.doc.invoice_type === "PO" && frm.doc.po_number) {

        //  FETCH HEADER DATA (ADD THIS)
        frappe.db.get_doc("Purchase Order", frm.doc.po_number)
            .then(po => {

                 // HEADER VALUES (NOW WILL WORK)
                    frm.set_value("cost_center", po.cost_center);
                    frm.set_value("plant", po.plant);

                // FETCH ITEMS (MOVE INSIDE)
                //frm.clear_table("po_items");
                if (frm.doc.po_items && frm.doc.po_items.length > 0) {
                    return;
                }
                

                po.items.forEach(function(item) {

                    let row = frm.add_child("po_items");

                    row.item = item.item_code;
                    row.required_qty = item.qty;
                    row.uom = item.uom;
                    row.rate = item.rate;
                    row.amount = item.amount;

                    

                });

                frm.refresh_field("po_items");
            });
    }
}
    

});