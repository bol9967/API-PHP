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

    def _sync_invoice_sequence_related_fields(self, old_name, new_name):
        """
        Sync changes for sequence edits.
        - Customer Invoices / Refunds: update payment_reference + AR labels.
        - Vendor Bills / Refunds: only update chatter.
        """
        self.ensure_one()

        if self.move_type in ('out_invoice', 'out_refund'):
            # Customer Invoices/Refunds → update refs & labels
            self.payment_reference = new_name
            # Update journal item labels (only receivable/payable lines)
            self.line_ids.filtered(
                lambda l: l.account_id.account_type in ('asset_receivable', 'liability_payable')
            ).write({'name': new_name})

        # Always log the change in chatter
        self.message_post(
            body=f"Sequence updated from <b>{old_name}</b> to <b>{new_name}</b> by {self.env.user.name}"
        )

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

        # 🚨 Block detaching origin (SO/PO link)
        if 'invoice_origin' in vals:
            vals.pop('invoice_origin')
        if 'invoice_ids' in vals:
            vals.pop('invoice_ids')

        # Keep original origins safe
        linked_origins = {move.id: move.invoice_origin for move in self if move.invoice_origin}

        # Track old names for chatter logs
        old_names = {move.id: move.name for move in self}

        res = super(AccountMove, self).write(vals)

        # Restore origin if cleared
        for move in self:
            if move.id in linked_origins and not move.invoice_origin:
                move.invoice_origin = linked_origins[move.id]

        # Sync after sequence edit
        if 'name' in vals:
            for move in self:
                old_name = old_names.get(move.id)
                if old_name and old_name != move.name:
                    move._sync_invoice_sequence_related_fields(old_name, move.name)

        return res
