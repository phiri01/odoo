# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.fields import Command
from odoo.tests import tagged

from odoo.addons.sale.tests.common import TestSaleCommon


@tagged('post_install', '-at_install')
class TestSaleOrderCreditWarning(TestSaleCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company.account_use_credit_limit = True

    def _create_order(self, amount_total):
        """Create a draft sale.order whose amount_total equals `amount_total`
        by adding a single untaxed order line with that price."""
        return self.env['sale.order'].create({
            'partner_id': self.partner_a.id,
            'order_line': [Command.create({
                'product_id': self.product_a.id,
                'product_uom_qty': 1,
                'price_unit': amount_total,
                'tax_id': False,
            })],
        })

    def test_no_credit_limit_set_no_banner(self):
        """No credit_limit on the partner => no warning at all."""
        self.partner_a.credit_limit = 0.0
        order = self._create_order(amount_total=1000.0)
        self.assertFalse(order.credit_limit_warning_level)
        self.assertFalse(order.partner_credit_warning)

    def test_exposure_well_within_limit_no_banner(self):
        """Exposure well below 80% of the limit => no warning."""
        self.partner_a.credit_limit = 1000.0
        order = self._create_order(amount_total=100.0)
        self.assertFalse(order.credit_limit_warning_level)

    def test_exposure_exactly_80_percent_is_warning(self):
        """Exposure exactly at 80% of the limit => 'warning'."""
        self.partner_a.credit_limit = 1000.0
        order = self._create_order(amount_total=800.0)
        self.assertEqual(order.credit_limit_warning_level, 'warning')

    def test_exposure_between_80_and_100_percent_is_warning(self):
        """Exposure strictly between 80% and 100% of the limit => 'warning'."""
        self.partner_a.credit_limit = 1000.0
        order = self._create_order(amount_total=900.0)
        self.assertEqual(order.credit_limit_warning_level, 'warning')

    def test_exposure_exactly_at_limit_is_still_warning(self):
        """Exposure exactly at 100% of the limit => still 'warning', not 'danger'."""
        self.partner_a.credit_limit = 1000.0
        order = self._create_order(amount_total=1000.0)
        self.assertEqual(order.credit_limit_warning_level, 'warning')

    def test_exposure_over_limit_is_danger(self):
        """Exposure exceeding the limit => 'danger'."""
        self.partner_a.credit_limit = 1000.0
        order = self._create_order(amount_total=1200.0)
        self.assertEqual(order.credit_limit_warning_level, 'danger')
        self.assertTrue(order.partner_credit_warning)

    def test_commercial_partner_credit_limit_warning(self):
        """Existing exposure booked against the commercial (parent) entity
        must still be attributed to a NEW order placed on a child contact,
        mirroring core's test_commercial_partner_credit
        (addons/sale/tests/test_credit_limit.py::test_commercial_partner_credit).

        `credit` / `credit_to_invoice` are computed per commercial entity -
        a child contact's own values always stay at 0 (see
        `_find_accounting_partner` / `commercial_partner_id` rollup in
        addons/account/models/partner.py). Reading `order.partner_id`
        directly (instead of `order.partner_id.commercial_partner_id`)
        would silently ignore the parent's real outstanding exposure.
        """
        company = self.env['res.partner'].create({
            'name': "Big Company",
            'is_company': True,
            'credit_limit': 1000.0,
            'child_ids': [Command.link(self.partner_a.id)],
        })
        self.assertEqual(self.partner_a.commercial_partner_id, company)

        # Book existing exposure (900) against the child contact - it rolls
        # up and is only visible on the commercial (parent) entity.
        exposure_order = self._create_order(amount_total=900.0)
        exposure_order.action_confirm()
        self.assertFalse(
            self.partner_a.credit_to_invoice,
            "Credit exposure should only be visible on the commercial entity",
        )
        self.assertEqual(company.credit_to_invoice, 900.0)

        # A further small order (200) on the same child contact should push
        # the company's total exposure (900 + 200 = 1100) over its limit
        # (1000) - a warning that only surfaces if the exposure is correctly
        # attributed to the commercial entity rather than the child contact.
        order = self._create_order(amount_total=200.0)
        self.assertEqual(order.partner_id, self.partner_a)
        self.assertEqual(order.credit_limit_warning_level, 'danger')
        self.assertTrue(order.partner_credit_warning)
        self.assertIn(company.name, order.partner_credit_warning)

    def test_account_use_credit_limit_disabled_no_banner(self):
        """Even when over limit, disabling account_use_credit_limit suppresses the banner."""
        self.env.company.account_use_credit_limit = False
        self.partner_a.credit_limit = 1000.0
        order = self._create_order(amount_total=1200.0)
        self.assertFalse(order.credit_limit_warning_level)
        self.assertFalse(order.partner_credit_warning)
