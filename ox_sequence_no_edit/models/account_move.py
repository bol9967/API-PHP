from odoo import models, fields
from odoo.exceptions import ValidationError

class AccountMove(models.Model):
    _inherit = 'account.move'

    invoice_edit_sequence = fields.Boolean(string='Account Invoice Edit Sequence',
                                           compute='_compute_for_hide_account_invoice_edit_sequence')

    def _compute_for_hide_account_invoice_edit_sequence(self):
        for rec in self:
            if self.env.user.has_group("ox_sequence_no_edit.invoice_edit_sequence_group"):
                rec.invoice_edit_sequence = False
            else:
                rec.invoice_edit_sequence = True

    def write(self, vals):
        if 'name' in vals:
            sale_id = self.search([('id', '!=', self.id), ('name', '=', vals['name'])])
            if sale_id:
                raise ValidationError('The {} Sequence Number already exits'.format(vals['name']))
        return super(AccountMove, self).write(vals)
