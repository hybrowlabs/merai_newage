window.get_item_options = function(frm) {
    let options = [];

    (frm.doc.item_details || []).forEach(item => {
        options.push({
            label: `${item.idx || ""} - ${item.item_code || ""} - ${item.description || ""}`,
            value: item.name
        });
    });

    return options;
};

window.get_item_by_row_name = function(frm, row_name) {
    return (frm.doc.item_details || []).find(item => item.name === row_name);
};

window.process_rodtep_selections = async function(frm, selections) {
    for (const script_name of selections) {
        await window.assign_single_rodtep_to_item(frm, script_name);
    }

    frm.refresh_field("rodtep_details");

    window.calculation_of_rodtep(frm);
    window.calculation_used_rodtep(frm);
    window.calculation_tax(frm);
    window.total_calculations(frm);
};

window.assign_single_rodtep_to_item = function(frm, script_name) {
    return new Promise((resolve) => {

        frappe.call({
            method: "frappe.client.get",
            args: {
                doctype: "Rodtep Utilization",
                name: script_name
            },
            callback: function(r) {

                if (!r.message) {
                    resolve();
                    return;
                }

                let script = r.message;

                //Build dropdown options (user-friendly)
                let options = (frm.doc.item_details || []).map(item => {
                    return `${item.item_code} (${item.description || ""})::${item.name}`;
                });

                if (!options.length) {
                    frappe.msgprint("Please add item details first.");
                    resolve();
                    return;
                }

                frappe.prompt(
                    [
                        {
                            fieldname: "selected_item_row",
                            label: "Select Item",
                            fieldtype: "Select",
                            options: options.join("\n"),
                            reqd: 1
                        },
                        {
                            fieldname: "assigned_amount",
                            label: "Assigned Amount",
                            fieldtype: "Currency",
                            default: script.remaining_amount || 0,
                            reqd: 1
                        }
                    ],
                    function(values) {

                        let selected_value = values.selected_item_row;

                        //Split value
                        let item_code = selected_value.split("::")[0].split(" ")[0];
                        let row_name = selected_value.split("::")[1];

                        let selected_item = frm.doc.item_details.find(
                            d => d.name === row_name
                        );

                        if (!selected_item) {
                            frappe.msgprint("Selected item not found.");
                            resolve();
                            return;
                        }

                        let remaining_amount = flt(script.remaining_amount);
                        let assigned_amount = flt(values.assigned_amount);

                        if (assigned_amount <= 0) {
                            frappe.msgprint("Assigned Amount must be greater than 0.");
                            resolve();
                            return;
                        }

                        if (assigned_amount > remaining_amount) {
                            frappe.msgprint(
                                `Assigned Amount cannot be greater than remaining amount (${remaining_amount}).`
                            );
                            resolve();
                            return;
                        }

                        //Build dropdown options (user-friendly)
                        let row = frm.add_child("rodtep_details");

                        row.script_no = script.name;
                        row.amount = remaining_amount;
                        row.script_date = script.script_date;

                        // ✔ store correctly
                        row.custom_selected_item_row = row_name;
                        row.custom_selected_item_code = item_code;

                        row.custom_assigned_total_amount = assigned_amount;
                        row.used_rodtep = 0;
                        row.custom_balance_amount = assigned_amount;

                        frm.refresh_field("rodtep_details");

                        resolve();
                    },
                    "Assign RODTEP To Item",
                    "Add"
                );
            }
        });

    });
};

window.validate_rodtep_assignments = function(frm) {
    let script_wise_total = {};

    (frm.doc.rodtep_details || []).forEach(r => {
        if (!r.script_no) return;

        if (!script_wise_total[r.script_no]) {
            script_wise_total[r.script_no] = {
                original_amount: flt(r.amount || 0),
                assigned_total: 0
            };
        }

        script_wise_total[r.script_no].assigned_total += flt(r.custom_assigned_total_amount || 0);
    });

    Object.keys(script_wise_total).forEach(script_no => {
        let row = script_wise_total[script_no];

        if (row.assigned_total > row.original_amount) {
            frappe.throw(
                `Assigned amount for script ${script_no} cannot exceed original amount ${row.original_amount}. Current assigned: ${row.assigned_total}`
            );
        }
    });
};