frappe.ui.form.on("Supplier Quotation", {
    // This trigger will run when the form is refreshed, and it will add a custom button to view the revision history of the RFQ if the document is submitted and is the latest revision.
    refresh(frm) {
        calculate_freight(frm);
        set_requisitioner_from_reference(frm);

    },

    custom_rate_kg: function(frm) {
        calculate_freight(frm);
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