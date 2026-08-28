# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.fields import Command
from odoo.tests import tagged
from odoo.tools import formatLang

from odoo.addons.sale.tests.common import TestSaleCommon


@tagged('post_install', '-at_install')
class TestSaleOrderCreditWarning(TestSaleCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company.account_use_credit_limit = True

    def _create_order(self, amount_total, partner=None):
        """Create a draft sale.order whose amount_total equals `amount_total`
        by adding a single untaxed order line with that price."""
        return self.env['sale.order'].create({
            'partner_id': (partner or self.partner_a).id,
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

    def test_confirmed_order_no_banner(self):
        """A confirmed order (state 'sale') must show no banner even when
        exposure is well over the credit limit - the warning is only
        relevant while the order is still a quotation (draft/sent)."""
        self.partner_a.credit_limit = 1000.0
        order = self._create_order(amount_total=1200.0)
        order.action_confirm()
        self.assertEqual(order.state, 'sale')
        self.assertFalse(order.credit_limit_warning_level)
        self.assertFalse(order.partner_credit_warning)

    def test_non_accounting_user_still_sees_banner(self):
        """A plain Sales user (no Invoicing/Accounting group membership)
        must still see the correct-tier banner - the model's sudo() read of
        the commercial partner's credit fields must not be silently blanked
        out by the acting user's own access rights."""
        salesman = self.company_data['default_user_salesman']
        self.assertFalse(
            salesman.has_group('account.group_account_invoice')
            or salesman.has_group('account.group_account_readonly'),
            "Test setup assumption violated: salesman must not hold an "
            "Invoicing/Accounting group",
        )
        self.partner_a.credit_limit = 1000.0
        order = self._create_order(amount_total=1200.0)
        order_as_salesman = order.with_user(salesman)
        self.assertEqual(
            order_as_salesman.credit_limit_warning_level, 'danger')
        self.assertTrue(order_as_salesman.partner_credit_warning)

    # -- UAT E2E spec
    # (memory-bank/uat/spec-customer-credit-limit-warning-e2e.md) --
    # These three cases codify the browser-verified journey from the passed
    # /bmb:uat walk. They exercise the same compute logic as the tests above
    # but pin the exact figures the UAT spec walked through in the UI, and
    # assert that all three currency figures (limit / outstanding / this-order)
    # are present in the rendered message, matching what a user would see.

    def test_e2e_warning_tier_via_ui_equivalent_values(self):
        """Partner with credit_limit=1000 and existing outstanding exposure
        of 400 (booked via a prior confirmed-but-uninvoiced order, mirroring
        the credit_to_invoice idiom used by
        test_commercial_partner_credit_limit_warning above). A NEW draft
        order totaling 510 pushes total exposure to 400 + 510 = 910, which
        is 91% of the limit (>= 80% threshold, not over 100%) => 'warning'.
        The message must break out all three figures (limit, outstanding,
        this-order-amount) as formatted currency."""
        self.partner_a.credit_limit = 1000.0
        exposure_order = self._create_order(amount_total=400.0)
        exposure_order.action_confirm()
        self.assertEqual(
            self.partner_a.credit_to_invoice, 400.0,
            "Test setup assumption violated: exposure order should book "
            "400 of outstanding (uninvoiced) exposure",
        )

        order = self._create_order(amount_total=510.0)
        self.assertEqual(order.credit_limit_warning_level, 'warning')

        currency = self.env.company.currency_id
        message = order.partner_credit_warning
        self.assertIn(
            formatLang(self.env, 1000.0, currency_obj=currency), message)
        self.assertIn(
            formatLang(self.env, 400.0, currency_obj=currency), message)
        self.assertIn(
            formatLang(self.env, 510.0, currency_obj=currency), message)

    def test_e2e_danger_tier_via_ui_equivalent_values(self):
        """Same partner/outstanding setup as the warning-tier case above, but
        the new order totals 680, pushing total exposure to
        400 + 680 = 1080 > the 1000 limit => 'danger'. The message must
        still break out all three figures."""
        self.partner_a.credit_limit = 1000.0
        exposure_order = self._create_order(amount_total=400.0)
        exposure_order.action_confirm()
        self.assertEqual(
            self.partner_a.credit_to_invoice, 400.0,
            "Test setup assumption violated: exposure order should book "
            "400 of outstanding (uninvoiced) exposure",
        )

        order = self._create_order(amount_total=680.0)
        self.assertEqual(order.credit_limit_warning_level, 'danger')

        currency = self.env.company.currency_id
        message = order.partner_credit_warning
        self.assertIn(
            formatLang(self.env, 1000.0, currency_obj=currency), message)
        self.assertIn(
            formatLang(self.env, 400.0, currency_obj=currency), message)
        self.assertIn(
            formatLang(self.env, 680.0, currency_obj=currency), message)

    def test_e2e_no_banner_explicit_zero_limit(self):
        """A partner with an EXPLICIT credit_limit of 0.0 (not merely unset)
        must never show a banner, regardless of order amount. This is
        distinct from an *unset* limit, which an ir.default fallback can
        resolve to a non-zero value (e.g. 1.0) - the explicit-zero case must
        be tested on its own to guard against that fallback masking a
        regression."""
        partner = self.env['res.partner'].create({
            'name': "Explicit Zero Limit Partner",
            'credit_limit': 0.0,
        })
        self.assertEqual(
            partner.credit_limit, 0.0,
            "Test setup assumption violated: credit_limit must be "
            "explicitly 0.0, not falling back to an ir.default value",
        )

        order = self._create_order(amount_total=5000.0, partner=partner)
        self.assertEqual(order.partner_credit_warning, '')
        self.assertFalse(order.credit_limit_warning_level)

    # Case 4 from the UAT spec (mobile-viewport rendering of the banner) is
    # explicitly out of scope for a Python TransactionCase - it requires a
    # real browser viewport and is left to /bmb:uat's browser walk.
