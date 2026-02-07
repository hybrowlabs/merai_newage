frappe.ui.form.on("Work Order", {

    on_submit(frm) {
        frappe.show_alert({
            message: __("Work Order Submitted"),
            indicator: "green"
        });

        // Reload document to reflect server-side changes
        frm.reload_doc();
    }
,
    refresh: function (frm) {
 setTimeout(function() {
        $('[data-original-title="Print"], .btn[title="Print"]').hide();
        
        frm.page.btn_secondary.find('.btn[data-original-title="Print"]').hide();
        
        $('.icon-btn svg use[href="#icon-printer"]').closest('.btn').hide();
    }, 100);
         if (frm.doc.docstatus===1) {
            frappe.db.count("Job Card", {
                filters: { work_order: frm.doc.name }
            }).then(count => {
                if (count > 0) {
                    frm.remove_custom_button("Create Job Card");
                    frm.remove_custom_button("Material Consumption");
                    frm.remove_custom_button("Create Pick List");
                    // frm.remove_custom_button("Finish");
                    frm.remove_custom_button("Start");


                }
            });
        }
        if (frm.doc.status === "Completed") {
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
        
        if (frm.doc.status === "Completed" && frm.doc.custom_is_full_dhr === 1) {
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
        if(frm.doc.docstatus === 1) {
        frm.add_custom_button(
                    __("BRC"),
                    function () {
                        frappe.call({
                            method: "merai_newage.merai_newage.doctype.batch_release_certificate.batch_release_certificate.create_brc",
                            args: {
                                work_order: frm.doc.name
                            },
                            freeze: true,
                            freeze_message: __("Creating BRC..."),
                            callback: function (r) {
                                if (r.message) {
                                    frappe.set_route(
                                        "Form",
                                        "Batch Release Certificate",
                                        r.message
                                    );
                                    frappe.show_alert({
                                        message: __("BRC created successfully"),
                                        indicator: "green"
                                    });
                                }
                            }
                        });
                    },
                    __("Make")  // This adds it to the "Create" dropdown
                );

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
                                let batch_no = first.message?.batch_no;
                                console.log("batch_no-----------------",batch_no)

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
                    // btn.removeClass('btn-default').addClass('btn-dark');
                }
                else {
                    console.log("All Operations must be completed to complete the Work Order")

                }
                                    }, 500);
    }
});