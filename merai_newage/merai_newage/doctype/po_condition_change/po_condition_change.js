// frappe.ui.form.on("PO Condition Change", {
//     refresh: function (frm) {

//         if (frm.doc.docstatus == 1) {

//             frm.add_custom_button("e-Waybill", function () {

//                 let items = [];
//                 let total_amount = 0;

//                 // 🔹 Child table se items uthao
//                 if (frm.doc.po_condition_change_items) {
//                     frm.doc.po_condition_change_items.forEach(item => {

//                         items.push({
//                             purchase_order: item.purchasing_doc,
//                             item_code: item.material,
//                             item_name: item.material,
//                             qty: item.order_quantity,
//                             po_qty: item.order_quantity,
//                             total_inr_value: item.amount,
//                             rate: item.amount / (item.order_quantity || 1),
//                             amount: item.amount,
//                             currency: item.currency || frm.doc.currency,
//                             rate_inr: item.amount / (item.order_quantity || 1)
//                         });

//                         total_amount += item.amount;
//                     });
//                 }

//                 // 🔹 E-Waybill create karo
//                 frappe.call({
//                     method: "frappe.client.insert",
//                     args: {
//                         doc: {
//                             doctype: "E-way Bill",

//                             //SAME LOGIC (important)
//                             select_doctype: frm.doctype,
//                             doctype_id: frm.doc.name,

//                             pre_alert_check_list: frm.doc.pre_alert_req,
//                             supplier: frm.doc.vendor,

//                             items: items
//                         }
//                     },
//                     callback: function (r) {
//                         if (r.message) {
//                             frappe.set_route("Form", "E-way Bill", r.message.name);
//                         }
//                     }
//                 });

//             }, __("Create"));
//         }
//     }
// });


frappe.ui.form.on("PO Condition Change", {
    refresh: function (frm) {

        // 🔹 Attachment Sync (NEW ADD)
        if (!frm._attachment_sync_bound && frm.attachments) {
            frm._attachment_sync_bound = true;

            frm.attachments.on("change", function () {
                if (merai?.sync_workflow_attachment_table) {
                    merai.sync_workflow_attachment_table(frm);
                }
            });
        }

        // 🔹 GET DETAIL BUTTON (BOE Entry se data lana)
        if (frm.doc.docstatus == 0) {
            frm.add_custom_button("BOE Entry", function () {

                new frappe.ui.form.MultiSelectDialog({
                    doctype: "BOE Entry",
                    target: frm,
                    setters: {},
                    add_filters_group: 1,
                    date_field: "boe_date",
                    columns: ["name", "boe_no", "boe_date", "vendor"],

                    get_query() {
                        return {
                            filters: {
                                docstatus: ["!=", 2],
                            },
                        };
                    },

                    action: function (selections) {

                        this.dialog.hide();

                        if (!selections.length) {
                            frappe.msgprint("Please select BOE Entry");
                            return;
                        }

                        let boe_name = selections[0];

                        frappe.call({
                            method: "merai_newage.merai_newage.doctype.po_condition_change.po_condition_change.get_boe_all_details",
                            args: {
                                boe_name: boe_name
                            },
                            callback: function (r) {
                                let data = r.message;

                                // 🔹 HEADER MAPPING
                                frm.set_value("boe_entry_reference", data.name);
                                frm.set_value("boe_no", data.boe_no);
                                frm.set_value("boe_date", data.boe_date);
                                frm.set_value("pre_alert_req", data.per_alert_check);
                                frm.set_value("pickup_req", data.pickup_request);
                                frm.set_value("rfq_number", data.request_for_quotation);
                                frm.set_value("vendor", data.vendor);
                                frm.set_value("vendor_name", data.custom_vendor_name);
                                frm.set_value("cha_vendor", data.cha);
                                frm.set_value("cha_name", data.custom_cha_name);
                                frm.set_value("exchange_rate", data.exchange_rate);

                                frm.set_value("bcd_amt", data.bcd_amount);
                                frm.set_value("h_cess_amt", data.h_cess_amount);
                                frm.set_value("sws_amt", data.sws_amount);
                                frm.set_value("igst_amt", data.igst_amount);
                                frm.set_value("total_duty", data.total_duty);

                                frm.set_value("freight_amt", data.total_freight);
                                frm.set_value("other_chrg", data.other_charges);
                                frm.set_value("total_inr_val", data.total_inr_value);
                                frm.set_value("accessible_val", data.accessible_value);

                                frm.set_value("check_list_date", data.check_list_date);
                                frm.set_value("job_number", data.job_number);
                                frm.set_value("ad_code", data.ad_code);
                                frm.set_value("penalty", data.penalty);

                                // 🔹 CHILD TABLE (optional – uncomment if needed)
                                /*
                                frm.clear_table("po_condition_change_items");

                                (data.boe_entries || []).forEach(row => {
                                    let child = frm.add_child("po_condition_change_items");

                                    child.purchasing_doc = row.po_number;
                                    child.order_quantity = row.total_qty;
                                    child.amount = row.total_inr_value;
                                    child.currency = data.currency;
                                    child.vendor = data.vendor;
                                });

                                frm.refresh_field("po_condition_change_items");
                                */
                            }
                        });
                    }
                });

            }, __("Get Detail"));
        }


        // 🔹 EXISTING E-WAYBILL BUTTON (UNCHANGED)
        // if (frm.doc.docstatus == 1) {

        //     frm.add_custom_button("e-Waybill", function () {

        //         let items = [];
        //         let total_amount = 0;

        //         if (frm.doc.po_condition_change_items) {
        //             frm.doc.po_condition_change_items.forEach(item => {

        //                 items.push({
        //                     purchase_order: item.purchasing_doc,
        //                     item_code: item.material,
        //                     item_name: item.material,
        //                     qty: item.order_quantity,
        //                     po_qty: item.order_quantity,
        //                     total_inr_value: item.amount,
        //                     rate: item.amount / (item.order_quantity || 1),
        //                     amount: item.amount,
        //                     currency: item.currency || frm.doc.currency,
        //                     rate_inr: item.amount / (item.order_quantity || 1)
        //                 });

        //                 total_amount += item.amount;
        //             });
        //         }

        //         frappe.call({
        //             method: "frappe.client.insert",
        //             args: {
        //                 doc: {
        //                     doctype: "E-way Bill",
        //                     select_doctype: frm.doctype,
        //                     doctype_id: frm.doc.name,
        //                     pre_alert_check_list: frm.doc.pre_alert_req,
        //                     supplier: frm.doc.vendor,
        //                     items: items
        //                 }
        //             },
        //             callback: function (r) {
        //                 if (r.message) {
        //                     frappe.set_route("Form", "E-way Bill", r.message.name);
        //                 }
        //             }
        //         });

        //     }, __("Create"));
        // }
        if (frm.doc.docstatus == 1) {

            frm.add_custom_button("e-Waybill", function () {

                // Prevent double click
                if (frm.__creating_ewb) return;
                frm.__creating_ewb = true;

                // Already created check
                if (frm.doc.e_way_bill) {
                    frappe.msgprint("E-Way Bill already created");
                    frappe.set_route("Form", "E-way Bill", frm.doc.e_way_bill);
                    frm.__creating_ewb = false;
                    return;
                }

                let items = [];
                let total_amount = 0;

                let source_items = frm.doc.items || [];

                // No items
                if (!source_items.length) {
                    frappe.msgprint("No items found in PO Condition Change");
                    frm.__creating_ewb = false;
                    return;
                }

                source_items.forEach(item => {

                    // Skip if no item_code
                    if (!item.item_code) return;

                    let qty = item.qty || 0;
                    let amt = item.amount || 0;

                    items.push({
                        purchase_order: item.purchase_order || "",
                        item_code: item.item_code,
                        item_name: item.item_name || item.item_code,
                        qty: qty,
                        po_qty: item.po_qty || qty,
                        total_inr_value: amt,
                        rate: qty ? (amt / qty) : 0,
                        amount: amt,
                        currency: item.currency || frm.doc.currency,
                        rate_inr: qty ? (amt / qty) : 0
                    });

                    total_amount += amt;
                });

                // No valid items after filtering
                if (!items.length) {
                    frappe.msgprint("No valid items found. Check item_code and qty.");
                    frm.__creating_ewb = false;
                    return;
                }

                // Create E-Way Bill
                frappe.call({
                    method: "frappe.client.insert",
                    args: {
                        doc: {
                            doctype: "E-way Bill",
                            select_doctype: frm.doctype,
                            doctype_id: frm.doc.name,
                            pre_alert_check_list: frm.doc.pre_alert_req,
                            supplier: frm.doc.vendor,
                            total_amount: total_amount,
                            items: items
                        }
                    },
                    callback: function (r) {
                        frm.__creating_ewb = false;

                        if (r.message) {

                            // 🔗 Save link back
                            frappe.db.set_value(
                                "PO Condition Change",
                                frm.doc.name,
                                "e_way_bill",
                                r.message.name
                            );

                            frappe.set_route("Form", "E-way Bill", r.message.name);
                        } else {
                            frappe.msgprint("Failed to create E-Way Bill");
                        }
                    },
                    error: function () {
                        frm.__creating_ewb = false;
                        frappe.msgprint("Server error while creating E-Way Bill");
                    }
                });

            }, __("Create"));
        }
    },
    // 🔹 Attachment Sync hooks
    after_save: function(frm) {
        if (merai?.sync_workflow_attachment_table) {
            merai.sync_workflow_attachment_table(frm);
        }
    },

    on_submit: function(frm) {
        if (merai?.sync_workflow_attachment_table) {
            merai.sync_workflow_attachment_table(frm);
        }
        if (frm.doc.eway_bill_reference) {

            frappe.db.set_value(
                "E-way Bill",
                frm.doc.eway_bill_reference,
                "custom_po_condition_change",
                frm.doc.name
            ).then(() => {
                frappe.set_route("Form", "E-way Bill", frm.doc.eway_bill_reference);
            });
        }
    }

});