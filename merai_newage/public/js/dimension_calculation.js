// Dimension Calculation
function calculate_dimension_row(frm, cdt, cdn) {

    const row = frappe.get_doc(cdt, cdn);
    if (!row) return;

    const length = flt(row.length) || 0;
    const width = flt(row.width) || 0;
    const height = flt(row.height) || 0;
    const box = flt(row.box) || 1;
    const gross_weight = flt(row.gross_weight) || 0;

    const shipment_mode = frm.doc.mode_of_shipment;

    // Divisor based on shipment mode
    let divisor = 6000;

    if (shipment_mode === "Air") {
        divisor = 6000;
    } 
    else if (shipment_mode === "Ship") {
        divisor = 1000000;
    } 
    else if (shipment_mode === "Courier") {
        divisor = 5000;
    }

    // Volume calculation
    let volume = 0;

    if (length && width && height) {
        volume = (length * width * height * box) / divisor;
    }

    frappe.model.set_value(
        cdt,
        cdn,
        "custom_volume_metric_weight_cm",
        flt(volume, 3)
    );

    // Total calculation
    let total_volume = 0;
    let total_gross = 0;

    (frm.doc.dimension_calculation || []).forEach(d => {
        total_volume += flt(d.custom_volume_metric_weight_cm);
        total_gross += flt(d.gross_weight);
    });

    // Final chargeable logic
    let final_value = 0;

    if (shipment_mode === "Sea") {
        final_value = total_volume;
    } else {
        final_value = Math.max(total_volume, total_gross);
    }

    frm.set_value("chargeable_weight", flt(final_value, 3));
}


// Child Table Events
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

    box(frm, cdt, cdn) {
        calculate_dimension_row(frm, cdt, cdn);
    },

    gross_weight(frm, cdt, cdn) {
        calculate_dimension_row(frm, cdt, cdn);
    }

});


// Parent Trigger
frappe.ui.form.on("Pickup Request", {

    mode_of_shipment(frm) {
        (frm.doc.dimension_calculation || []).forEach(d => {
            calculate_dimension_row(frm, d.doctype, d.name);
        });
    }

});