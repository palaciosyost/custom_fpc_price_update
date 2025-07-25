from odoo import api, fields, models, _
from odoo.exceptions import UserError

class TipoEntrega(models.Model):
    _name = 'medida.tiempo'
    _description = "Tipo de medida ( entreha )"

    name = fields.Char(string="Nombre")

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    tipo_entrega = fields.Many2one("medida.tiempo", string="Tipo de entrega")
    price_unit_manual = fields.Boolean(
        string="Precio Modificado Manualmente",
        default=False,
        help="Indica si el precio unitario fue modificado manualmente para no recalcularlo automáticamente."
    )

    @api.depends('product_id', 'product_uom', 'product_uom_qty')
    def _compute_price_unit(self):
        for line in self:
            # 🚫 No recalcular si fue modificado manualmente
            if line.price_unit_manual:
                continue

            if line.qty_invoiced > 0 or (line.product_id.expense_policy == 'cost' and line.is_expense):
                continue

            if not line.product_uom or not line.product_id:
                line.price_unit = 0.0
            else:
                line = line.with_company(line.company_id)
                price = line._get_display_price()
                line.price_unit = line.product_id._get_tax_included_unit_price_from_price(
                    price,
                    line.currency_id or line.order_id.currency_id,
                    product_taxes=line.product_id.taxes_id.filtered(
                        lambda tax: tax.company_id == line.env.company
                    ),
                    fiscal_position=line.order_id.fiscal_position_id,
                )

    @api.onchange('price_unit')
    def _onchange_price_unit(self):
        for line in self:
            # ✅ Marca como modificado si el precio se cambia manualmente
            if line.price_unit:
                line.price_unit_manual = True

    @api.onchange('product_id', 'product_uom')
    def _reset_price_manual_flag(self):
        # 🔁 Si se cambia el producto o la unidad, se permite recalcular nuevamente
        self.price_unit_manual = False
