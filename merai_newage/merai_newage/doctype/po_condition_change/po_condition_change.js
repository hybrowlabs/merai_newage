frappe.ui.form.on("PO Condition Change", {
    refresh: function (frm) {

        if (frm.doc.docstatus == 1) {

            frm.add_custom_button("e-Waybill", function () {

                let items = [];
                let total_amount = 0;

                // 🔹 Child table se items uthao
                if (frm.doc.po_condition_change_items) {
                    frm.doc.po_condition_change_items.forEach(item => {

                        items.push({
                            purchase_order: item.purchasing_doc,
                            item_code: item.material,
                            item_name: item.material,
                            qty: item.order_quantity,
                            po_qty: item.order_quantity,
                            total_inr_value: item.amount,
                            rate: item.amount / (item.order_quantity || 1),
                            amount: item.amount,
                            currency: item.currency || frm.doc.currency,
                            rate_inr: item.amount / (item.order_quantity || 1)
                        });

                        total_amount += item.amount;
                    });
                }

                // 🔹 E-Waybill create karo
                frappe.call({
                    method: "frappe.client.insert",
                    args: {
                        doc: {
                            doctype: "E-way Bill",

                            // 🔥 SAME LOGIC (important)
                            select_doctype: frm.doctype,
                            doctype_id: frm.doc.name,

                            pre_alert_check_list: frm.doc.pre_alert_req,
                            supplier: frm.doc.vendor,

                            items: items
                        }
                    },
                    callback: function (r) {
                        if (r.message) {
                            frappe.set_route("Form", "E-way Bill", r.message.name);
                        }
                    }
                });

            }, __("Create"));
        }
    }
});