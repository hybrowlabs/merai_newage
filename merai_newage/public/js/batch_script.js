frappe.ui.form.on("Batch", {
    onload(frm) {
        setCodes(frm);
    },
    refresh(frm) {
        // console.log("-----------------")
        setCodes(frm);
    },
    manufacturing_date(frm) {
        setCodes(frm);
    },
    validate(frm) {
        setCodes(frm);
    }
});

function setCodes(frm) {
    const d = frm.doc.manufacturing_date;
    if (!d) {
        frm.set_value("custom_year", "");
        frm.set_value("custom_month_code", "");
        return;
    }

    // Use Frappe datetime util (safe for yyyy-mm-dd strings)
    const dt = frappe.datetime.str_to_obj(d);
    if (!dt) {
        frm.set_value("custom_year", "");
        frm.set_value("custom_month_code", "");
        return;
    }

    // Year (yy)
    const yy = String(dt.getFullYear() % 100).padStart(2, "0");
    frm.set_value("custom_year", yy);

    // Month → Letter code
    const letters = "ABCDEFGHIJKL"; // Jan = A … Dec = L
    const code = letters[dt.getMonth()] || "";
    frm.set_value("custom_month_code", code);
}
