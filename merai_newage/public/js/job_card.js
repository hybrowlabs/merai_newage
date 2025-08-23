
frappe.ui.form.on("Job Card", {
    refresh: function (frm) {
        console.log("operation =", frm.doc.operation);

        if (!frm.doc.operation || !frm.doc.work_order) return;

        frappe.db.get_value("Operation", frm.doc.operation, "custom_quality_inspection_required")
            .then(r => {

                if (r.message && r.message.custom_quality_inspection_required) {
                    frm.add_custom_button(__('Create QI'), function () {
                        frappe.db.get_doc("Work Order", frm.doc.work_order).then(work_order_doc => {

                            let matched_items = (work_order_doc.required_items || []).filter(item => {
                                return item.operation === frm.doc.operation;
                            });


                            let qi = frappe.model.get_new_doc("Quality Inspection");
                            qi.reference_type = "Job Card";
                            qi.reference_name = frm.doc.name;
                            qi.inspection_type = "Incoming";
                            qi.item_code = work_order_doc.production_item;
                            qi.sample_size = frm.doc.for_quantity;
                            qi.inspected_by = frappe.session.user;


                            matched_items.forEach(item => {
                                let qi_item = frappe.model.add_child(qi, "QC Items", "custom_qc_items");
                                qi_item.item_code = item.item_code;
                                qi_item.item_name = item.item_name;
                                qi_item.item_description = item.description;
                            });

                          frappe.db.insert(qi).then(qi_doc => {
                            frm.set_value("quality_inspection", qi_doc.name);
                            frm.save().then(() => {
                                // setTimeout(function() {
                                //     frappe.msgprint(`Quality Inspection ${qi_doc.name} created in Draft.`);
                                // }, 1200); 
                                frappe.set_route("Form", "Quality Inspection", qi_doc.name);

                            });
                        });

                        });
                    });
                }
            });
    }
});