
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


            if (frm.doc.operation) {
            frappe.db.get_doc("Operation", frm.doc.operation).then(op => {
                if (op.custom_line_clearance_template) {
                    let template_name = op.custom_line_clearance_template;

                    frappe.db.get_doc("Line Clearance Template", template_name).then(template => {
                        frm.clear_table("custom_line_clearance_checklist");

                        (template.line_clearence_checkpoints || []).forEach(row => {
                            let child = frm.add_child("custom_line_clearance_checklist");
                            child.line_clearance_criteria = row.line_clearance_criteria;
                            child.yesno = row.yesno;
                        });

                        frm.refresh_field("custom_line_clearance_checklist");
                    });
                }
            });
        }


if (frm.doc.operation) {
    frappe.db.get_doc("Operation", frm.doc.operation).then(op => {
        if (op.custom_feasibility_testing_template) {
            let template_name = op.custom_feasibility_testing_template;

            frappe.db.get_doc("Feasibility Testing Template", template_name).then(template => {
                frm.clear_table("custom_feasibility_testing");

                (template.feasibility_testing_template_details || []).forEach(row => {
                    let child = frm.add_child("custom_feasibility_testing");
                    child.feasibility_testing = row.feasibility_testing;   
                });

                frm.refresh_field("custom_feasibility_testing");
            });
        }
    });
}
if (frm.doc.bom_no && frm.doc.operation) {
    frappe.db.get_doc("BOM", frm.doc.bom_no).then(bom_doc => {
        frm.clear_table("custom_jobcard_opeartion_deatils");  

        (bom_doc.items || []).forEach(row => {
            if (row.operation === frm.doc.operation) {
                let child = frm.add_child("custom_jobcard_opeartion_deatils");
                child.item_code = row.item_code;
                child.item_name = row.item_name;
                child.item_description = row.description;
            }
        });

        frm.refresh_field("custom_jobcard_opeartion_deatils");
    });
}


    }
});