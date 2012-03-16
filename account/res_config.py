# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import logging
import time
import datetime
from dateutil.relativedelta import relativedelta
from operator import itemgetter
from os.path import join as opj

from tools.translate import _
from osv import fields, osv
import netsvc
import tools

class account_configuration(osv.osv_memory):
    _name = 'account.installer'
    _inherit = 'res.config.settings'
    __logger = logging.getLogger(_name)

    def _get_charts(self, cr, uid, context=None):
        modules = self.pool.get('ir.module.module')
        # Looking for the module with the 'Account Charts' category
        category_name, category_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'base', 'module_category_localization_account_charts')
        ids = modules.search(cr, uid, [('category_id', '=', category_id)], context=context)
        charts = list(
            sorted(((m.name, m.shortdesc)
                    for m in modules.browse(cr, uid, ids, context=context)),
                   key=itemgetter(1)))
        charts.insert(0, ('configurable', 'Generic Chart Of Accounts'))
        return charts

    _columns = {
            'company_id': fields.many2one('res.company', 'Company',help="Your company."),
            'currency_id': fields.related('company_id', 'currency_id', type='many2one', relation='res.currency', string='Currency', store=True, help="Currency of your company."),
            'charts': fields.selection(_get_charts, 'Chart of Accounts',
                                        required=True,
                                        help="Installs localized accounting charts to match as closely as "
                                             "possible the accounting needs of your company based on your "
                                             "country."),
            'date_start': fields.date('Start Date', required=True),
            'date_stop': fields.date('End Date', required=True),
            'period': fields.selection([('month', 'Monthly'), ('3months','3 Monthly')], 'Periods', required=True),
            'has_default_company' : fields.boolean('Has Default Company', readonly=True),
            'chart_template_id': fields.many2one('account.chart.template', 'Chart Template'),
            'fiscalyear_id': fields.many2one('account.fiscalyear', 'Fiscal Year'),
            'default_paypal_account': fields.char("Your Paypal Account", size=128, help="Paypal username (usually email) for receiving online payments.", default_model='res.company'),
            'company_footer': fields.char("Footer of Reports", size=128, readonly=True, help="Footer of reports based on your bank accounts."),
            'sale_journal_id': fields.many2one('account.journal','Sale Journal'),
            'customer_invoice_sequence_prefix': fields.related('sale_journal_id', 'sequence_id', 'prefix', type='char', relation='ir.sequence', string='Invoice Sequence'),
            'customer_invoice_sequence_next': fields.related('sale_journal_id', 'sequence_id', 'number_next', type='integer', relation='ir.sequence', string='Invoice Sequence Next Number'),
            'sale_refund_journal_id': fields.many2one('account.journal','Sale Refund Journal'),
            'customer_refund_sequence_prefix': fields.related('sale_refund_journal_id', 'sequence_id', 'prefix', type='char', relation='ir.sequence', string='Refund Sequence'),
            'customer_refund_sequence_next': fields.related('sale_refund_journal_id', 'sequence_id', 'number_next', type='integer', relation='ir.sequence', string='Refund Sequence Next Number'),
            'purchase_journal_id': fields.many2one('account.journal','Purchase Journal'),
            'supplier_invoice_sequence_prefix': fields.related('purchase_journal_id', 'sequence_id', 'prefix', type='char', relation='ir.sequence', string='Supplier Invoice Sequence'),
            'supplier_invoice_sequence_next': fields.related('purchase_journal_id', 'sequence_id', 'number_next', type='integer', relation='ir.sequence', string='Supplier Invoice Sequence Next Number'),
            'purchase_refund_journal_id': fields.many2one('account.journal','Purchase Refund Journal'),
            'supplier_refund_sequence_prefix': fields.related('purchase_refund_journal_id', 'sequence_id', 'prefix', type='char', relation='ir.sequence', string='Supplier Refund Sequence'),
            'supplier_refund_sequence_next': fields.related('purchase_refund_journal_id', 'sequence_id', 'number_next', type='integer', relation='ir.sequence', string='Supplier Refund Sequence Next Number'),

            'module_account_check_writing': fields.boolean('Support check writings',
                                            help="""  This allows you to check writing and printing.
                                            It installs the account_check_writing module."""),
            'module_account_accountant': fields.boolean('Accountant Features',
                                        help="""This allows you to access all the accounting features like the journal items and the chart of accounts.
                                        It installs the account_accountant module."""),
            'module_account_asset': fields.boolean('Assets Management',
                                    help="""This allows you to manages the assets owned by a company or an individual. It will keep track of depreciation's occurred on
                                    those assets. And it allows to create Move's of the depreciation lines.
                                    It installs the account_asset module."""),
            'module_account_budget': fields.boolean('Budgets Management',
                                    help="""This allows accountants to manage analytic and crossovered budgets.
                                    Once the Master Budgets and the Budgets are defined (in Accounting/Budgets/),
                                    the Project Managers can set the planned amount on each Analytic Account.
                                    It installs the account_budget module."""),
            'module_account_payment': fields.boolean('Supplier Payment Orders',
                                    help="""This allows you to create and manage your payment orders, with purposes to
                                    * serve as base for an easy plug-in of various automated payment mechanisms.
                                    * provide a more efficient way to manage invoice payment.
                                    It installs the account_payment module."""),
            'module_account_voucher': fields.boolean('Manage Customer Payments',
                                    help="""This includes all the basic requirements of Voucher Entries for Bank, Cash, Sales, Purchase, Expanse, Contra, etc.
                                    It installs the account_voucher module."""),
            'module_account_followup': fields.boolean('Customer Follow-Ups',
                                    help="""This allows to automate letters for unpaid invoices, with multi-level recalls.
                                    It installs the account_followup module."""),
            'module_account_analytic_plans': fields.boolean('Support Multiple Analytic Plans',
                                        help="""This allows to use several analytic plans, according to the general journal.
                                        It installs the account_analytic_plans module."""),
            'module_account_analytic_default': fields.boolean('Rules for Analytic Assignation',
                                            help="""Set default values for your analytic accounts
                                            Allows to automatically select analytic accounts based on criterias:
                                            * Product
                                            * Partner
                                            * User
                                            * Company
                                            * Date.
                                        It installs the account_analytic_default module."""),
            'module_account_invoice_layout': fields.boolean('Allow notes and subtotals',
                                            help="""This provides some features to improve the layout of the invoices.
                                            It gives you the possibility to:
                                            * order all the lines of an invoice
                                            * add titles, comment lines, sub total lines
                                            * draw horizontal lines and put page breaks.
                                            It installs the account_invoice_layout module."""),

            'group_analytic_account_for_sales': fields.boolean('Analytic Accounting for Sales', group='base.group_user', implied_group='base.group_analytic_account_for_sales',
                                                               help="Allows you to set analytic account for sale order. It assigns 'Analytic Accounting for Sales' group to all employees."),
            'group_analytic_account_for_purchase': fields.boolean('Analytic Accounting for Purchase', group='base.group_user', implied_group='base.group_analytic_account_for_purchase',
                                                                  help="Allows you to set analytic account for purchase order. It assigns 'Analytic Accounting for Purchase' group to all employees."),
            'group_dates_periods': fields.boolean('Allow dates/periods', group='base.group_user', implied_group='base.group_dates_periods',
                                                  help="Allows you to keep the period same as your invoice date when you validate the invoice."\
                                                       "It will add the group 'Allow dates and periods' for all users."),
            'group_proforma_invoices': fields.boolean('Allow Pro-forma Invoices', group='base.group_user', implied_group='base.group_proforma_invoices',
                                                      help="Allows you to put invoice in pro-forma state. It assigns 'Allow Pro-forma Invoices' group to all employees."),

            'multi_charts_id':fields.many2one('wizard.multi.charts.accounts', 'Multi charts accounts'),
            'taxes_id':fields.many2one('account.tax.template', 'Default Sale Tax'),
            'supplier_taxes_id':fields.many2one('account.tax.template', 'Default Purchase Tax'),
            'sale_tax_rate': fields.float('Sales Tax(%)'),
            'purchase_tax_rate': fields.float('Purchase Tax(%)'),
            'complete_tax_set': fields.boolean('Complete Set of Taxes'),
    }
    def _default_company(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        return user.company_id and user.company_id.id or False

    def _default_has_default_company(self, cr, uid, context=None):
        count = self.pool.get('res.company').search_count(cr, uid, [], context=context)
        return bool(count == 1)

    _defaults = {
            'date_start': lambda *a: time.strftime('%Y-01-01'),
            'date_stop': lambda *a: time.strftime('%Y-12-31'),
            'period': 'month',
            'company_id': _default_company,
            'has_default_company': _default_has_default_company,
            'charts': 'configurable',
    }

    def _check_default_tax(self, cr, uid, context=None):
        ir_values_obj = self.pool.get('ir.values')
        taxes = {}
        for tax in ir_values_obj.get(cr, uid, 'default', False, ['product.template']):
            if tax[1] == 'taxes_id':
                taxes.update({'taxes_id': tax[2]})
            if tax[1] == 'supplier_taxes_id':
                taxes.update({'supplier_taxes_id': tax[2]})
        return taxes

    def set_tax_defaults(self, cr, uid, ids, context=None):
        ir_values_obj = self.pool.get('ir.values')

        res = {}
        wizard = self.browse(cr, uid, ids)[0]
        if wizard.taxes_id.id:
            ir_values_obj.set_default(cr, uid, 'product.template', 'taxes_id', wizard.taxes_id.id )

        if wizard.supplier_taxes_id.id:
            ir_values_obj.set_default(cr, uid, 'product.template', 'supplier_taxes_id', wizard.supplier_taxes_id.id )

        return res

    def default_get(self, cr, uid, fields_list, context=None):
        ir_values_obj = self.pool.get('ir.values')
        chart_template_obj = self.pool.get('account.chart.template')
        fiscalyear_obj = self.pool.get('account.fiscalyear')
        journal_obj = self.pool.get('account.journal')
        res = super(account_configuration, self).default_get(cr, uid, fields_list, context=context)
        taxes = self._check_default_tax(cr, uid, context)
        chart_template_ids = chart_template_obj.search(cr, uid, [('visible', '=', True)], context=context)
        fiscalyear_ids = fiscalyear_obj.search(cr, uid, [('date_start','=',time.strftime('%Y-01-01')),('date_stop','=',time.strftime('%Y-12-31'))])

        cmp_id = self.pool.get('ir.model.data').get_object(cr, uid, 'base', 'main_company').id
        company_data = self.pool.get('res.company').browse(cr, uid, cmp_id)
        res.update({'company_footer': company_data.rml_footer2})

        journal_ids = journal_obj.search(cr, uid, [('company_id', '=', res.get('company_id'))])
        if journal_ids:
            for journal in journal_obj.browse(cr, uid, journal_ids, context=context):
                if journal.type == 'sale':
                    res.update({'sale_journal_id': journal.id})
                if journal.type == 'sale_refund':
                    res.update({'sale_refund_journal_id': journal.id})
                if journal.type == 'purchase':
                    res.update({'purchase_journal_id': journal.id})
                if journal.type == 'purchase_refund':
                    res.update({'purchase_refund_journal_id': journal.id})

        if chart_template_ids:
            data = chart_template_obj.browse(cr, uid, chart_template_ids[0], context=context)
            res.update({'complete_tax_set': data.complete_tax_set})
            supplier_taxes_id = ir_values_obj.get_default(cr, uid, 'product.template', 'supplier_taxes_id')
            res.update({'supplier_taxes_id': supplier_taxes_id})
            taxes_id = ir_values_obj.get_default(cr, uid, 'product.template', 'taxes_id')
            res.update({'chart_template_id': taxes_id})
            res.update({'chart_template_id': chart_template_ids[0]})

        if fiscalyear_ids:
            res.update({'fiscalyear_id': fiscalyear_ids[0]})
        if taxes:
            if chart_template_ids:
                sale_tax_id = taxes.get('taxes_id')
                res.update({'taxes_id': isinstance(sale_tax_id,list) and sale_tax_id[0] or sale_tax_id})
                purchase_tax_id = taxes.get('supplier_taxes_id')
                res.update({'supplier_taxes_id': isinstance(purchase_tax_id,list) and purchase_tax_id[0] or purchase_tax_id})
        else:
            res.update({'sale_tax_rate': 15.0, 'purchase_tax_rate': 15.0})
        return res

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        ir_values_obj = self.pool.get('ir.values')
        res = super(account_configuration, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu)
        cmp_select = []
        # display in the widget selection only the companies that haven't been configured yet
        unconfigured_cmp = self.get_unconfigured_cmp(cr, uid, context=context)
        for field in res['fields']:
            if field == 'company_id':
                res['fields'][field]['domain'] = [('id','in',unconfigured_cmp)]
                res['fields'][field]['selection'] = [('', '')]
                if unconfigured_cmp:
                    cmp_select = [(line.id, line.name) for line in self.pool.get('res.company').browse(cr, uid, unconfigured_cmp)]
                    res['fields'][field]['selection'] = cmp_select
        return res

    def get_unconfigured_cmp(self, cr, uid, context=None):
        """ get the list of companies that have not been configured yet
        but don't care about the demo chart of accounts """
        cmp_select = []
        company_ids = self.pool.get('res.company').search(cr, uid, [], context=context)
        cr.execute("SELECT company_id FROM account_account WHERE active = 't' AND account_account.parent_id IS NULL AND name != %s", ("Chart For Automated Tests",))
        configured_cmp = [r[0] for r in cr.fetchall()]
        return list(set(company_ids)-set(configured_cmp))

    def check_unconfigured_cmp(self, cr, uid, context=None):
        """ check if there are still unconfigured companies """
        if not self.get_unconfigured_cmp(cr, uid, context=context):
            raise osv.except_osv(_('No unconfigured company !'), _("There are currently no company without chart of account. The wizard will therefore not be executed."))

    def on_change_start_date(self, cr, uid, id, start_date=False):
        if start_date:
            start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            end_date = (start_date + relativedelta(months=12)) - relativedelta(days=1)
            return {'value': {'date_stop': end_date.strftime('%Y-%m-%d')}}
        return {}

    def on_change_company_id(self, cr, uid, id, company_id=False):
        company_obj = self.pool.get('res.company')
        currency_id = company_obj.browse(cr, uid, company_id).currency_id
        return {'value': {'currency_id': currency_id.id}}

    def install_chartofaccounts(self, cr, uid, ids, context=None):
        ir_module = self.pool.get('ir.module.module')
        multi_chart_obj = self.pool.get('wizard.multi.charts.accounts')
        chart_template_obj = self.pool.get('account.chart.template')
        tax_templ_obj = self.pool.get('account.tax.template')

        data = self.read(cr, uid, ids, context=context)[0]
        if context is None:
            context = {}
        for res in self.read(cr, uid, ids, context=context):
            chart = res.get('charts')
            if chart == 'configurable':
                #load generic chart of account
                fp = tools.file_open(opj('account', 'configurable_account_chart.xml'))
                tools.convert_xml_import(cr, 'account', fp, {}, 'init', True, None)
                fp.close()
            elif chart.startswith('l10n_'):
                mod_ids = ir_module.search(cr, uid, [('name','=',chart)])
                if mod_ids and ir_module.browse(cr, uid, mod_ids[0], context).state == 'uninstalled':
                    ir_module.button_immediate_install(cr, uid, mod_ids, context)

        chart_template_ids = chart_template_obj.search(cr, uid, [('visible', '=', True)], context=context)
        complete_tax_set = chart_template_obj.browse(cr, uid, chart_template_ids[0]).complete_tax_set
        if not complete_tax_set:
            code_digits = multi_chart_obj.onchange_chart_template_id(cr, uid, [], chart_template_ids[0], context=context)['value']['code_digits']
            object_id = multi_chart_obj.create(cr, uid, {'code_digits': code_digits , 'sale_tax_rate':data['sale_tax_rate'], 'purchase_tax_rate': data['purchase_tax_rate']}, context=context)
            multi_chart_obj.execute(cr, uid, [object_id], context=context)

    def configure_fiscalyear(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        fy_obj = self.pool.get('account.fiscalyear')
        for res in self.read(cr, uid, ids, context=context):
            if 'date_start' in res and 'date_stop' in res:
                f_ids = fy_obj.search(cr, uid, [('date_start', '<=', res['date_start']), ('date_stop', '>=', res['date_stop']), ('company_id', '=', res['company_id'][0])], context=context)
                if not f_ids:
                    name = code = res['date_start'][:4]
                    if int(name) != int(res['date_stop'][:4]):
                        name = res['date_start'][:4] +'-'+ res['date_stop'][:4]
                        code = res['date_start'][2:4] +'-'+ res['date_stop'][2:4]
                    vals = {
                        'name': name,
                        'code': code,
                        'date_start': res['date_start'],
                        'date_stop': res['date_stop'],
                        'company_id': res['company_id'][0]
                    }
                    fiscal_id = fy_obj.create(cr, uid, vals, context=context)
                    if res['period'] == 'month':
                        fy_obj.create_period(cr, uid, [fiscal_id])
                    elif res['period'] == '3months':
                        fy_obj.create_period3(cr, uid, [fiscal_id])

account_configuration()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: