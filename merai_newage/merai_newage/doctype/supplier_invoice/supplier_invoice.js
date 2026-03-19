frappe.ui.form.on("Supplier Invoice", {
    refresh: function(frm) {

       

        // Scan File Button
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
                        options: `
                        <div class="ocr-progress">
                            <p class="progress-status">Sending file to OCR server...</p>
                            <div class="progress" style="height: 20px;">
                                <div class="progress-bar progress-bar-striped progress-bar-animated"
                                     role="progressbar"
                                     style="width: 0%;">
                                </div>
                            </div>
                            <p class="progress-percent text-muted mt-2">0%</p>
                        </div>`
                    }]
                });

                progress_dialog.show();
                progress_dialog.$wrapper.find('.modal-footer').hide();

                let progress_interval = setInterval(() => {
                    if (progress_value < 90) {
                        progress_value += Math.random() * 10;
                        if (progress_value > 90) progress_value = 90;

                        progress_dialog.$wrapper.find('.progress-bar')
                            .css('width', progress_value + '%');

                        progress_dialog.$wrapper.find('.progress-percent')
                            .text(Math.round(progress_value) + '%');
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

                let status_interval = setInterval(() => {
                    status_index++;
                    if (status_index < status_messages.length) {
                        progress_dialog.$wrapper.find('.progress-status')
                            .text(status_messages[status_index]);
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
                        progress_dialog.$wrapper.find('.progress-status')
                            .text('OCR completed successfully!');

                        setTimeout(() => {
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

        // Decode Button
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

   if (frm.doc.docstatus === 1) {
    frm.add_custom_button('Purchase Invoice', function () {
        frappe.call({
            method: 'merai_newage.merai_newage.api.create_purchase_invoice',
            args: { source_name: frm.doc.name },
            callback: function (r) {
                if (r.message) {
                    let doc = r.message;

                    // put the doc into frappe locals so the form can read it
                    frappe.model.sync(doc);

                    // open the form — it will read from locals, not DB
                    frappe.set_route('Form', 'Purchase Invoice', doc.name);
                }
            }
        });
    }, 'Create');
}
        /// Gate Entry (only for PO)
        

//             if (frm.doc.invoice_type === "PO") {
//             frm.add_custom_button('Create Gate Entry', function () {

//             frappe.call({
//             method: 'cn_exim.cn_exim.doctype.gate_entry.gate_entry.get_supplier_document_details_from_po',
//             args: { doc_name: frm.doc.name },

//             callback: function (r) {
//                 if (r.message) {
//                     var data = r.message;

//                     frappe.new_doc('Gate Entry', {
//                         po_number: frm.doc.name,
//                         bill_number: frm.doc.invoice_no,             
//                         bill_date: frm.doc.invoice_date,
//                         supplier: frm.doc.vendor_id,             
//                         supplier_name: frm.doc.vendor_name, 
//                     });

//                 } else {
//                     frappe.msgprint("No Supplier Invoice found linked to this PO.");
//                 }
//             }
//         });

//     }, 'Create');
// }
    },

    onload: function(frm) {
        if (frm.doc.invoice_type === "PO" && frm.doc.po_number) {
            frm.trigger("po_number");
        }

        if (frm.doc.upload_file) {
            show_preview(frm);
        }
    },

    upload_file: function(frm) {
        if (frm.doc.upload_file) {
            show_preview(frm);
        }
    },

    po_number: function(frm) {

        if (frm.doc.invoice_type === "PO" && frm.doc.po_number) {

            frappe.db.get_doc("Purchase Order", frm.doc.po_number)
                .then(po => {
                      if (frm.doc.docstatus === 1) return; 

                    // Header
                    frm.set_value("cost_center", po.cost_center);
                    frm.set_value("plant", po.plant);
                    if (frm.doc.po_items && frm.doc.po_items.length > 0) {
                        return;
                    }

                    // Items
                    po.items.forEach(item => {
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

frappe.ui.form.on('Non PO Items', {
    item: function(frm, cdt, cdn) {
        var row = locals[cdt][cdn];
        if (row.item) {
            frappe.db.get_value('Item', row.item, 'stock_uom', function(value) {
                if (value && value.stock_uom) {
                    frappe.model.set_value(cdt, cdn, 'uom', value.stock_uom);
                }
            });
        }
    }
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