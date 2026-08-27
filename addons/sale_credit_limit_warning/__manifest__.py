# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Sale Credit Limit Warning',
    'version': '18.0.1.0.0',
    'category': 'Sales/Sales',
    'summary': 'Warn salespeople when a quotation would approach or exceed a customer\'s credit limit',
    'description': """
Adds a graduated (warning/danger) credit-limit banner on the sales order form,
extending the existing partner credit-limit check with an intermediate
"approaching the limit" state.
    """,
    'depends': ['sale', 'account'],
    'data': ['views/sale_order_views.xml'],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
