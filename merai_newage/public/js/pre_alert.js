frappe.ui.form.on('Pre-Alert Item Details', {
    igcr: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        if (row.igcr) {
            frappe.model.set_value(cdt, cdn, 'category', '9');
            frm.fields_dict.item_details.grid.toggle_enable('category', false);
        } else {
            frappe.model.set_value(cdt, cdn, 'category', null);
            frm.fields_dict.item_details.grid.toggle_enable('category', true);
        }
    }
});
