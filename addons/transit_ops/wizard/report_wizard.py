from odoo import models, fields, api


class TransitReportWizard(models.TransientModel):
    """
    Report Export Wizard
    ====================
    Owner: Person A

    Transient model (wizard) allowing users to select parameters
    (e.g., date range, export format) and generate CSV or PDF reports.
    """
    _name = 'transit.report.wizard'
    _description = 'Transit Report Wizard'

    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')
    export_type = fields.Selection(
        selection=[
            ('csv', 'CSV Export'),
            ('pdf', 'PDF Export'),
        ],
        string='Export Format',
        required=True,
        default='csv',
    )

    def action_generate_report(self):
        """
        TODO (Person A): Implement report generation logic.
        - For 'csv': Generate CSV file as attachment and trigger download.
        - For 'pdf': Call the act_window action to print a QWeb PDF.
        """
        return True
