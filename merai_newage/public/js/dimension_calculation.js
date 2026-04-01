function calculation_box_and_gross_weight(frm, cdt, cdn) {

    const row = frappe.get_doc(cdt, cdn);
    if (!row) return;

    const box = flt(row.box);
    const weight = flt(row.weight);

    const gross_weight = flt(box * weight, 3);

    frappe.model.set_value(cdt, cdn, "gross_weight", gross_weight);
}

/**
 * Calculate Volume Metric Weight for Row
 * And Update Parent Chargeable Weight
 */
function calculate_dimension_row(frm, cdt, cdn) {

    const row = frappe.get_doc(cdt, cdn);
    if (!row) return;

    const length = flt(row.length);
    const width = flt(row.width);
    const height = flt(row.height);
    const gross_weight = flt(row.gross_weight);
    const type_wise_value = flt(frm.doc.type_wise_value) || 1;

    // Volume Metric Weight (fix formula if needed later)
    const volume =
        (length * width * height) / type_wise_value;

    frappe.model.set_value(
        cdt,
        cdn,
        "custom_volume_metric_weight_cm",
        flt(volume, 3)
    );

    // Calculate totals
    let total_volume = 0;
    let total_gross = 0;

    (frm.doc.dimension_calculation || []).forEach(d => {
        total_volume += flt(d.custom_volume_metric_weight_cm);
        total_gross += flt(d.gross_weight);
    });

    // Set max value
    const chargeable = Math.max(total_volume, total_gross);

    frm.set_value("chargeable_weight", flt(chargeable, 3));
}

/**
 * Child Table Events
 */
frappe.ui.form.on("Dimension Calculation", {

    length(frm, cdt, cdn) {
        calculate_dimension_row(frm, cdt, cdn);
    },

    width(frm, cdt, cdn) {
        calculate_dimension_row(frm, cdt, cdn);
    },

    height(frm, cdt, cdn) {
        calculate_dimension_row(frm, cdt, cdn);
    },

    gross_weight(frm, cdt, cdn) {
        calculate_dimension_row(frm, cdt, cdn);
    },

    box(frm, cdt, cdn) {
        calculation_box_and_gross_weight(frm, cdt, cdn);
        calculate_dimension_row(frm, cdt, cdn);
    },

    weight(frm, cdt, cdn) {
        calculation_box_and_gross_weight(frm, cdt, cdn);
        calculate_dimension_row(frm, cdt, cdn);
    }

});
