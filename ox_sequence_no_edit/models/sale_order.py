from odoo import models, fields
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    edit_sequence = fields.Boolean(
        string='Sales Order Edit Sequence',
        compute='_eg_compute_for_edit_sequence'
    )

    def _eg_compute_for_edit_sequence(self):
        for rec in self:
            if self.env.user.has_group("ox_sequence_no_edit.sale_edit_sequence_group"):
                rec.edit_sequence = False
            else:
                rec.edit_sequence = True

    def write(self, vals):
        # 🚨 Prevent duplicate sequence numbers
        if 'name' in vals:
            existing = self.search([
                ('id', '!=', self.id),
                ('name', '=', vals['name'])
            ])
            if existing:
                raise ValidationError(
                    f'The {vals["name"]} Sequence Number already exists'
                )

        # Keep old names for chatter + invoice/picking updates
        old_names = {rec.id: rec.name for rec in self}

        res = super(SaleOrder, self).write(vals)

        # After write, handle sequence changes
        if 'name' in vals:
            for so in self:
                old_name = old_names.get(so.id)
                if old_name and old_name != so.name:
                    # 1️⃣ Log on Sale Order
                    so.message_post(
                        body=f"Sale Order sequence updated from <strong>{old_name}</strong> "
                            f"to <strong>{so.name}</strong> by {self.env.user.name}"
                    )

                    # 2️⃣ Update linked Customer Invoices/Refunds
                    moves = self.env['account.move'].search([
                        ('move_type', 'in', ('out_invoice', 'out_refund')),
                        ('invoice_origin', '=', old_name)
                    ])
                    if moves:
                        moves.write({'invoice_origin': so.name})
                        for move in moves:
                            move.message_post(
                                body=f"Invoice Origin updated from <strong>{old_name}</strong> "
                                    f"to <strong>{so.name}</strong> due to Sale Order sequence change "
                                    f"by {self.env.user.name}"
                            )

                    # 3️⃣ Update linked Stock Pickings
                    pickings = self.env['stock.picking'].search([
                        ('origin', '=', old_name)
                    ])
                    if pickings:
                        pickings.write({'origin': so.name})
                        for picking in pickings:
                            picking.message_post(
                                body=f"Origin updated from <strong>{old_name}</strong> "
                                    f"to <strong>{so.name}</strong> due to Sale Order sequence change "
                                    f"by {self.env.user.name}"
                            )

        return res
