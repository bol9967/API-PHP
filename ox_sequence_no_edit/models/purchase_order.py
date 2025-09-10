from odoo import models, fields
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    purchase_edit_sequence = fields.Boolean(
        string='Purchase Order Edit Sequence',
        compute='_compute_for_hide_edit_sequence_purchase_'
    )

    def _compute_for_hide_edit_sequence_purchase_(self):
        for rec in self:
            if self.env.user.has_group("ox_sequence_no_edit.purchase_edit_sequence_group"):
                rec.purchase_edit_sequence = False
            else:
                rec.purchase_edit_sequence = True

    def write(self, vals):
        # 🚨 Prevent duplicate sequence numbers
        if 'name' in vals:
            existing = self.search([
                ('id', '!=', self.id),
                ('name', '=', vals['name'])
            ])
            if existing:
                raise ValidationError(
                    f'The {vals['name']} Sequence Number already exists'
                )

        # Keep old names for logging and bill updates
        old_names = {rec.id: rec.name for rec in self}

        res = super(PurchaseOrder, self).write(vals)

        # After write, handle sequence changes
        if 'name' in vals:
            for po in self:
                old_name = old_names.get(po.id)
                if old_name and old_name != po.name:
                    # 1️⃣ Log on Purchase Order
                    po.message_post(
                        body=f"Purchase Order sequence updated "
                             f"from <b>{old_name}</b> to <b>{po.name}</b> "
                             f"by {self.env.user.name}"
                    )

                    # 2️⃣ Update linked Vendor Bills/Refunds
                    moves = self.env['account.move'].search([
                        ('move_type', 'in', ('in_invoice', 'in_refund')),
                        ('invoice_origin', '=', old_name)
                    ])
                    if moves:
                        moves.write({'invoice_origin': po.name})
                        # Log on each bill
                        for move in moves:
                            move.message_post(
                                body=f"Invoice Origin updated from <b>{old_name}</b> "
                                     f"to <b>{po.name}</b> due to Purchase Order sequence change "
                                     f"by {self.env.user.name}"
                            )

        return res
