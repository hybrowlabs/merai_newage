frappe.ui.form.PrintView = class extends frappe.ui.form.PrintView {
    set_default_print_format() {
        if (this.frm.doc.custom_print_format ) {
            this.print_format_selector.empty();
            this.print_format_selector.val(this.frm.doc.custom_print_format);
        } else {
            if (
                frappe.meta
                    .get_print_formats(this.frm.doctype)
                    .includes(this.print_format_selector.val()) ||
                !this.frm.meta.default_print_format
            )
                return;

            this.print_format_selector.empty();
            this.print_format_selector.val(this.frm.meta.default_print_format);
        }
    }

};
