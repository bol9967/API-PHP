from odoo import models, fields, api
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    edit_sequence = fields.Boolean(string='Sales Order Edit Sequence', compute='_eg_compute_for_edit_sequence')

    def _eg_compute_for_edit_sequence(self):
        for rec in self:
            if self.env.user.has_group("ox_sequence_no_edit.sale_edit_sequence_group"):
                rec.edit_sequence = False
            else:
                rec.edit_sequence = True

    def write(self, vals):
        if 'name' in vals:
            sale_id = self.search([('id', '!=', self.id), ('name', '=', vals['name'])])
            if sale_id:
                raise ValidationError('The {} Sequence Number already exits'.format(vals['name']))
        return super(SaleOrder, self).write(vals)

# _sql_constraints = [
#     ('name_uniq', 'unique (name)', "The {} Sequence Number already exits".format(name)),
# ]
