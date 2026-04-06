frappe.ready(function () {
    const params = new URLSearchParams(window.location.search);
    const rfq = params.get("rfq");
    const supplier = params.get("supplier");

    if (supplier) {
        frappe.web_form.set_value("supplier", supplier);

        frappe.call({
            method: "frappe.client.get_value",
            args: {
                doctype: "Supplier",
                filters: { name: supplier },
                fieldname: ["supplier_name"]
            },
            callback: function (r) {
                if (r.message) {
                    frappe.web_form.set_value("supplier_name", r.message.supplier_name);
                }
            }
        });
    }

    if (rfq) {
        frappe.call({
            method: "frappe.client.get",
            args: { doctype: "Request for Quotation", name: rfq },
            callback: function (r) {
                if (r.message) {
                    const doc = r.message;

                    frappe.web_form.set_value("company", doc.company);
                    frappe.web_form.set_value("plant", doc.custom_plant || "");
                    frappe.web_form.set_value("cost_center", doc.cost_center || "");
                    frappe.web_form.set_value("quotation_number", doc.name);
                    frappe.web_form.set_value("custom_rfq_reference", rfq);
					frappe.web_form.set_value("custom_type",doc.custom_type)

                    if (doc.items && doc.items.length > 0) {
                        frappe.web_form.doc.items = doc.items.map(function (item, index) {
                            return {
                                doctype: "Supplier Quotation Item",
                                name: "new-items-" + index,
                                __islocal: 1,
                                __unsaved: 1,
                                idx: index + 1,
                                item_code: item.item_code,
                                item_name: item.item_name || "",
                                description: item.description || "",
                                qty: item.qty,
                                uom: item.uom,
                                warehouse: item.warehouse || "",  
                                rate: 0,      
                                amount: 0,
								request_for_quotation:rfq

                            };
                        });

                        frappe.web_form.fields_dict['items'].refresh();

                        // ✅ Auto-calculate amount when rate is changed
                        frappe.web_form.fields_dict['items'].grid.wrapper
                            .on('change', 'input[data-fieldname="rate"]', function () {
                                recalculate_amounts();
                            });
                    }
                }
            }
        });
    }

    // ✅ Also recalculate on any grid input change (covers all edits)
    $(document).on('change', '.grid-body input', function () {
        recalculate_amounts();
    });

    function recalculate_amounts() {
        const items = frappe.web_form.doc.items || [];
        let updated = false;

        items.forEach(function (item) {
            const rate = parseFloat(item.rate) || 0;
            const qty  = parseFloat(item.qty)  || 0;
            const newAmount = rate * qty;

            if (item.amount !== newAmount) {
                item.amount = newAmount;
                updated = true;
            }
        });

        if (updated) {
            frappe.web_form.fields_dict['items'].refresh();
        }
    }

    // ✅ Validate before submit
    frappe.web_form.validate = function () {
        const items = frappe.web_form.doc.items || [];

        for (let i = 0; i < items.length; i++) {
            const item = items[i];
            const rate = parseFloat(item.rate) || 0;
            const qty  = parseFloat(item.qty)  || 0;

            if (rate <= 0) {
                frappe.msgprint({
                    title: "Validation Error",
                    message: `Row ${i + 1}: Please enter Rate for item <b>${item.item_code}</b>`,
                    indicator: "red"
                });
                return false;
            }
            // set final amount before save
            item.amount = rate * qty;
        }
        return true;
    };
});