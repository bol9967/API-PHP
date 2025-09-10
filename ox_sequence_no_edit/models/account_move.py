from odoo import models, fields
from odoo.exceptions import ValidationError

class AccountMove(models.Model):
    _inherit = 'account.move'

    invoice_edit_sequence = fields.Boolean(
        string='Account Invoice Edit Sequence',
        compute='_compute_for_hide_account_invoice_edit_sequence'
    )

    def _compute_for_hide_account_invoice_edit_sequence(self):
        for rec in self:
            if self.env.user.has_group("ox_sequence_no_edit.invoice_edit_sequence_group"):
                rec.invoice_edit_sequence = False
            else:
                rec.invoice_edit_sequence = True

    def _sync_invoice_sequence_related_fields(self, new_name):
        """Sync sequence changes to payment_reference and AR/AP line labels."""
        self.ensure_one()

        # update payment_reference
        self.payment_reference = new_name

        # update journal item labels (only receivable/payable lines)
        self.line_ids.filtered(
            lambda l: l.account_id.account_type in ('asset_receivable', 'liability_payable')
        ).write({'name': new_name})

        # optional: log in chatter
        self.message_post(
            body=f"Invoice sequence updated to <b>{new_name}</b> by {self.env.user.name}"
        )

    def write(self, vals):
        # Prevent duplicate sequence numbers
        if 'name' in vals:
            existing = self.search([
                ('id', '!=', self.id),
                ('name', '=', vals['name'])
            ])
            if existing:
                raise ValidationError(
                    'The {} Sequence Number already exists'.format(vals['name'])
                )

        res = super(AccountMove, self).write(vals)

        # After write, sync related fields if name changed
        if 'name' in vals:
            for move in self:
                move._sync_invoice_sequence_related_fields(move.name)

        return res
