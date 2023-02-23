from datetime import datetime
import calendar
from odoo import models, fields, api


class Employee(models.Model):
    _inherit = 'hr.employee'

    min_hours_per_month = fields.Float(string='Minimum hours per month')
    opt_out_letter = fields.Boolean(string='Opt-out of letters')
    boolean_field = fields.Boolean(string='Boolean field')
    hours_per_month = fields.Float(string='Hours per month', compute='_compute_hours_per_month')
    hours_per_week = fields.Float(string='Hours per week', compute='_compute_hours_per_week')
    hours_per_day = fields.Float(string='Hours per day', compute='_compute_hours_per_day')

    @api.depends('min_hours_per_month')
    def _compute_hours_per_month(self):
        for employee in self:
            # min hrs per diena kad pasiekt min hrs per menesi
            hours_per_day = employee.min_hours_per_month / 30.0
            # hrs per menesi = min hrs per diena * dienu skaicius menesi
            employee.hours_per_month = hours_per_day * calendar.monthrange(datetime.now().year, datetime.now().month)[1]

    @api.depends('min_hours_per_month')
    def _compute_hours_per_week(self):
        for employee in self:
            # kiek hrs per savaite
            hours_per_week = employee.min_hours_per_month / 4.0
            employee.hours_per_week = hours_per_week

    @api.depends('min_hours_per_month')
    def _compute_hours_per_day(self):
        for employee in self:
            # kiek dienu dabartiniam menesi
            days_in_month = calendar.monthrange(datetime.now().year, datetime.now().month)[1]
            # kiek hrs per diena kad pasiekti min hrs per month
            hours_per_day = employee.min_hours_per_month / days_in_month
            employee.hours_per_day = hours_per_day

    def send_information_letter(self):
        for employee in self:
            if not employee.opt_out_letter:
                if employee.hours_per_month < employee.min_hours_per_month:
                    # Load emailo template
                    template = self.env.ref('new_module.mail_template_employee_hours_reminder')
                    # Replace the placeholders with actual values
                    body_html = template.body_html.replace('${employee_name}', employee.name)
                    body_html = body_html.replace('${hours_per_month}', str(employee.hours_per_month))
                    body_html = body_html.replace('${min_hours_per_month}', str(employee.min_hours_per_month))
                    # issiuncia emaila
                    email_values = {
                        'subject': 'Information letter',
                        'body_html': body_html,
                        'email_to': employee.work_email,
                    }
                    email = self.env['mail.mail'].create(email_values)

                    # patikrinu ar issiuncia
                    print("Created email: ", email)
                    email.send()


class Task(models.Model):
    _inherit = 'project.task'

    invoice_id = fields.Many2one('account.move', string='Invoice')

    def create_invoice(self):
        invoice = self.env['account.move'].create({
            'partner_id': self.project_id.partner_id.id,
            'invoice_line_ids': [(0, 0, {
                'name': self.name,
                'quantity': 1,
                'price_unit': self.sale_line_id.price_unit,
                'account_id': self.sale_line_id.account_id.id,
            })]
        })
        self.write({'invoice_id': invoice.id})
