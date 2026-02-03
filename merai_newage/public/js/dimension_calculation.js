
console.log("Dimension Calculation JS Loaded");

function calculation_box_and_gross_weight(frm, cdt, cdn) {
  const row = locals[cdt][cdn];
  if (!row) return;

  const box = flt(row.box || 0);
  const weight = flt(row.weight || 0); // manual input

  const gross = flt(box * weight, 3);
  frappe.model.set_value(cdt, cdn, "gross_weight", gross);
}

function dimension_calculation(frm, cdt, cdn) {
  const row = locals[cdt][cdn];
  if (!row) return;

  const length = flt(row.length || 0);
  const width = flt(row.width || 0);
  const height = flt(row.height || 0);
  const gross_weight = flt(row.gross_weight || 0);
  const type_wise_value = flt(frm.doc.type_wise_value || 1);

  const volume =
    (length * width * height * gross_weight) / type_wise_value;

  frappe.model.set_value(
    cdt,
    cdn,
    "custom_volume_metric_weight_cm",
    flt(volume, 3)
  );

  // Parent total
  let total = 0;
  (frm.doc.dimension_calculation || []).forEach((d) => {
    total += flt(d.custom_volume_metric_weight_cm || 0);
  });

  frm.set_value("chargeable_weight", flt(total, 3));
}

frappe.ui.form.on("Dimension Calculation", {
  length(frm, cdt, cdn) {
    dimension_calculation(frm, cdt, cdn);
  },
  width(frm, cdt, cdn) {
    dimension_calculation(frm, cdt, cdn);
  },
  height(frm, cdt, cdn) {
    dimension_calculation(frm, cdt, cdn);
  },
  gross_weight(frm, cdt, cdn) {
    dimension_calculation(frm, cdt, cdn);
  },
  box(frm, cdt, cdn) {
    calculation_box_and_gross_weight(frm, cdt, cdn);
    dimension_calculation(frm, cdt, cdn);
  },
  weight(frm, cdt, cdn) {
    calculation_box_and_gross_weight(frm, cdt, cdn);
    dimension_calculation(frm, cdt, cdn);
  }
});
