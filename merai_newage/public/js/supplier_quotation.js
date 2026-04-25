frappe.ui.form.on("Supplier Quotation", {

    // This trigger will run when the form is refreshed, and it will add a custom button to view the revision history of the RFQ if the document is submitted and is the latest revision.
    refresh: function (frm) {

        // toggle_previous_rate(frm);
        set_shipment_details_from_rfq(frm);

        // base rate mandotory only for non-logistics items
        toggle_base_rate_reqd(frm);
        //supplier REVISION BUTTON
        if (frm.doc.docstatus === 1 && !frm.doc.custom_is_revision) {

            if (!frm.custom_revision_added) {

                frm.custom_revision_added = true;

                frm.add_custom_button(
                    'Revise Supplier Quotation',
                    function () {

                        frappe.call({
                            method: "merai_newage.merai_newage.api.create_revision_supplier_quotation",
                            args: {
                                docname: frm.doc.name
                            },
                            callback: function (r) {
                                if (r.message) {
                                    frappe.set_route("Form", "Supplier Quotation", r.message);
                                }
                            }
                        });

                    },
                    'Create'
                );

            }
        }
        
        // Check if the document is submitted and is the latest revision
        if (!frm.doc.request_for_quotation) return;
        // Fetch the quotation deadline from the linked RFQ and disable save if the deadline has passed
        frappe.db.get_value(
            'Request for Quotation',
            frm.doc.request_for_quotation,
            'custom_quotation_deadline1'
        ).then(r => {
            let deadline = r.message.custom_quotation_deadline1;
            let now = frappe.datetime.now_datetime();

            if (deadline && deadline <= now) {
                frm.disable_save();

                frappe.show_alert({
                    message: "RFQ deadline has passed. You cannot submit quotation.",
                    indicator: 'red'
                });
            }
        });

        // Calculate freight and set requisitioner from reference on refresh
        calculate_freight(frm);
        set_requisitioner_from_reference(frm);

        if (!frm._attachment_sync_bound && frm.attachments) {
			frm._attachment_sync_bound = true;

			frm.attachments.on("change", function () {
				if (merai?.sync_workflow_attachment_table) {
					merai.sync_workflow_attachment_table(frm);
				}
			});
		}

    },
    custom_purchase_order: function(frm) {

        if (!frm.doc.custom_purchase_order) return;

        frappe.call({
            method: "merai_newage.overrides.supplier_quotation.get_po_details",
            args: {
                po_name: frm.doc.custom_purchase_order
            },
            callback: function(r) {

                if (!r.message) return;

                // MAIN MAPPING
                if (r.message.cost_center) {
                    frm.set_value("cost_center", r.message.cost_center);
                }

                if (r.message.plant) {
                    frm.set_value("plant", r.message.plant);
                }
            }
        });
    },
    
    custom_pickup_request: function(frm) {

        if (!frm.doc.custom_pickup_request) return;

            frappe.call({
                method: "merai_newage.overrides.supplier_quotation.get_po_numbers",
                args: {
                    pr_name: frm.doc.custom_pickup_request
                },
                callback: function(r) {

                    if (!r.message || !r.message.length) return;

                    let po_number = r.message[0].po_number;

                    // prevent overwrite spam
                    if (frm.doc.custom_purchase_order !== po_number) {
                        frm.set_value("custom_purchase_order", po_number);
                    }
                }
            });
        },

    onload: function(frm) {
        if (frm.doc.custom_pickup_request && !frm.doc.custom_purchase_order) {
            frm.trigger("custom_pickup_request");
        }
    },

    request_for_quotation: function(frm) {
        set_shipment_details_from_rfq(frm);
    },

    custom_rate_kg: function(frm) {
        calculate_freight(frm);
    },

    custom_type: function(frm) {
        toggle_base_rate_reqd(frm);
    },
    
    custom_fsc: function(frm) {
        calculate_freight(frm);
    },

    custom_sc: function(frm) {
        calculate_freight(frm);
    },

    custom_xray: function(frm) {
        calculate_freight(frm);
    },

    custom_cw: function(frm) {
        calculate_freight(frm);
    },

    custom_ex_words: function(frm) {
        calculate_freight(frm);
    },

    // This trigger will recalculate the total freight in INR whenever the XR/ XE component changes

    custom_total_freight:function(frm) {
        calculate_sum_freight_and_xr(frm);
    },
    custom_xrxe_com: function(frm) {
        calculate_sum_freight_and_xr(frm);
    },

    // The following triggers will recalculate the total landing price in INR whenever any of the components change
    custom_total_freight_inr: function(frm) {
        sum_landing_prices(frm);
    },
    custom_dc_inr: function(frm) {
        sum_landing_prices(frm);
    },
    custom_shipping_line_charges: function(frm) {
        sum_landing_prices(frm);
    },
    custom_cfs_charges: function(frm) {
        sum_landing_prices(frm);    
    },
    
    // The following triggers will fetch the exchange rate and recalculate the freight in INR whenever the from or to currency changes
    custom_from_currency: function(frm) {
        console.log("From currency changed");
        fetch_exchange_rate(frm);
    },

    custom_to_currency: function(frm) {
        console.log("To currency changed");
        fetch_exchange_rate(frm);
    },

    after_save: function (frm) {
        if (merai?.sync_workflow_attachment_table) {
            merai.sync_workflow_attachment_table(frm);
        }
    },

    on_submit: function (frm) {
        if (merai?.sync_workflow_attachment_table) {
            merai.sync_workflow_attachment_table(frm);
        }
    }

});

// Function to calculate total freight based on the provided components
function calculate_freight(frm) {

    let rate = flt(frm.doc.custom_rate_kg);
    let fsc = flt(frm.doc.custom_fsc);
    let sc = flt(frm.doc.custom_sc);
    let xray = flt(frm.doc.custom_xray);
    let weight = flt(frm.doc.custom_cw);
    let exwords = flt(frm.doc.custom_ex_words);

    let total_rate = rate + fsc + sc + xray;

    let freight_fcr = (total_rate * weight) + exwords;

    frm.set_value("custom_total_freight", freight_fcr);
}

// Function to calculate total freight in INR based on the total freight and XR/ XE component
function calculate_sum_freight_and_xr(frm){
    let freight_fcr = flt(frm.doc.custom_total_freight);
    let xr = flt(frm.doc.custom_xrxe_com);

    let sum_total_freight  = freight_fcr * xr;

    frm.set_value("custom_total_freight_inr", sum_total_freight);
}


// Function to calculate total landing price in INR based on the sum of total freight in INR and other components
function sum_landing_prices(frm) {
    let sum_total_freight = flt(frm.doc.custom_total_freight_inr);
    let dc = flt(frm.doc.custom_dc_inr);
    let shipping_line_charges = flt(frm.doc.custom_shipping_line_charges || 0);
    let cfs_charges = flt(frm.doc.custom_cfs_charges || 0);

    let total_landing_price = sum_total_freight + dc + shipping_line_charges + cfs_charges;

    frm.set_value("custom_total_landing_pricecinr", total_landing_price);
}

// Function to fetch exchange rate from the server and update the XR/ XE component, then recalculate the freight in INR
function fetch_exchange_rate(frm) {

    if (!frm.doc.custom_from_currency || !frm.doc.custom_to_currency) {
        return;
    }

    frappe.call({
        method: "merai_newage.merai_newage.api.get_exchange_rate",
        args: {
            from_currency: frm.doc.custom_from_currency,
            to_currency: frm.doc.custom_to_currency
        },
        callback: function(r) {

            if (r && r.message !== undefined) {

                frm.set_value("custom_xrxe_com", r.message);
                frm.refresh_field("custom_xrxe_com");

                calculate_sum_freight_and_xr(frm);
            }
        }
    });
}



function set_requisitioner_from_reference(frm) {
    // already set → do nothing
    if (frm.doc.custom_requisitioner && frm.doc.cost_center && frm.doc.plant) return;

    if (!frm.doc.items || !frm.doc.items.length) return;

    // 1️⃣ Try direct Material Request from PO items
    let mr = frm.doc.items.find(d => d.material_request)?.material_request;

    if (mr) {
        fetch_mr_details(frm, mr);
        return;
    }

    // 2️⃣ Try via Supplier Quotation
    let sq = frm.doc.items.find(d => d.supplier_quotation)?.supplier_quotation;

    if (!sq) return;

    frappe.db.get_value(
        "Supplier Quotation Item",
        { parent: sq },
        ["material_request"]
    ).then(r => {
        if (r.message?.material_request) {
            fetch_mr_details(frm, r.message.material_request);
        }
    });
}


function fetch_mr_details(frm, mr) {

    frappe.db.get_value(
        "Material Request",
        mr,
        [
            "custom_requisitioner",
            "custom_cost_center",
            "custom_plant" // change to custom_plant if needed
        ]
    ).then(r => {

        if (!r.message) return;

        // if (r.message.custom_requisitioner) {
        //     frm.set_value("custom_requisitioner", r.message.custom_requisitioner);
        // }

        if (r.message.custom_cost_center) {
            frm.set_value("cost_center", r.message.custom_cost_center);
        }

        if (r.message.custom_plant) {
            frm.set_value("plant", r.message.custom_plant); // change if custom field
        }

    });
}

// This function will fetch the details of the linked RFQ and set the corresponding fields in the Supplier Quotation form
function set_shipment_details_from_rfq(frm) {

    // prevent overwrite
    if (frm.doc.custom_shipment_mode) return;

    let rfq_name = null;

    if (frm.doc.items && frm.doc.items.length) {
        for (let item of frm.doc.items) {
            if (item.request_for_quotation) {
                rfq_name = item.request_for_quotation;
                break;
            }
        }
    }

    if (!rfq_name) return;

    frappe.db.get_doc('Request for Quotation', rfq_name).then(rfq => {
        if (!rfq) return;

        frm.set_value('custom_shipment_mode', rfq.custom_mode_of_shipment);
        frm.set_value('custom_vol_weightkg', rfq.custom_vol_weight);
        frm.set_value('custom_no_of_pkg_unit', rfq.custom_no_of_pkg_units);
        frm.set_value('custom_actual_weight', rfq.custom_actual_weights);
    });
}


// function toggle_previous_rate(frm) {

//     let show = frm.doc.custom_is_revision ? 1 : 0;

//     // child table column show/hide
//     frm.fields_dict.items.grid.update_docfield_property(
//         'custom_previous_rate_display',
//         'hidden',
//         show ? 0 : 1
//     );

//     frm.refresh_field('items');
// }

function toggle_base_rate_reqd(frm) {
    let is_required = frm.doc.custom_type !== "Logistics";

    frm.fields_dict.items.grid.update_docfield_property(
        'base_rate',
        'reqd',
        is_required ? 1 : 0
    );

    frm.refresh_field('items');
}