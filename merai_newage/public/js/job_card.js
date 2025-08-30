

frappe.ui.form.on("Job Card", {
    refresh: function (frm) {
        // Prevent multiple refresh calls in short time
        if (frm._refresh_in_progress) return;
        frm._refresh_in_progress = true;
        setTimeout(() => frm._refresh_in_progress = false, 1000);

        if (!frm.doc.operation || !frm.doc.work_order) return;
        
        if(frm.doc.docstatus!=1 && !frm.doc.quality_inspection){
            frappe.db.get_value("Operation", frm.doc.operation, "custom_quality_inspection_required")
                .then(r => {
                    if (r.message && r.message.custom_quality_inspection_required) {
                        frm.add_custom_button(__('Create QI'), function () {
                            create_quality_inspection(frm);
                        });
                    }
                });
        }
        
         if ((frm.is_new() || frm.doc.__islocal) && frm.doc.docstatus != 1) {
            console.log("====refresh==========")
            if (!frm.doc.custom_feasibility_testing_template) {
                console.log("refresh=====2")
                load_feasibility_testing_template(frm);
            }
            if (!frm.doc.custom_line_clearance_template) {
                load_line_clearance_template(frm);
            }
        }


        // Only load templates if they don't exist and doc is not submitted
        // if(!frm.doc.custom_feasibility_testing_template && frm.doc.docstatus!=1){
        //     load_feasibility_testing_template(frm)
        // }
        
        // if(!frm.doc.custom_line_clearance_template && frm.doc.docstatus!=1){
        //     load_line_clearance_template(frm);
        // }
        
        if (frm.is_new() || frm.doc.__islocal || !frm._software_fields_initialized) {
            setTimeout(() => {
                handle_software_fields(frm);
            }, 500);
        }
        
        if (frm.is_new() || frm.doc.__islocal) {
            setTimeout(() => {
                hide_tabs_and_tables_if_templates_empty(frm);
            }, 2500);
        }
        
        load_form_data(frm);
    },

    operation: function(frm) {
        // Prevent cascading events during refresh
        if (frm._refresh_in_progress) return;
        
        if (frm.doc.operation) {
            frm._last_line_clearance_operation = null;
            frm._last_feasibility_operation = null;
            frm._last_bom_operation = null;
            frm._software_fields_initialized = null; 
            
            // Use timeout to prevent immediate cascading
            clearTimeout(frm._operation_timeout);
            frm._operation_timeout = setTimeout(() => {
                load_form_data(frm);
                handle_software_fields(frm);
                frm._software_fields_initialized = true;
            }, 200);
        }
    },
    
    bom_no: function(frm) {
        if (frm._refresh_in_progress) return;
        
        if (frm.doc.bom_no) {
            frm._last_bom_no = null;
            frm._last_bom_operation = null;
            
            clearTimeout(frm._bom_timeout);
            frm._bom_timeout = setTimeout(() => {
                if (should_load_bom_details(frm)) {
                    load_bom_operation_details(frm).then(() => {
                        toggle_custom_tab(frm);
                    });
                }
            }, 200);
        }
    },

    production_item: function(frm) {
        if (frm._refresh_in_progress) return;
        
        if (frm.doc.production_item) {
            frm._last_feasibility_operation = null;
            
            clearTimeout(frm._item_timeout);
            frm._item_timeout = setTimeout(() => {
                console.log("============production item")
                load_feasibility_testing_template(frm).then(() => {
                    toggle_feasibility_tab(frm);
                });
            }, 200);
        } else {
            frm.clear_table("custom_feasibility_testing");
            frm.doc.custom_feasibility_testing_template = "";
            frm.refresh_field("custom_feasibility_testing_template");
            frm.refresh_field("custom_feasibility_testing");
            frm.set_df_property("custom_feasibility_testing", "hidden", 1);
        }
    },

    custom_feasibility_testing_template: function(frm) {
        if (frm._loading_feasibility_template || frm._refresh_in_progress) return;
        
        if (frm.doc.custom_feasibility_testing_template) {
            frm._loading_feasibility_template = true;
            load_feasibility_testing_from_template(frm, frm.doc.custom_feasibility_testing_template).then(() => {
                frm._loading_feasibility_template = false;
            }).catch(() => {
                frm._loading_feasibility_template = false;
            });
        } else {
            frm.clear_table("custom_feasibility_testing");
            frm.refresh_field("custom_feasibility_testing");
            frm.set_df_property("custom_feasibility_testing", "hidden", 1);
        }
    },
    
    custom_line_clearance_template: function(frm) {
        if (frm._loading_line_clearance_template || frm._refresh_in_progress) return;
        
        if (frm.doc.custom_line_clearance_template) {
            frm._loading_line_clearance_template = true;
            load_line_clearnce_from_template(frm, frm.doc.custom_line_clearance_template).then(() => {
                frm._loading_line_clearance_template = false;
            }).catch(() => {
                frm._loading_line_clearance_template = false;
            });
        } else {
            frm.clear_table("custom_line_clearance_checklist_details");
            frm.refresh_field("custom_line_clearance_checklist_details");
            frm.set_df_property("custom_line_clearance_checklist_details", "hidden", 1);
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
        qi.inspection_type = "In Process";
        qi.item_code = work_order_doc.production_item;
        qi.sample_size = frm.doc.for_quantity;
        qi.inspected_by = frappe.session.user;
        qi.manual_inspection=1

        if (software_operations.includes(frm.doc.operation)) {
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
    
    if(frm.doc.docstatus!=1){
        // if (should_load_line_clearance(frm)) {
        //     console.log("==========")
        //     promises.push(load_line_clearance_template(frm));
        // }

        // if (should_load_feasibility_testing(frm)) {
        //     console.log("======load form data=====")
        //     promises.push(load_feasibility_testing_template(frm));
        // }

        // Only load if the table is empty (length is 0), or if it's a new doc
if ((frm.doc.__islocal || !(frm.doc.custom_line_clearance_checklist_details && frm.doc.custom_line_clearance_checklist_details.length > 0))) {
    promises.push(load_line_clearance_template(frm));
}
if ((frm.doc.__islocal || !(frm.doc.custom_feasibility_testing && frm.doc.custom_feasibility_testing.length > 0))) {
    promises.push(load_feasibility_testing_template(frm));
}
if ((frm.doc.__islocal || !(frm.doc.custom_jobcard_opeartion_deatils.length > 0))) {
    promises.push(load_bom_operation_details(frm));
}

        // if (should_load_bom_details(frm)) {
        //     promises.push(load_bom_operation_details(frm));
        // }

        Promise.all(promises).then(() => {
            setTimeout(() => {
                toggle_custom_tab(frm);
                toggle_lineclearance_tab(frm);
            }, 1000);
        });
    }
}

function should_load_line_clearance(frm) {
    return   frm.doc.operation 
        && (!frm.doc.custom_line_clearance_checklist_details 
            || frm.doc.custom_line_clearance_checklist_details.length === 0)
        && frm._last_line_clearance_operation !== frm.doc.operation;
}

function should_load_feasibility_testing(frm) {
    return  frm.doc.production_item && 
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

function load_feasibility_testing_template(frm) {
    if (frm._loading_feasibility_template) {
        return Promise.resolve();
    }
    
    frm.set_df_property("custom_feasibility_testing", "hidden", 1);

    if (!frm.doc.production_item) {
        frm.clear_table("custom_feasibility_testing");
        frm.doc.custom_feasibility_testing_template = "";
        frm.refresh_field("custom_feasibility_testing_template");
        frm.refresh_field("custom_feasibility_testing");
        return Promise.resolve();
    }

    frm._loading_feasibility_template = true;
    
    return frappe.db.get_doc("Operation", frm.doc.operation).then(operation_doc => {
        let template_name = operation_doc.custom_feasibility_testing_template || "";
        console.log("=====728====feasibility================", template_name);
        
        if (frm.doc.custom_feasibility_testing_template !== template_name) {
            frm.doc.custom_feasibility_testing_template = template_name;
            frm.refresh_field("custom_feasibility_testing_template");
        }

        if (!template_name) {
            frm.clear_table("custom_feasibility_testing");
            frm.refresh_field("custom_feasibility_testing");
            frm._loading_feasibility_template = false;
            return Promise.resolve();
        }

        return load_feasibility_testing_from_template(frm, template_name, operation_doc).then(() => {
            frm._loading_feasibility_template = false;
        });
    }).catch(err => {
        frm._loading_feasibility_template = false;
        console.error("Error in load_feasibility_testing_template:", err);
        return Promise.resolve();
    });
}


function load_feasibility_testing_from_template(frm, template_name, operation_doc = null) {
    return frappe.db.get_doc("Feasibility Testing Template", template_name).then(template => {
        frm.clear_table("custom_feasibility_testing");

        (template.feasibility_testing_template_details || []).forEach(template_row => {
            let child = frm.add_child("custom_feasibility_testing");
            child.feasibility_testing = template_row.feasibility_testing;
            
            // ✅ fetch from Operation instead of Item
            if (operation_doc && operation_doc.custom_feasibility_testing_details) {
                let existing_row = operation_doc.custom_feasibility_testing_details.find(
                    op_row => op_row.feasibility_testing === template_row.feasibility_testing
                );
                
                if (existing_row) {
                    Object.keys(existing_row).forEach(key => {
                        if (!['name','parent','parentfield','parenttype','idx'].includes(key)) {
                            child[key] = existing_row[key];
                        }
                    });
                }
            }
        });

        frm.refresh_field("custom_feasibility_testing");
        frm._last_feasibility_operation = frm.doc.operation;

        if ((frm.doc.custom_feasibility_testing || []).length > 0) {
            frm.set_df_property("custom_feasibility_testing", "hidden", 0);
        }
    }).catch(err => {
        console.error("Error loading feasibility testing template:", err);
    });
}

function load_line_clearance_template(frm) {
    if (frm._loading_line_clearance_template) {
        return Promise.resolve();
    }
    
    frm.set_df_property("custom_line_clearance_checklist_details", "hidden", 1);

    frm._loading_line_clearance_template = true;
    
    return frappe.db.get_doc("Operation", frm.doc.operation).then(item => {
        let template_name = item.custom_line_clearance_template || "";
    
        // Only update if different to avoid triggering events
        if (frm.doc.custom_line_clearance_template !== template_name) {
            frm.doc.custom_line_clearance_template = template_name;
            frm.refresh_field("custom_line_clearance_template");
        }

        if (!template_name) {
            frm.clear_table("custom_line_clearance_checklist_details");
            frm.refresh_field("custom_line_clearance_checklist_details");
            frm._loading_line_clearance_template = false;
            return Promise.resolve();
        }

        return load_line_clearnce_from_template(frm, template_name, item).then(() => {
            frm._loading_line_clearance_template = false;
        });
    }).catch(err => {
        frm._loading_line_clearance_template = false;
        console.error("Error in load_line_clearance_template:", err);
        return Promise.resolve();
    });
}

function load_line_clearnce_from_template(frm, template_name, item_doc = null) {
    return frappe.db.get_doc("Line Clearance Template", template_name).then(template => {
        frm.clear_table("custom_line_clearance_checklist_details");

        (template.line_clearance_template_details || []).forEach(template_row => {
            let child = frm.add_child("custom_line_clearance_checklist_details");
            child.line_clearance_checklist = template_row.line_clearance_checklist;
        });

        frm.refresh_field("custom_line_clearance_checklist_details");
        // FIX: This was the bug - was setting feasibility instead of line clearance
        frm._last_line_clearance_operation = frm.doc.operation;

        if ((frm.doc.custom_line_clearance_checklist_details || []).length > 0) {
            frm.set_df_property("custom_line_clearance_checklist_details", "hidden", 0);
        }
    }).catch(err => {
        console.error("Error loading line clearance template:", err);
    });
}

function load_bom_operation_details(frm) {
    const software_operations = [
        "MISSO Robotic Execution Software-Arm Cart",
        "MISSO Robotic Execution Software",
        "MISSO Planning Software"
    ];

    if (software_operations.includes(frm.doc.operation)) {
        frm.clear_table("custom_jobcard_opeartion_deatils");
        frm.refresh_field("custom_jobcard_opeartion_deatils");
        frm.set_df_property("custom_jobcard_opeartion_deatils", "hidden", 1);
        
        frm._last_bom_operation = frm.doc.operation;
        frm._last_bom_no = frm.doc.bom_no;
        
        return Promise.resolve();
    }

    if (!frm.doc.bom_no) {
        return Promise.resolve();
    }

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

        let has_rows = (frm.doc.custom_jobcard_opeartion_deatils || []).length > 0;
        frm.set_df_property("custom_jobcard_opeartion_deatils", "hidden", has_rows ? 0 : 1);

        frm._last_bom_operation = frm.doc.operation;
        frm._last_bom_no = frm.doc.bom_no;
    }).catch(err => {
        console.error("Error loading BOM details:", err);
        frm._last_bom_operation = frm.doc.operation;
        frm._last_bom_no = frm.doc.bom_no;
        return Promise.resolve();
    });
}

function toggle_custom_tab(frm) {
    let has_rows = (frm.doc.custom_jobcard_opeartion_deatils || []).length > 0;
    
    frm.set_df_property("custom_opeartions_list", "hidden", !has_rows);
    frm.set_df_property("custom_jobcard_opeartion_deatils", "hidden", !has_rows);

    frm.refresh_fields();
}

function toggle_lineclearance_tab(frm) {
    let has_rows = (frm.doc.custom_line_clearance_checklist_details || []).length > 0;
    
    frm.set_df_property("custom_line_clearance_checklist_details", "hidden", !has_rows);
    frm.set_df_property("custom_line_clearance", "hidden", !has_rows);

    frm.refresh_fields();
}

function toggle_feasibility_tab(frm) {
    let has_rows = (frm.doc.custom_feasibility_testing || []).length > 0;
    
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

        // Only update if different to avoid triggering events
        if (frm.doc.custom_software !== frm.doc.operation) {
            frm.doc.custom_software = frm.doc.operation;
            frm.refresh_field("custom_software");
        }
        
        frm.clear_table("custom_jobcard_opeartion_deatils");
        frm.refresh_field("custom_jobcard_opeartion_deatils");
        frm.set_df_property("custom_jobcard_opeartion_deatils", "hidden", 1);

    } else {
        frm.set_df_property("custom_software", "hidden", 1);
        frm.set_df_property("custom_version", "hidden", 1);
        frm.set_df_property("custom_installed", "hidden", 1);
    }

    frm.refresh_fields();
}

function hide_tabs_and_tables_if_templates_empty(frm) {
    if (!frm.doc.custom_feasibility_testing_template) {
        frm.set_df_property("custom_feasibility_test", "hidden", 1);
        frm.set_df_property("custom_feasibility_testing", "hidden", 1);
    }
    
    if (!frm.doc.custom_line_clearance_template) {
        frm.set_df_property("custom_line_clearance", "hidden", 1);
        frm.set_df_property("custom_line_clearance_checklist_details", "hidden", 1);
    }
    frm.refresh_fields();
}
