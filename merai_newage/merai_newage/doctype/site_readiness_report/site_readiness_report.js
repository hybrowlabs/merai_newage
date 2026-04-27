// Copyright (c) 2026, Siddhant Hybrowlabs and contributors
// For license information, please see license.txt


frappe.ui.form.on("Site Readiness Report", {
    refresh: function(frm) {
        if (frm.is_new() && !frm.__defaults_loaded) {
            frappe.call({
                method: "merai_newage.merai_newage.doctype.site_readiness_report.site_readiness_report.get_default_rows",
                args: {
                    doc: frm.doc
                },
                callback: function(r) {
                    if (r.message) {

                        // clear existing (important)
                        frm.clear_table("power_testing");
                        frm.clear_table("pre_installation_table");
                        frm.clear_table("sawbone_testing");
                        frm.clear_table("closure_activity");

                        // populate child tables manually
                        let data = r.message;

                        ["power_testing", "pre_installation_table", "sawbone_testing", "closure_activity"]
                        .forEach(field => {
                            (data[field] || []).forEach(row => {
                                let child = frm.add_child(field);
                                Object.assign(child, row);
                            });
                        });

                        frm.refresh_fields();
                        frm.__defaults_loaded = true;
                    }
                }
            });
        }
    }
});