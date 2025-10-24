

frappe.ui.form.on("Job Card", {
    refresh: function (frm) {

        if (frm.doc.custom_print_format) {
            let print_format = frm.doc.custom_print_format;
            frm.meta.default_print_format = print_format;

            frm.page.print_doc = () => {
                frappe.ui.get_print_settings(false, (print_settings) => {
                    frappe.print_doc({
                        doctype: frm.doc.doctype,
                        name: frm.doc.name,
                        print_format: print_format,   
                        letterhead: print_settings.letterhead,
                        lang: print_settings.lang,
                        always_print: print_settings.always_print
                    });
                });
            };
        }
         setTimeout(() => 
          set_batch_query(frm),1000);
        // Prevent multiple refresh calls in short time
        if (frm._refresh_in_progress) return;
        frm._refresh_in_progress = true;
        setTimeout(() => frm._refresh_in_progress = false, 1000);

        if (!frm.doc.operation || !frm.doc.work_order) return;
        
        // Quality Inspection button
        if(frm.doc.docstatus != 1 && !frm.doc.quality_inspection) {
            frappe.db.get_value("Operation", frm.doc.operation, "custom_quality_inspection_required")
                .then(r => {
                    if (r.message && r.message.custom_quality_inspection_required) {
                        frm.add_custom_button(__('Create QI'), function () {
                            create_quality_inspection(frm);
                        });
                    }
                });
        }
        
        // Load templates only for new documents
        if ((frm.is_new() || frm.doc.__islocal) && frm.doc.docstatus != 1) {
            load_templates_for_new_doc(frm);
        }
        
        // Handle software fields
        if (frm.is_new() || frm.doc.__islocal || !frm._software_fields_initialized) {
            setTimeout(() => {
                handle_software_fields(frm);
                frm._software_fields_initialized = true;
            }, 500);
        }
        
        // Load form data and manage visibility
        load_form_data(frm);
        
        // Single call to manage all tab visibility
        setTimeout(() => {
            // display_fields_in_ops(frm)
            manage_tab_visibility(frm);
        }, 1000);
    },
    before_save: function(frm) {
        frappe.call({
            method: "merai_newage.overrides.job_card.get_employee_by_user",
            callback: function(r) {
                if (r.message) {
                    console.log("r---",r)
                    frm.doc.custom_signed_by = r.message; 
                    frm.refresh_field('custom_signed_by');
                }
            }
        });
    },
onload: function(frm) {

        

        setTimeout(() => {
            manage_tab_visibility(frm);
        }, 1000);

         if (frm.is_new() || frm.doc.__islocal || !frm._software_fields_initialized) {
            setTimeout(() => {
                handle_software_fields(frm);
                frm._software_fields_initialized = true;
            }, 500);
        }
    },
    operation: function(frm) {
        if (frm._refresh_in_progress) return;
        
        if (frm.doc.operation) {
            reset_operation_cache(frm);
            
            clearTimeout(frm._operation_timeout);
            frm._operation_timeout = setTimeout(() => {
                load_form_data(frm);
                handle_software_fields(frm);
                manage_tab_visibility(frm);
                frm._software_fields_initialized = true;
            }, 300);
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
                        manage_tab_visibility(frm);
                    });
                }
            }, 300);
        }
    },

    production_item: function(frm) {
        if (frm._refresh_in_progress) return;
        
        if (frm.doc.production_item) {
            frm._last_feasibility_operation = null;
            
            clearTimeout(frm._item_timeout);
            frm._item_timeout = setTimeout(() => {
                load_feasibility_testing_template(frm).then(() => {
                    manage_tab_visibility(frm);
                });
            }, 300);
        } else {
            frm.clear_table("custom_feasibility_testing");
            frm.doc.custom_feasibility_testing_template = "";
            frm.refresh_field("custom_feasibility_testing_template");
            frm.refresh_field("custom_feasibility_testing");
            manage_tab_visibility(frm);
        }
    },

    custom_feasibility_testing_template: function(frm) {
        if (frm._loading_feasibility_template || frm._refresh_in_progress) return;
        
        if (frm.doc.custom_feasibility_testing_template) {
            frm._loading_feasibility_template = true;
            load_feasibility_testing_from_template(frm, frm.doc.custom_feasibility_testing_template).then(() => {
                frm._loading_feasibility_template = false;
                manage_tab_visibility(frm);
            }).catch(() => {
                frm._loading_feasibility_template = false;
            });
        } else {
            frm.clear_table("custom_feasibility_testing");
            frm.refresh_field("custom_feasibility_testing");
            manage_tab_visibility(frm);
        }
    },
    
    custom_line_clearance_template: function(frm) {
        if (frm._loading_line_clearance_template || frm._refresh_in_progress) return;
        
        if (frm.doc.custom_line_clearance_template) {
            frm._loading_line_clearance_template = true;
            load_line_clearnce_from_template(frm, frm.doc.custom_line_clearance_template).then(() => {
                frm._loading_line_clearance_template = false;
                manage_tab_visibility(frm);
            }).catch(() => {
                frm._loading_line_clearance_template = false;
            });
        } else {
            frm.clear_table("custom_line_clearance_checklist_details");
            frm.refresh_field("custom_line_clearance_checklist_details");
            manage_tab_visibility(frm);
        }
    }
});

// Centralized function to manage all tab visibility
function manage_tab_visibility(frm) {
   
    
    // const is_draft = frm.doc.workflow_state === "Draft";
    const is_software_operation = frm.doc.custom_software_reqd
    const has_feasibility_data = (frm.doc.custom_feasibility_testing || []).length > 0;
    console.log("has_feasibility_data---------160",has_feasibility_data)
    const has_line_clearance_data = (frm.doc.custom_line_clearance_checklist_details || []).length > 0;
    const has_operation_details = (frm.doc.custom_jobcard_opeartion_deatils || []).length > 0;
    
    // Check if templates exist
    const has_feasibility_template = frm.doc.custom_feasibility_testing_template;
    const has_line_clearance_template = frm.doc.custom_line_clearance_template;

    // Feasibility Testing - Hide if: No template OR (Draft state AND has template)
    // Show only if: Has template AND NOT draft state
    const hide_feasibility = !has_feasibility_template
    frm.set_df_property("custom_feasibility_testing", "hidden", hide_feasibility ? 1 : 0);
    frm.set_df_property("custom_feasibility_test", "hidden", hide_feasibility || !has_feasibility_data ? 1 : 0);

    // Operations List - Hide if: software operation OR draft state OR no operation details
    frm.set_df_property("custom_opeartions_list", "hidden", (is_software_operation ||  !has_operation_details) ? 1 : 0);
    frm.set_df_property("custom_jobcard_opeartion_deatils", "hidden", (is_software_operation || !has_operation_details) ? 1 : 0);

    // Line Clearance - Hide if: No template OR no data
    // Show only if: Has template AND has data
    const hide_line_clearance = !has_line_clearance_template || !has_line_clearance_data;
    frm.set_df_property("custom_line_clearance_checklist_details", "hidden", hide_line_clearance ? 1 : 0);
    frm.set_df_property("custom_line_clearance", "hidden", hide_line_clearance ? 1 : 0);

    frm.refresh_fields();
}

function reset_operation_cache(frm) {
    frm._last_line_clearance_operation = null;
    frm._last_feasibility_operation = null;
    frm._last_bom_operation = null;
    frm._software_fields_initialized = null;
}

function load_templates_for_new_doc(frm) {
    if (!frm.doc.custom_feasibility_testing_template) {
        load_feasibility_testing_template(frm);
    }
    if (!frm.doc.custom_line_clearance_template) {
        load_line_clearance_template(frm);
    }
}

function create_quality_inspection(frm) {
   
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
        qi.manual_inspection = 1;
        qi.custom_qi_print_format = frm.doc.custom_qi_print_format

        if (frm.doc.custom_software_reqd) {
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
    if (frm.doc.docstatus == 1) return;
    
    let promises = [];

    // Load templates only if tables are empty or it's a new document
    if (frm.doc.__islocal || !(frm.doc.custom_line_clearance_checklist_details && frm.doc.custom_line_clearance_checklist_details.length > 0)) {
        promises.push(load_line_clearance_template(frm));
    }
    if (frm.doc.__islocal || !(frm.doc.custom_feasibility_testing && frm.doc.custom_feasibility_testing.length > 0)) {
        promises.push(load_feasibility_testing_template(frm));
    }
    if (frm.doc.__islocal || !(frm.doc.custom_jobcard_opeartion_deatils && frm.doc.custom_jobcard_opeartion_deatils.length > 0)) {
        promises.push(load_bom_operation_details(frm));
    }

    Promise.all(promises).then(() => {
        setTimeout(() => {
            manage_tab_visibility(frm);
        }, 500);
    });
}

function should_load_bom_details(frm) {
    return frm.doc.bom_no && frm.doc.operation && 
           (!frm.doc.custom_jobcard_opeartion_deatils || 
            frm.doc.custom_jobcard_opeartion_deatils.length === 0 ||
            frm._last_bom_operation !== frm.doc.operation ||
            frm._last_bom_no !== frm.doc.bom_no);
}

function load_feasibility_testing_template(frm) {
    if (frm._loading_feasibility_template || !frm.doc.production_item) {
        return Promise.resolve();
    }
    
    frm._loading_feasibility_template = true;
    
    return frappe.db.get_doc("Operation", frm.doc.operation).then(operation_doc => {
        let template_name = operation_doc.custom_feasibility_testing_template || "";
        
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
    }).catch(err => {
        console.error("Error loading feasibility testing template:", err);
    });
}

function load_line_clearance_template(frm) {
    if (frm._loading_line_clearance_template) {
        return Promise.resolve();
    }
    
    frm._loading_line_clearance_template = true;
    
    return frappe.db.get_doc("Operation", frm.doc.operation).then(operation_doc => {
        let template_name = operation_doc.custom_line_clearance_template || "";
    
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

        return load_line_clearnce_from_template(frm, template_name, operation_doc).then(() => {
            frm._loading_line_clearance_template = false;
        });
    }).catch(err => {
        frm._loading_line_clearance_template = false;
        console.error("Error in load_line_clearance_template:", err);
        return Promise.resolve();
    });
}

function load_line_clearnce_from_template(frm, template_name, operation_doc = null) {
    return frappe.db.get_doc("Line Clearance Template", template_name).then(template => {
        frm.clear_table("custom_line_clearance_checklist_details");

        (template.line_clearance_template_details || []).forEach(template_row => {
            let child = frm.add_child("custom_line_clearance_checklist_details");
            child.line_clearance_checklist = template_row.line_clearance_checklist;
        });

        frm.refresh_field("custom_line_clearance_checklist_details");
        frm._last_line_clearance_operation = frm.doc.operation;
    }).catch(err => {
        console.error("Error loading line clearance template:", err);
    });
}

function load_bom_operation_details(frm) {
    

    if (frm.doc.custom_software_reqd) {
        frm.clear_table("custom_jobcard_opeartion_deatils");
        frm.refresh_field("custom_jobcard_opeartion_deatils");
        
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
        frm._last_bom_operation = frm.doc.operation;
        frm._last_bom_no = frm.doc.bom_no;
    }).catch(err => {
        console.error("Error loading BOM details:", err);
        frm._last_bom_operation = frm.doc.operation;
        frm._last_bom_no = frm.doc.bom_no;
        return Promise.resolve();
    });
}

function handle_software_fields(frm) {


    if (frm.doc.custom_software_reqd) {
        frm.set_df_property("custom_software", "hidden", 0);
        frm.set_df_property("custom_version", "hidden", 0);
        frm.set_df_property("custom_installed", "hidden", 0);
        

        if (!frm.doc.custom_software) {
            frm.set_value("custom_software", frm.doc.operation);
        }
        // if (frm.doc.custom_software !== frm.doc.operation) {
        //     frm.doc.custom_software = frm.doc.operation;
        //     frm.refresh_field("custom_software");
        // }
        
        frm.clear_table("custom_jobcard_opeartion_deatils");
        frm.refresh_field("custom_jobcard_opeartion_deatils");
    } else {
        frm.set_df_property("custom_software", "hidden", 1);
        frm.set_df_property("custom_version", "hidden", 1);
        frm.set_df_property("custom_installed", "hidden", 1);
    }

    frm.refresh_fields();
}






frappe.ui.form.on("Job Card", {
    refresh: function(frm) {
        // Wait for default ERPNext buttons to load
        setTimeout(() => {
            control_default_button_visibility(frm);
        }, 1000);
    },
    
    after_save: function(frm) {
        setTimeout(() => {
            control_default_button_visibility(frm);
        }, 300);
    }
});

function control_default_button_visibility(frm) {
    // Find ANY button with "Complete Job" text (default ERPNext button)
    let buttons_found = 0;
    
    // Search in the entire document for Complete Job buttons
    $(document).find('button, .btn, a').each(function() {
        let $this = $(this);
        let text = $this.text().trim();
        let dataLabel = $this.attr('data-label');
        let onclick = $this.attr('onclick');
        
        // Check if this looks like a Complete Job button
        if (text === "Complete Job" || 
            text.includes("Complete Job") ||
            dataLabel === "Complete%20Job" ||
            (onclick && onclick.includes("Complete"))) {
            
            buttons_found++;
            // console.log("Found Complete Job button:", text, $this.attr('class'));
            
            // Control visibility based on form state
            if (frm.is_dirty() || frm.is_new()) {
                $this.hide();
                // console.log("Hiding default button");
            } else {
                $this.show();
                // console.log("Showing default button");
            }
        }
    });
    
    if (buttons_found === 0) {
        // console.log("=== ALL BUTTONS ON PAGE ===");
        $(document).find('button').each(function(index) {
            // console.log(index + ":", $(this).text().trim(), $(this).attr('class'));
        });

    }
}

// Listen for any form changes
$(document).on('change input keyup', function() {
    if (cur_frm && cur_frm.doctype === "Job Card") {
        setTimeout(() => {
            control_default_button_visibility(cur_frm);
        }, 100);
    }
});

// Alternative: Use MutationObserver to watch for button creation
if (typeof window.job_card_observer === 'undefined') {
    window.job_card_observer = new MutationObserver(function(mutations) {
        if (cur_frm && cur_frm.doctype === "Job Card") {
            mutations.forEach(function(mutation) {
                if (mutation.addedNodes.length > 0) {
                    // Check if any new buttons were added
                    $(mutation.addedNodes).find('button').each(function() {
                        if ($(this).text().includes("Complete Job")) {
                            // console.log("New Complete Job button detected!");
                            setTimeout(() => {
                                control_default_button_visibility(cur_frm);
                            }, 100);
                        }
                    });
                }
            });
        }
    });
    
    // Start observing
    window.job_card_observer.observe(document.body, {
        childList: true,
        subtree: true
    });
}

function set_batch_query(frm) {
    if (frm.fields_dict.custom_jobcard_opeartion_deatils) {
        console.log("570------------------")
        frm.fields_dict.custom_jobcard_opeartion_deatils.grid.get_field("batch_number").get_query = function(doc, cdt, cdn) {
            const child = locals[cdt][cdn];
            
            if (!child.item_code) {
                return;
            }
            
            return {
                filters: {
                    item: child.item_code,  
                    // disabled: 0
                }
            };
        };
    }
}




frappe.ui.form.on("Job Card Opeartion Deatils", {
    batch_number: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        console.log("row---------",row)
        if (row.batch_number) {
            frappe.db.get_value("Batch", row.batch_number, "custom_batch_number")
                .then(r => {
                    if (r.message && r.message.custom_batch_number) {
                        frappe.model.set_value(cdt, cdn, "batch_no_common", r.message.custom_batch_number);
                    } else {
                        frappe.model.set_value(cdt, cdn, "batch_no_common", "");
                    }
                })
                .catch(err => {
                    console.error("Error fetching custom_batch_no:", err);
                    frappe.model.set_value(cdt, cdn, "batch_no_common", "");
                });

            frappe.db.get_value("Work Order",{"custom_batch":row.batch_number} , "name")
                .then(r => {
                    if (r.message && r.message.name) {
                        frappe.model.set_value(cdt, cdn, "work_order_reference", r.message.name);
                    } else {
                        frappe.model.set_value(cdt, cdn, "work_order_reference", "");
                    }
                })
                .catch(err => {
                    console.error("Error fetching custom_batch_no:", err);
                    frappe.model.set_value(cdt, cdn, "work_order_reference", "");
                });


        } else {
            frappe.model.set_value(cdt, cdn, "batch_no_common", "");
        }


        
    }
});
