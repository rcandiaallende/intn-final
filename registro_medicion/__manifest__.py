# -*- coding: utf-8 -*-
{
    'name': 'Registro de Mediciones',
    'version': '1.0',
    'summary': 'Módulo para el registro de mediciones',
    'description': 'Gestión de registros de mediciones con datos del instrumento, cliente, y resultados de las pruebas.',
    'website': 'https://www.tusitio.com',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/registro_medicion.xml',
        'views/reg_medicion.xml',
        'wizard/wizard_comisionamiento.xml',
        'reports/bascula.xml',
        'reports/bascula_template.xml',
        'reports/comisionamiento_template.xml',
        'reports/report_configs.xml',

    ],
    'installable': True,
    'application': True,
}
