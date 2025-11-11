{
    'name' : 'Lab',
    'version' : '1.0',
    'summary': 'Lab Services',
    'author' : 'Rawdah',
    'sequence': 1,
    'description': """
Lab Services
====================
The specific and easy-to-use Lab services system in Odoo allows you to keep track of all activities in a Laboratory. It provides an easy way to follow up on test results and print them.
    """,
    'category': 'Services',
    'depends': ['base','mail'],
    'data': [
        'data/sequence.xml',
        'views/test_result_views.xml',
        'views/test_type_views.xml',
        'views/menu.xml',
        'security/ir.model.access.csv'
    ],
    'installable': True,
    'application': True,
    'assets': {},
    'license': 'LGPL-3',
}
