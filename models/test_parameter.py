# -*- coding: utf-8 -*-
from odoo import fields, models

class TestParameter(models.Model):
    _name = "test.parameter"
    _description = "Laboratory Test Parameter"

    name = fields.Char(string="Parameter Name", required=True)
    test_type_id = fields.Many2one(
        'test.type', string="Test Type", ondelete='cascade', required=True
    )
    normal_range = fields.Char(
        string="Normal Range", required=True, help="e.g., '14.0 - 18.0'"
    )
    uom_id = fields.Many2one(
        'uom.uom', string="Unit of Measure",
        help="Select the unit of measure for this parameter (e.g., mg/dL, %)."
    )
    _sql_constraints = [
        ('name_test_type_uniq', 'unique(name, test_type_id)',
         'This parameter already exists for this test type!')
    ]