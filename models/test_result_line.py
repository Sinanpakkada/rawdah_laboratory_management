# -*- coding: utf-8 -*-
from odoo import fields, models


class TestResultLine(models.Model):
    _name = 'test.result.line'
    _description = 'Test Result Line'

    result_id = fields.Many2one(
        'test.result', string="Result ID", ondelete='cascade'
    )
    parameter_id = fields.Many2one(
        'test.parameter', string='Parameter',
    )
    result_value = fields.Char(string="Result")

    # --- Related fields for display and consistency ---

    normal_range = fields.Char(
        string="Normal Range",
        related='parameter_id.normal_range',
        readonly=True,
        store=True,
    )
    uom_id = fields.Many2one(
        related='parameter_id.uom_id',
        string="Unit of Measure",
        readonly=True,
        store=True,
    )
    test_type_id = fields.Many2one(
        related='parameter_id.test_type_id',
        string="Test Type",
        store=True,
    )