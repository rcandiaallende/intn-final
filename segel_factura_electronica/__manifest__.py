# -*- coding: utf-8 -*-
{
    'name': "Factura Electronica",

    'summary': """
        Factura Electronica
        """,

    'description': """
        Factura Electronica
    """,

    'author': "Segel S.A",
    'website': "http://www.segel.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Invoicing',
    'version': '1.2023.9.9',

    # any module necessary for this one to work correctly
    'depends': ['base','account', 'l10n_py', 'sale_management', 'grupo_account_payment'],

    # always loaded
    'data': [
        'security/security.xml',
        'views/account_invoice_refund_view.xml',
        'views/account_invoice.xml',
        'views/res_config_settings.xml',
        'views/wizard_pago.xml',
        'views/app_basculas.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
