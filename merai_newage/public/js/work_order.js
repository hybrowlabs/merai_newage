frappe.ui.form.on("Work Order", {
    refresh: function (frm) {
        if (frm.doc.docstatus == 1) {
            frm.add_custom_button("Print DHR", function () {
                frappe.call({
                    method: "merai_newage.overrides.work_order.print_work_order_async",
                    args: {
                        name: frm.doc.name
                    },
                    freeze: true,
                    freeze_message: "Printing DHR...",
                    callback: function (response) {
                        window.open(window.location.origin + response.filecontent);
                    }
                });
            });
        }
        
        if (frm.doc.docstatus == 1 && frm.doc.custom_is_full_dhr === 1) {
            frm.add_custom_button("Print Full DHR", function () {
                frappe.call({
                    method: "merai_newage.overrides.work_order.print_full_bmr",
                    args: {
                        name: frm.doc.name
                    },
                    freeze: true,
                    freeze_message: "Printing Full DHR...",
                    callback: function (response) {
                        window.open(window.location.origin + response.filecontent);
                    }
                });
            });
        }


        setTimeout(() => {
                        var completed = true;
                        console.log("-----324------",frm.doc.operations)
                        if (frm.doc.operations && Array.isArray(frm.doc.operations) && frm.doc.operations.length > 0) {
                            frm.doc.operations.forEach(function (row) {
                                if (row.completed_qty <= 0) {
                                    completed = false;
                                }
                            });
                        } else {
                            console.warn("⚠️ No operations found in the document (yet).");
                            completed = false;
                        }

                        console.log("-----------328---------", completed);

                if (frm.doc.status == "In Process" && completed) {
                    let btn = frm.add_custom_button("Completed Work Order", async function () {
                        try {
                            // 1st call
                            let first = await frappe.call({
                                method: "merai_newage.overrides.work_order.complete_work_order",
                                args: { doc_name: frm.doc.name }
                            });

                            if (first.message) {
                                frappe.show_alert({
                                    message: __("Work Order Completed Successfully"),
                                    indicator: "green"
                                });
                                await frm.reload_doc();
                            }
                            let batch_no = first.message.batch_no;

                            // 2nd call (runs only after first is finished)
                            let second = await frappe.call({
                                method: "merai_newage.overrides.work_order.create_fg_consumption_entry",
                                args: {
                                    doc_name: frm.doc.name,
                                    batch_no: batch_no
                                }
                            });

                            if (second.message) {
                                frappe.show_alert({
                                    message: __("FG Consumption Entry Created Successfully"),
                                    indicator: "green"
                                });
                            }
                        } catch (e) {
                            frappe.msgprint(__("Something went wrong: ") + e.message);
                        }
                    });
                    btn.removeClass('btn-default').addClass('btn-dark');
                }
                else {
                    frappe.message("All Operations must be completed to complete the Work Order")

                }
                                    }, 500);
    }
});