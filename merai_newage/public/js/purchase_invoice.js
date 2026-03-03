

frappe.ui.form.on("Purchase Invoice", {

    onload(frm) {
        fetch_supplier_invoice_details(frm);
        setup_raise_query_button(frm);
    },

    refresh(frm) {
        setup_raise_query_button(frm);
        setup_resolve_query_button(frm);
    },

    custom_purchase_receipt(frm) {
        fetch_supplier_invoice_details(frm);
    },
    after_workflow_action: function(frm) {
    frappe.call({
        method: "merai_newage.overrides.purchase_invoice.capture_workflow_user",
        args: {
            docname: frm.doc.name,
            workflow_state: frm.doc.workflow_state
        },
        callback: function(r) {
            if (!r.exc) {
                console.log("Workflow user captured:", frm.doc.workflow_state);
                frm.reload_doc();
            }
        }
    });
}
});

function setup_raise_query_button(frm) {
    frm.remove_custom_button('Raise Query');

    const allowed_states = ["Pending From Accountant", "Draft", "Pending From Checker"];
    if (!allowed_states.includes(frm.doc.workflow_state)) return;

    frm.add_custom_button('Raise Query', function () {

        const current_user = frappe.session.user;
        let assigned_to = "";
        let assigned_to_label = "Assign To";

        const maker = frm.doc.custom_approved_by_maker || frm.doc.owner;

        function open_prompt(assigned_to_value, label_text) {

            frappe.prompt([
                {
                    label: 'Raised By',
                    fieldname: 'raised_by',
                    fieldtype: 'Link',
                    options: 'User',
                    default: current_user,
                    read_only: 1,
                    reqd: 1
                },
                {
                    label: label_text,
                    fieldname: 'assigned_to',
                    fieldtype: 'Link',
                    options: 'User',
                    default: assigned_to_value,
                    reqd: 1
                },
                {
                    label: 'Query',
                    fieldname: 'query_text',
                    fieldtype: 'Small Text',
                    reqd: 1
                },
                {
                    label: 'Related Field',
                    fieldname: 'related_field',
                    fieldtype: 'Select',
                    options: [
                        "Supplier Invoice No.",
                        "Supplier Invoice Date",
                        "Cost Center",
                        "Plant",
                        "Due Date",
                        "Items"
                    ],
                    reqd: 1
                }
            ],
            function (values) {
                frappe.call({
                    method: "merai_newage.overrides.purchase_invoice.raise_query",
                    args: {
                        docname: frm.doc.name,
                        query_text: values.query_text,
                        related_field: values.related_field,
                        raised_by: values.raised_by,
                        assigned_to: values.assigned_to
                    },
                    callback: function (r) {
                        if (!r.exc) {
                            frappe.show_alert({
                                message: `Query raised and assigned to ${values.assigned_to}`,
                                indicator: 'green'
                            });
                            frm.reload_doc();
                        }
                    }
                });
            }, 'Raise Query', 'Submit');
        }

        // ✅ Workflow logic
        if (frm.doc.workflow_state === "Pending From Checker") {
            assigned_to = maker;
            assigned_to_label = "Assign To (Maker)";
            open_prompt(assigned_to, assigned_to_label);

        } else if (frm.doc.workflow_state === "Pending From Accountant") {

            assigned_to_label = "Assign To (GRN Creator)";

            frappe.db.get_value(
                "Purchase Receipt",
                frm.doc.custom_purchase_receipt,
                "owner"
            ).then(r => {

                if (r && r.message && r.message.owner) {
                    assigned_to = r.message.owner;
                }

                // 🔥 Open prompt AFTER getting value
                open_prompt(assigned_to, assigned_to_label);
            });

        } else {
            open_prompt("", "Assign To");
        }

    }, __("Actions"));
}
function fetch_supplier_invoice_details(frm) {
    if (!frm.doc.custom_purchase_receipt) return;

    frappe.db.get_value(
        "Purchase Receipt",
        frm.doc.custom_purchase_receipt,
        ["custom_supplier_document_no", "custom_supplier_document_date"]
    ).then(r => {
        if (!r.message) return;

        if (!frm.doc.bill_no && r.message.custom_supplier_document_no) {
            frm.set_value("bill_no", r.message.custom_supplier_document_no);
        }

        if (!frm.doc.bill_date && r.message.custom_supplier_document_date) {
            frm.set_value("bill_date", r.message.custom_supplier_document_date);
        }
    });
}

function setup_resolve_query_button(frm) {

    frm.remove_custom_button("Resolve Query");

    // Show only if current user is Maker
    if (frm.doc.custom_approved_by_maker !== frappe.session.user) return;

    // Show only if there are open queries
    let open_queries = (frm.doc.custom_purchase_invoice_query || [])
        .filter(q => q.status === "Open");
    console.log("open_queries.length",open_queries.length)
    if (!open_queries.length) return;

    frm.add_custom_button("Resolve Query", function () {

        frappe.confirm(
            "Are you sure you want to resolve all open queries?",
            function () {

                frappe.call({
                    method: "merai_newage.overrides.purchase_invoice.resolve_all_queries",
                    args: {
                        docname: frm.doc.name
                    },
                    freeze: true,
                    callback: function (r) {
                        if (!r.exc) {
                            frappe.show_alert({
                                message: "Queries resolved and sent to Checker",
                                indicator: "green"
                            });
                            frm.reload_doc();
                        }
                    }
                });

            }
        );

    }, __("Actions"));
}