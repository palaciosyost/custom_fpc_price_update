from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    price_unit_manual = fields.Boolean(
        string="Precio Modificado Manualmente",
        default=False,
        help="Indica si el precio unitario fue modificado manualmente para no recalcularlo automáticamente."
    )

    @api.depends('product_id', 'product_uom', 'date_order', 'partner_id')
    def _compute_price_unit(self):
        for line in self:
            # 🚫 No recalcular si fue modificado manualmente
            if line.price_unit_manual:
                continue

            if not line.product_id or not line.product_uom:
                line.price_unit = 0.0
                continue

            line = line.with_company(line.company_id)
            supplier = line.product_id._select_seller(
                partner_id=line.partner_id,
                quantity=line.product_qty,
                date=line.order_id.date_order and line.order_id.date_order.date(),
                uom_id=line.product_uom
            )

            if supplier:
                price = line.env['account.tax']._fix_tax_included_price_company(
                    supplier.price, supplier.discount_policy == 'with_discount',
                    supplier.tax_id, line.taxes_id, line.company_id
                )
                line.price_unit = line.currency_id._convert(
                    price, line.order_id.currency_id, line.company_id, line.order_id.date_order or fields.Date.today()
                )
            else:
                line.price_unit = 0.0

    @api.onchange('price_unit')
    def _onchange_price_unit_manual(self):
        for line in self:
            if line.price_unit:
                line.price_unit_manual = True

    @api.onchange('product_id', 'product_uom')
    def _reset_manual_flag_on_product_change(self):
        self.price_unit_manual = False
