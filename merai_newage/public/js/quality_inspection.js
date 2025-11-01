frappe.ui.form.on("Quality Inspection", {
    refresh: function(frm) {
        handle_software_fields(frm);
       
    },
// before_save: function(frm) {
//   frappe.call({
//     method: "merai_newage.overrides.quality_inspection.get_employee_by_user",
//     args: {
//       user: frappe.session.user
//     },
//     callback: function(r) {
//       if (r.message) {
//         console.log("Employee:", r.message);
//       }
//     }
//   });
// },
   

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
