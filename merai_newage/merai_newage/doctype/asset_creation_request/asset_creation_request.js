frappe.ui.form.on("Asset Creation Request", {


    qty(frm) {
    update_asset_code_rows(frm);
},

composite_item(frm) {
    update_asset_code_rows(frm);
},

generate_asset_codes(frm) {
    if (frm.is_dirty()) {
        frm.save().then(() => {
            frm.trigger("generate_asset_codes");
        });
        return;
    }

    frappe.call({
        method: "merai_newage.merai_newage.doctype.asset_creation_request.asset_creation_request.create_assets_from_request",
        args: {
            doc: frm.doc
        },
        freeze: true,
        callback: function (r) {
            if (!r.message || !r.message.length) return;

            frm.clear_table("asset_code_details");

            r.message.forEach(row => {
                let child = frm.add_child("asset_code_details");
                child.asset_code = row.asset_code;
            });

            frm.refresh_field("asset_code_details");
        }
    });
}

,
    
    refresh(frm){

         if (frm.doc.enable_cwip_accounting && 
            frm.doc.custom_cwip_purchase_receipts && 
            frm.doc.custom_cwip_purchase_receipts.length > 0 &&
            frm.doc.custom_cwip_asset) {
            
            frm.add_custom_button(__('Convert to Fixed Asset'), function() {
                let total_prs = frm.doc.custom_cwip_purchase_receipts.length;
                let total_amount = frm.doc.custom_total_cwip_amount || 0;
                let main_items = frm.doc.custom_cwip_purchase_receipts.filter(r => !r.is_service_item).length;
                let service_items = frm.doc.custom_cwip_purchase_receipts.filter(r => r.is_service_item).length;
                
                frappe.confirm(
                    __('Update CWIP Asset with accumulated costs?<br><br>' +
                       '<b>Total PRs:</b> {0}<br>' +
                       '<b>Main Asset Items:</b> {1}<br>' +
                       '<b>Service Items:</b> {2}<br>' +
                       '<b>Total Amount:</b> ₹{3}<br><br>' +
                       'This will update the asset amount.',
                       [total_prs, main_items, service_items, format_currency(total_amount)]
                    ),
                    function() {
                        frappe.call({
                            method: 'merai_newage.merai_newage.doctype.asset_creation_request.asset_creation_request.convert_cwip_to_fixed_asset',
                            args: {
                                acr_name: frm.doc.name
                            },
                            callback: function(r) {
                                if (r.message) {
                                    frappe.msgprint({
                                        title: __('Success'),
                                        indicator: 'green',
                                        message: __(r.message)
                                    });
                                    frm.reload_doc();
                                }
                            }
                        });
                    }
                );
            }, __('CWIP Actions'));
            
            // Add button to view CWIP breakdown
            frm.add_custom_button(__('View Cost Breakdown'), function() {
                show_cwip_breakdown(frm);
            }, __('CWIP Actions'));
        }
    
        if (!frm.doc.employee) {
            let user = frappe.session.user;
            console.log("user=====",user)
            frappe.db.get_list("Employee", {
                fields: ["name"],
                filters: {
                    user_id: user
                },
                limit: 1
            }).then(res => {
                if (res.length > 0) {
                    frm.set_value("employee", res[0].name);
                }
            });
        }
        frm.set_query("cost_centre", () => {
            return {
                filters: {
                    company: frm.doc.entinty,
                }
            };
        });
        frm.set_query("item", () => {
            return {
                filters: {
                    is_fixed_asset: 1,
                    is_stock_item:0
                }
            };
        });
    }
});


function update_asset_code_rows(frm) {
    let qty = cint(frm.doc.qty || 0);
    let is_composite = frm.doc.composite_item;

    frm.clear_table("asset_code_details");

    if (qty <= 0) {
        frm.refresh_field("asset_code_details");
        return;
    }

    let row_count = is_composite ? 1 : qty;

    for (let i = 0; i < row_count; i++) {
        frm.add_child("asset_code_details", {
            asset_code: ""
        });
    }

    frm.refresh_field("asset_code_details");
}


