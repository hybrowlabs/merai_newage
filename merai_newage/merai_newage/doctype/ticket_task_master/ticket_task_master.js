frappe.ui.form.on("Ticket Task Master", {
    refresh(frm) {
        frm._previous_workflow_state = frm.doc.workflow_state;
        clear_highlight(frm, "remarks");
    },

    after_workflow_action: function(frm) {
        clear_highlight(frm, "remarks");

        if (frm.doc.workflow_state === "Approved") {
            frappe.call({
                method: "merai_newage.merai_newage.doctype.ticket_task_master.ticket_task_master.update_ticket_master",
                args: {
                    reference_name: frm.doc.ticket_master_reference || null,
                    task_doc: frm.doc,
                    previous_state: frm._previous_workflow_state
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.show_alert({
                            message: __('Ticket Master updated successfully'),
                            indicator: 'green'
                        });
                        setTimeout(() => frm.reload_doc(), 1000);
                    }
                }
            });
        }
    },

    remarks: function(frm) {
        if (frm.doc.remarks) {
            clear_highlight(frm, "remarks");
        }
    }
});

// Listen for server validation error and highlight remarks
$(document).ajaxError(function(event, xhr) {
    try {
        const res = JSON.parse(xhr.responseText);
        const messages = res._server_messages || res.exc || "";
        if (messages && messages.toLowerCase().includes("remarks")) {
            const frm = cur_frm;
            if (frm && frm.doctype === "Ticket Task Master") {
                highlight_field(frm, "remarks");
            }
        }
    } catch(e) {}
});

function highlight_field(frm, fieldname) {
    const fieldWrapper = frm.fields_dict[fieldname]?.$wrapper;
    if (!fieldWrapper) return;

    [
        fieldWrapper.find(".form-control"),
        fieldWrapper.find(".ql-editor"),
        fieldWrapper.find(".ql-container"),
        fieldWrapper.find(".input-with-feedback"),
    ].forEach(el => {
        if (el.length) {
            el.css({
                "border": "2px solid #e74c3c",
                "background-color": "#fff5f5",
                "box-shadow": "0 0 0 3px rgba(231, 76, 60, 0.2)",
                "border-radius": "4px"
            });
        }
    });

    fieldWrapper.find(".frappe-control").css({
        "border": "2px solid #e74c3c",
        "border-radius": "6px",
        "padding": "4px",
        "background-color": "#fff5f5"
    });

    fieldWrapper.find("label").css({ "color": "#e74c3c", "font-weight": "600" });
    fieldWrapper[0]?.scrollIntoView({ behavior: "smooth", block: "center" });

    const focusTarget = fieldWrapper.find(".ql-editor, .form-control, input, textarea").first();
    focusTarget.focus();

    focusTarget.one("keydown input", function() {
        clear_highlight(frm, fieldname);
    });
}

function clear_highlight(frm, fieldname) {
    const fieldWrapper = frm.fields_dict[fieldname]?.$wrapper;
    if (!fieldWrapper) return;

    fieldWrapper.find(".form-control, .ql-editor, .ql-container, .input-with-feedback").css({
        "border": "", "background-color": "", "box-shadow": "", "border-radius": ""
    });
    fieldWrapper.find(".frappe-control").css({
        "border": "", "border-radius": "", "padding": "", "background-color": ""
    });
    fieldWrapper.find("label").css({ "color": "", "font-weight": "" });
}