frappe.ui.form.on("Job Card", {
    refresh: function (frm) {
        // console.log("operation =", frm.doc.operation);

        if (!frm.doc.operation || !frm.doc.work_order) return;

        frappe.db.get_value("Operation", frm.doc.operation, "custom_quality_inspection_required")
            .then(r => {
                if (r.message && r.message.custom_quality_inspection_required) {
                    frm.add_custom_button(__('Create QI'), function () {
                        create_quality_inspection(frm);
                    });
                }
            });
            
        if(!frm.doc.custom_feasibility_testing_template){
            load_feasibility_testing_template(frm)
        }

        if (frm.is_new() || frm.doc.__islocal || !frm._software_fields_initialized) {
            setTimeout(() => {
                handle_software_fields(frm);
                // frm._software_fields_initialized = true;
            }, 500);
        }

        load_form_data(frm);
    },

    operation: function(frm) {
        if (frm.doc.operation) {
            frm._last_line_clearance_operation = null;
            frm._last_feasibility_operation = null;
            frm._last_bom_operation = null;
            frm._software_fields_initialized = null; // Reset to trigger re-initialization
            
            load_form_data(frm);
            handle_software_fields(frm);
            frm._software_fields_initialized = true;
        }
    },
    
    bom_no: function(frm) {
        if (frm.doc.bom_no) {
            // Clear previous BOM tracking
            frm._last_bom_no = null;
            frm._last_bom_operation = null;
            
            // Reload BOM data
            if (should_load_bom_details(frm)) {
                load_bom_operation_details(frm).then(() => {
                    toggle_custom_tab(frm);
                });
            }
        }
    },

    // Handle item_code field changes
    production_item: function(frm) {
        if (frm.doc.production_item) {
            // Clear previous feasibility tracking
            frm._last_feasibility_operation = null;
            
            // Reload feasibility testing data
            load_feasibility_testing_template(frm).then(() => {
                toggle_feasibility_tab(frm);
            });
        } else {
            // Clear feasibility testing if no item selected
            frm.clear_table("custom_feasibility_testing");
            frm.set_value("custom_feasibility_testing_template", "");
            frm.refresh_field("custom_feasibility_testing");
            frm.set_df_property("custom_feasibility_testing", "hidden", 1);
        }
    },

    // Handle template field changes
    custom_feasibility_testing_template: function(frm) {
        if (frm.doc.custom_feasibility_testing_template) {
            load_feasibility_testing_from_template(frm, frm.doc.custom_feasibility_testing_template);
        } else {
            frm.clear_table("custom_feasibility_testing");
            frm.refresh_field("custom_feasibility_testing");
            frm.set_df_property("custom_feasibility_testing", "hidden", 1);
        }
    }
});

function create_quality_inspection(frm) {
    const software_operations = [
        "MISSO Robotic Execution Software-Arm Cart",
        "MISSO Robotic Execution Software",
        "MISSO Planning Software"
    ];

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
        qi.manual_inspection=1
        // console.log("104========")
        if (software_operations.includes(frm.doc.operation)) {
            // Case 2: Software operations
            qi.custom_software = frm.doc.operation;
            frappe.db.insert(qi).then(qi_doc => {
                frm.set_value("quality_inspection", qi_doc.name);
                frm.save().then(() => {
                    frappe.set_route("Form", "Quality Inspection", qi_doc.name);

                });
            });
        } else {
            matched_items.forEach(item => {
                let qi_item = frappe.model.add_child(qi, "QC Items", "custom_qc_items");
                qi_item.item_code = item.item_code;
                qi_item.item_name = item.item_name;
                qi_item.item_description = item.description;
            });

            frappe.db.insert(qi).then(qi_doc => {
                frm.set_value("quality_inspection", qi_doc.name);
                frm.save().then(() => {
                    frappe.set_route("Form", "Quality Inspection", qi_doc.name);
                });
            });
        }
    });
}

function load_form_data(frm) {
    let promises = [];

    if (should_load_line_clearance(frm)) {
        promises.push(load_line_clearance_template(frm));
    }

    if (should_load_feasibility_testing(frm)) {
        promises.push(load_feasibility_testing_template(frm));
    }

    if (should_load_bom_details(frm)) {
        promises.push(load_bom_operation_details(frm));
    }

    Promise.all(promises).then(() => {
        setTimeout(() => {
            toggle_custom_tab(frm);
            toggle_lineclearance_tab(frm);
        }, 100);
    });
}

function should_load_line_clearance(frm) {
    return frm.doc.operation && 
           (!frm.doc.custom_line_clearance_checklist || 
            frm.doc.custom_line_clearance_checklist.length === 0 ||
            frm._last_line_clearance_operation !== frm.doc.operation);
}

function should_load_feasibility_testing(frm) {
    return frm.doc.production_item && 
           (!frm.doc.custom_feasibility_testing || 
            frm.doc.custom_feasibility_testing.length === 0 ||
            frm._last_feasibility_operation !== frm.doc.operation);
}

function should_load_bom_details(frm) {
    return frm.doc.bom_no && frm.doc.operation && 
           (!frm.doc.custom_jobcard_opeartion_deatils || 
            frm.doc.custom_jobcard_opeartion_deatils.length === 0 ||
            frm._last_bom_operation !== frm.doc.operation ||
            frm._last_bom_no !== frm.doc.bom_no);
}

function load_line_clearance_template(frm) {
    return frappe.db.get_doc("Operation", frm.doc.operation).then(op => {
        if (op.custom_line_clearance_template) {
            let template_name = op.custom_line_clearance_template;

            return frappe.db.get_doc("Line Clearance Template", template_name).then(template => {
                frm.clear_table("custom_line_clearance_checklist");

                (template.line_clearence_checkpoints || []).forEach(row => {
                    let child = frm.add_child("custom_line_clearance_checklist");
                    child.line_clearance_criteria = row.line_clearance_criteria;
                    child.yesno = row.yesno;
                });

                frm.refresh_field("custom_line_clearance_checklist");
                frm._last_line_clearance_operation = frm.doc.operation;
            });
        }
    });
}

function load_feasibility_testing_template(frm) {
    frm.set_df_property("custom_feasibility_testing", "hidden", 1);

    if (!frm.doc.production_item) {
        frm.clear_table("custom_feasibility_testing");
        frm.set_value("custom_feasibility_testing_template", "");
        frm.refresh_field("custom_feasibility_testing");
        return Promise.resolve();
    }

    return frappe.db.get_doc("Item", frm.doc.production_item).then(item => {
        let template_name = item.custom_feasibility_testing_template || "";
    
        if (frm.doc.custom_feasibility_testing_template !== template_name) {
            frm.set_value("custom_feasibility_testing_template", template_name);
        }

        if (!template_name) {
            frm.clear_table("custom_feasibility_testing");
            frm.refresh_field("custom_feasibility_testing");
            return Promise.resolve();
        }

        return load_feasibility_testing_from_template(frm, template_name, item);
    });
}

function load_feasibility_testing_from_template(frm, template_name, item_doc = null) {
    return frappe.db.get_doc("Feasibility Testing Template", template_name).then(template => {
        frm.clear_table("custom_feasibility_testing");

        (template.feasibility_testing_template_details || []).forEach(template_row => {
            let child = frm.add_child("custom_feasibility_testing");
            child.feasibility_testing = template_row.feasibility_testing;
            
            // If item_doc is provided (from Item), try to get existing values
            if (item_doc && item_doc.custom_feasibility_testing_details) {
                let existing_row = item_doc.custom_feasibility_testing_details.find(
                    item_row => item_row.feasibility_testing === template_row.feasibility_testing
                );
                
                if (existing_row) {
                    // Copy all fields from Item's feasibility testing details
                    Object.keys(existing_row).forEach(key => {
                        if (key !== 'name' && key !== 'parent' && key !== 'parentfield' && key !== 'parenttype' && key !== 'idx') {
                            child[key] = existing_row[key];
                        }
                    });
                }
            }
        });

        frm.refresh_field("custom_feasibility_testing");
        frm._last_feasibility_operation = frm.doc.operation;

        // Show table only if rows exist
        if ((frm.doc.custom_feasibility_testing || []).length > 0) {
            frm.set_df_property("custom_feasibility_testing", "hidden", 0);
        }
    });
}
function load_bom_operation_details(frm) {
    const software_operations = [
        "MISSO Robotic Execution Software-Arm Cart",
        "MISSO Robotic Execution Software",
        "MISSO Planning Software"
    ];

    // if operation is in software_operations -> just clear & hide
    if (software_operations.includes(frm.doc.operation)) {
        frm.clear_table("custom_jobcard_opeartion_deatils");
        frm.refresh_field("custom_jobcard_opeartion_deatils");

        // hide the child table field
        frm.set_df_property("custom_jobcard_opeartion_deatils", "hidden", 1);
        return;
    }

    // otherwise fetch from BOM and populate
    return frappe.db.get_doc("BOM", frm.doc.bom_no).then(bom_doc => {
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

        // show back the table if rows exist
        let has_rows = (frm.doc.custom_jobcard_opeartion_deatils || []).length > 0;
        frm.set_df_property("custom_jobcard_opeartion_deatils", "hidden", has_rows ? 0 : 1);

        frm._last_bom_operation = frm.doc.operation;
        frm._last_bom_no = frm.doc.bom_no;
    });
}


function toggle_custom_tab(frm) {
    let has_rows = (frm.doc.custom_jobcard_opeartion_deatils || []).length > 0;
    // console.log("Has rows:", has_rows);
    
    frm.set_df_property("custom_opeartions_list", "hidden", !has_rows);
    frm.set_df_property("custom_jobcard_opeartion_deatils", "hidden", !has_rows);
    //  frm.clear_table("custom_jobcard_opeartion_deatils");

    frm.refresh_fields();
}




function toggle_lineclearance_tab(frm) {
    let has_rows = (frm.doc.custom_line_clearance_checklist || []).length > 0;
    console.log("Line clearance has rows:", has_rows);
    
    frm.set_df_property("custom_line_clearance", "hidden", !has_rows);
    frm.set_df_property("custom_line_clearance_checklist", "hidden", !has_rows);

    frm.refresh_fields();
}

function toggle_feasibility_tab(frm) {
    let has_rows = (frm.doc.custom_feasibility_testing || []).length > 0;
    // console.log("Feasibility testing has rows:", has_rows);
    
    frm.set_df_property("custom_feasibility_test", "hidden", !has_rows);
    frm.set_df_property("custom_feasibility_testing", "hidden", !has_rows);

    frm.refresh_fields();
}

function handle_software_fields(frm) {
    const software_operations = [
        "MISSO Robotic Execution Software-Arm Cart",
        "MISSO Robotic Execution Software",
        "MISSO Planning Software"
    ];

    if (frm.doc.operation && software_operations.includes(frm.doc.operation)) {
        frm.set_df_property("custom_software", "hidden", 0);
        frm.set_df_property("custom_version", "hidden", 0);
        frm.set_df_property("custom_installed", "hidden", 0);

        if (frm.doc.custom_software !== frm.doc.operation) {
            frm.set_value("custom_software", frm.doc.operation);
        }
        
        frm.clear_table("custom_jobcard_opeartion_deatils");
        frm.refresh_field("custom_jobcard_opeartion_deatils");
        frm.set_df_property("custom_jobcard_opeartion_deatils", "hidden", 1);

    } else {
        frm.set_df_property("custom_software", "hidden", 1);
        frm.set_df_property("custom_version", "hidden", 1);
        frm.set_df_property("custom_installed", "hidden", 1);

        // toggle_custom_tab(frm);
    }

    frm.refresh_fields();
}
