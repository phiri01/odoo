# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, fields, models
from odoo.tools import formatLang


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    _CREDIT_WARNING_THRESHOLD_RATIO = 0.8

    credit_limit_warning_level = fields.Selection(
        [('warning', 'Warning'), ('danger', 'Danger')],
        compute='_compute_partner_credit_warning',
        store=False,
        help="Set to 'Warning' when this order would push the customer's total "
             "credit exposure to 80% or more of its credit limit, or to "
             "'Danger' when it would exceed the limit entirely.",
    )

    def _compute_partner_credit_warning(self):
        # EXTENDS 'sale'
        super()._compute_partner_credit_warning()
        for order in self:
            order.credit_limit_warning_level = False
            show_warning = order.state in ('draft', 'sent') and \
                order.company_id.account_use_credit_limit
            if not show_warning:
                continue

            # `credit`, `credit_to_invoice` & `credit_limit` are computed on
            # the commercial entity (see account.move._build_credit_warning_message),
            # so roll up to the commercial partner before reading them -
            # otherwise a child contact's own (always-zero) fields silently
            # suppress the warning regardless of the company's real exposure.
            # sudo() to ensure access to these fields, which are restricted
            # to the Invoicing groups (see account.res.partner).
            partner = order.partner_id.commercial_partner_id.sudo()
            limit = partner.credit_limit
            if not limit:
                continue

            outstanding = partner.credit + partner.credit_to_invoice
            this_order_amount = order.amount_total / order.currency_rate
            total_exposure = outstanding + this_order_amount

            if total_exposure > limit:
                level = 'danger'
            elif total_exposure >= self._CREDIT_WARNING_THRESHOLD_RATIO * limit:
                level = 'warning'
            else:
                level = False

            order.credit_limit_warning_level = level
            if level:
                order.partner_credit_warning = self._build_credit_limit_warning_message(
                    order, level, partner, limit, outstanding, this_order_amount,
                )

    def _build_credit_limit_warning_message(self, order, level, partner, limit, outstanding, this_order_amount):
        currency = order.company_id.currency_id
        limit_formatted = formatLang(self.env, limit, currency_obj=currency)
        outstanding_formatted = formatLang(self.env, outstanding, currency_obj=currency)
        this_order_amount_formatted = formatLang(self.env, this_order_amount, currency_obj=currency)

        if level == 'danger':
            return _(
                "%(partner)s has exceeded its credit limit of %(limit)s. "
                "Current outstanding receivables: %(outstanding)s. "
                "This order would add: %(this_order_amount)s.",
                partner=partner.name,
                limit=limit_formatted,
                outstanding=outstanding_formatted,
                this_order_amount=this_order_amount_formatted,
            )
        return _(
            "%(partner)s is approaching its credit limit of %(limit)s. "
            "Current outstanding receivables: %(outstanding)s. "
            "This order would add: %(this_order_amount)s.",
            partner=partner.name,
            limit=limit_formatted,
            outstanding=outstanding_formatted,
            this_order_amount=this_order_amount_formatted,
        )
