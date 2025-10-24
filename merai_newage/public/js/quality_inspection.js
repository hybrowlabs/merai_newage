frappe.ui.form.on("Quality Inspection", {
    refresh: function(frm) {
        handle_software_fields(frm);
        if (frm.doc.custom_qi_print_format) {
            let print_format = frm.doc.custom_qi_print_format;
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
    },

    after_save: function(frm) {
        handle_software_fields(frm);
    }
});

function handle_software_fields(frm) {
    if (!frm.doc.reference_name) return;  

    frappe.db.get_value("Job Card", frm.doc.reference_name, "operation", function(r) {
        if (!r || !r.operation) return;

        const jobcard_operation = r.operation;
        const software_operations = [
            "MISSO Robotic Execution Software-Arm Cart",
            "MISSO Robotic Execution Software",
            "MISSO Planning Software"
        ];
        console.log("jobcard_operation=====",jobcard_operation)
        if (software_operations.includes(jobcard_operation)) {
            console.log("====25")
            frm.set_df_property("custom_software", "hidden", 0);
            frm.set_df_property("custom_verified", "hidden", 0);
            frm.set_df_property("custom_remarks", "hidden", 0);

            frm.set_value("custom_software", jobcard_operation);

            // Hide child table
            frm.clear_table("custom_qc_items");
            frm.refresh_field("custom_qc_items");
            frm.set_df_property("custom_qc_items", "hidden", 1);

        } else {
            // Hide software fields
            console.log("38===")
            frm.set_df_property("custom_software", "hidden", 1);
            frm.set_df_property("custom_verified", "hidden", 1);
            frm.set_df_property("custom_remarks", "hidden", 1);

            // Show child table
            frm.set_df_property("custom_qc_items", "hidden", 0);
        }

        frm.refresh_fields();
    });
}
