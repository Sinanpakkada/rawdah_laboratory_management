# -*- coding: utf-8 -*-
from odoo import fields, models

class TestResultBillLine(models.Model):
    _name = 'test.result.bill.line'
    _description = 'Bill Line'
    _order = 'id ASC'

    result_id = fields.Many2one(
        'test.result',
        string="Test Result",
        required=True,
        ondelete="cascade",
        index=True,
    )

    test_id = fields.Many2one(
        'test.type',
        string="Test",
        required=True,
        ondelete='restrict',
    )

    # Use related field so price always reflects test.type.test_amount
    amount = fields.Float(
        string="Amount",
        related='test_id.test_amount',
        store=True,
        readonly=True,
    )
