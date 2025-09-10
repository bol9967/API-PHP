from odoo import models, fields
from odoo.exceptions import ValidationError

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    purchase_edit_sequence = fields.Boolean(string='Purchase Order Edit Sequence',
                                            compute='_compute_for_hide_edit_sequence_purchase_')

    def _compute_for_hide_edit_sequence_purchase_(self):
        for rec in self:
            if self.env.user.has_group("ox_sequence_no_edit.purchase_edit_sequence_group"):
                rec.purchase_edit_sequence = False
            else:
                rec.purchase_edit_sequence = True

    def write(self, vals):
        if 'name' in vals:
            purchase_id = self.search([('id', '!=', self.id), ('name', '=', vals['name'])])
            if purchase_id:
                raise ValidationError('The {} Sequence Number already exits'.format(vals['name']))
        return super(PurchaseOrder, self).write(vals)
