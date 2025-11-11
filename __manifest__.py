# -*- coding: utf-8 -*-
{
    'name': 'Laboratory Management',
    'version': '17.0.1.0.0',
    'summary': 'Manage patient test results, reporting, and billing for laboratories.',
    'description': """
Laboratory Management System
============================
This module provides a comprehensive solution for managing laboratory operations within Odoo.

Key Features:
-------------
- Patient registration and management.
- Creation and management of lab test types and parameters.
- Entry of test results for patients.
- Automated workflow from draft to billed state.
- Generation of professional PDF reports for test results.
- Integrated billing and invoicing.
    """,
    'author': 'Rawdah, Sinanpakkada',
    'website': 'https://github.com/Sinanpakkada/rawdah_laboratory_management', # Good to add your repo link
    'category': 'Services/Industries',
    'sequence': 10,
    'depends': [
        'base',
        'mail'
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/test_type_views.xml',
        'views/test_result_views.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}