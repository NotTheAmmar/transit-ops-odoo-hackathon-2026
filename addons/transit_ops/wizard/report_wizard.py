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
        if self.export_type == 'csv':
            return self._action_export_csv()
        else:
            return self._action_export_pdf()

    def _action_export_csv(self):
        import base64
        import csv
        import io

        vehicles = self.env['transit.vehicle'].search([])
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            'Registration', 'Name', 'Type', 'Status',
            'Region', 'Fuel Cost', 'Maintenance Cost', 'Total Op. Cost'
        ])
        for v in vehicles:
            writer.writerow([
                v.registration_number,
                v.name,
                v.vehicle_type,
                v.status,
                v.region or '',
                v.total_fuel_cost,
                v.total_maintenance_cost,
                v.total_operational_cost,
            ])
        csv_data = base64.b64encode(output.getvalue().encode())
        attachment = self.env['ir.attachment'].create({
            'name': 'fleet_summary.csv',
            'type': 'binary',
            'datas': csv_data,
            'mimetype': 'text/csv',
        })
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%d?download=true' % attachment.id,
            'target': 'self',
        }

    def _action_export_pdf(self):
        vehicles = self.env['transit.vehicle'].search([])
        return self.env.ref('transit_ops.action_report_fleet_summary').report_action(vehicles)