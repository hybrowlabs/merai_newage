// Copyright (c) 2025, Siddhant Hybrowlabs and contributors
// For license information, please see license.txt

frappe.ui.form.on("Batch Release Certificate", {
	refresh(frm) {
        add_verify_buttons_to_grid(frm, 'batch_release_certificate_details', 'Batch Release Certificate Details');
        if (frm.doc.docstatus === 1) {

            frm.add_custom_button(
                __("Dispatch"),
                function () {
                    frappe.new_doc("Dispatch", {
                        item_code: frm.doc.product_name,   
                        batch_number: frm.doc.batch,
                        batch_no:frm.doc.batch_number,    
                        refrence_brc: frm.doc.name        
                    });

                },
                __("Create")
            );
        }

	},
   batch(frm) {

    if (!frm.doc.batch) return;

    frappe.db.get_value(
        "Batch",
        { custom_batch_number: frm.doc.batch },
        "name"
    ).then(r => {

        if (r && r.message) {
            frm.set_value("batch_number", r.message.name);
        }

    });
}
,
   work_order: function(frm) {
    if (!frm.doc.work_order) return;

    frappe.call({
        method: "merai_newage.merai_newage.doctype.batch_release_certificate.batch_release_certificate.fetch_brc_details",
        args: {
            work_order: frm.doc.work_order
        },
        callback: function(r) {

            if (!r.message) return;

          
            frm.clear_table('batch_release_certificate_item_details');

            if (r.message.child_items && r.message.child_items.length) {
                r.message.child_items.forEach(function(item) {
                    let row = frm.add_child(
                        'batch_release_certificate_item_details'
                    );
                    row.part_no = item.part_no;
                    row.std_qty = item.std_qty;
                    row.description = item.description;
                });
            }

            frm.refresh_field('batch_release_certificate_item_details');


            frm.clear_table('batch_release_certificate_details');

            if (r.message.verification_items && r.message.verification_items.length) {
                r.message.verification_items.forEach(function(item) {
                    let row = frm.add_child(
                        'batch_release_certificate_details'
                    );
                    row.test_description = item.test_description;
                });
            }

            frm.refresh_field('batch_release_certificate_details');

            frappe.show_alert({
                message: __('Data fetched successfully'),
                indicator: 'green'
            });
        }
    });



}
});

function add_verify_buttons_to_grid(frm, fieldname, doctype) {
    let grid = frm.fields_dict[fieldname].grid;
    
    // Override the render method to add buttons
    grid.wrapper.find('.grid-body .rows').on('click', '.grid-row', function() {
        setTimeout(() => {
            add_verify_button_to_row(frm, fieldname, doctype);
        }, 100);
    });
    
    // Add buttons on initial load
    setTimeout(() => {
        add_verify_button_to_row(frm, fieldname, doctype);
    }, 500);
}

function add_verify_button_to_row(frm, fieldname, doctype) {
    let grid = frm.fields_dict[fieldname].grid;
    
    grid.grid_rows.forEach(row => {
        if (row.doc && !row.wrapper.find('.verify-btn-custom').length) {
            let verify_cell = row.wrapper.find('[data-fieldname="verify"]');
            
            if (verify_cell.length) {
                verify_cell.empty();
                
                let btn = $(`<button class="btn btn-success btn-xs verify-btn-custom" 
                    style="background-color: #28a745; color: white; border-color: #28a745; padding: 3px 12px;">
                    Verify
                </button>`);
                
                btn.on('click', function(e) {
                    e.stopPropagation();
                    handle_verify_click(frm, row.doc.doctype, row.doc.name, fieldname);
                });
                
                verify_cell.append(btn);
            }
        }
    });
}

function handle_verify_click(frm, cdt, cdn, fieldname) {
    let row = locals[cdt][cdn];
    
    let field_to_check = fieldname === 'batch_release_certificate_details' ? 'test_description' : 'performance_check';
    
    if (!row[field_to_check]) {
        frappe.msgprint(`Please select ${fieldname === 'batch_release_certificate_details' ? 'BRC Item' : 'Performance Check'} first.`);
        return;
    }

    frappe.call({
        method: "merai_newage.merai_newage.doctype.installation.installation.get_safety_check_items",
        args: {
            safety_steps: row[field_to_check]
        },
        callback(r) {
            if (!r.message) {
                frappe.msgprint("No Safety Checks found.");
                return;
            }
            show_safety_popup(r.message, frm, row, cdt, cdn, fieldname);
        }
    });
}


function show_safety_popup(items, frm, row, cdt, cdn, fieldname) {
    let question_html = "<ul style='margin-top: 10px;'>";
    items.forEach((item, idx) => {
        question_html += `<li style='margin-bottom: 5px;'>${item.check_name}</li>`;
    });
    question_html += "</ul>";

    let dialog = new frappe.ui.Dialog({
        title: "Safety Check Verification",
        fields: [
            {
                fieldname: "questions",
                fieldtype: "HTML",
                options: `<div class="form-group">
                    <label style='font-weight: bold;'>Please verify the following steps:</label>
                    ${question_html}
                </div>`
            },
            {
                fieldname: "verification",
                label: "Verification Result",
                fieldtype: "Select",
                options: "Yes\nNo",
                reqd: 1
            },
            {
                fieldname: "remarks",
                label: "Remarks",
                fieldtype: "Small Text"
            }
        ],
        primary_action_label: "Save",
        primary_action(values) {
            row.remarks = values.remarks;
            row.result = values.verification || "";
            
            frm.refresh_field(fieldname);
            frm.dirty();
            
            // Re-add buttons after refresh
            setTimeout(() => {
                add_verify_button_to_row(frm, fieldname, cdt.replace(' ', '_').toLowerCase());
            }, 300);
            
            frm.save_or_update();
            dialog.hide();
        }
    });

    dialog.show();
}
