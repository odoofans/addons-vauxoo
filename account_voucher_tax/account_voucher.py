# -*- coding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2012 Vauxoo - http://www.vauxoo.com
#    All Rights Reserved.
#    info@vauxoo.com
############################################################################
#    Coded by: Rodo (rodo@vauxoo.com)
############################################################################
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

from osv import osv, fields
from tools.translate import _

class account_voucher(osv.osv):
    _inherit = 'account.voucher'
    
    def voucher_move_line_create(self, cr, uid, voucher_id, line_total, move_id, company_currency, current_currency, context=None):
        move_obj = self.pool.get('account.move')
        move_line_obj = self.pool.get('account.move.line')
        invoice_obj = self.pool.get('account.invoice')
        currency_obj = self.pool.get('res.currency')
        res=super(account_voucher, self).voucher_move_line_create(cr, uid, voucher_id, line_total, move_id, company_currency, current_currency, context=None)
        print res,"ressssss"
        print line_total,"totaaal"
        new_move=move_obj.create(cr, uid, self.account_move_get(cr, uid, voucher_id, context=context), context=context)
        for voucher in self.browse(cr,uid,[voucher_id],context=context):
            lines=[]
            for line in voucher.line_ids:
                factor=line.amount_original and line.amount/line.amount_original or 0.0
                print factor,"facorrrrrrrr"
                if line.amount>0:
                    invoice_ids=invoice_obj.search(cr,uid,[('move_id','=',line.move_line_id.move_id.id)],context=context)
                    for invoice in invoice_obj.browse(cr,uid,invoice_ids,context=context):
                        for tax in invoice.tax_line:
                            if tax.tax_id.tax_voucher_ok:
                                move_ids=[]
                                account=tax.tax_id.account_collected_voucher_id.id
                                credit_amount= float('%.*f' % (2,((tax.tax_id.amount*tax.base)*factor)))
                                if credit_amount:
                                    if abs(float('%.*f' % (2,credit_amount))-(tax.tax_id.amount*tax.base))<=.02:
                                        credit_amount=credit_amount-abs(float('%.*f' % (2,credit_amount))-(tax.tax_id.amount*tax.base))
                                    if abs(float('%.*f' % (2,credit_amount))+ ((tax.tax_id.amount*tax.base)*(1-factor))-(tax.tax_id.amount*tax.base))<.02:
                                        credit_amount=credit_amount-abs(float('%.*f' % (2,credit_amount))+ ((tax.tax_id.amount*tax.base)*(1-factor))-(tax.tax_id.amount*tax.base))
                                context['date']=invoice.date_invoice
                                credit_amount=currency_obj.compute(cr, uid, line.move_line_id.currency_id.id,company_currency, float('%.*f' % (2,credit_amount)), round=False, context=context)
                                print credit_amount,"por eso sale de mas"
                                debit_amount=0.0
                                if tax.tax_id.amount<0:
                                    credit_amount=0.0
                                    debit_amount=float('%.*f' % (2,((tax.tax_id.amount*tax.base)*factor)))
                                    if debit_amount: 
                                        if abs(float('%.*f' % (2,debit_amount))-(tax.tax_id.amount*tax.base))<=.02:
                                            debit_amount=debit_amount-abs(float('%.*f' % (2,debit_amount))-(tax.tax_id.amount*tax.base))
                                        if abs(float('%.*f' % (2,debit_amount))+ ((tax.tax_id.amount*tax.base)*(1-factor))-(tax.tax_id.amount*tax.base))<.02:
                                            debit_amount=debit_amount-abs(float('%.*f' % (2,debit_amount))+ ((tax.tax_id.amount*tax.base)*(1-factor))-(tax.tax_id.amount*tax.base))
                                        debit_amount=(-1.0*currency_obj.compute(cr, uid, line.move_line_id.currency_id.id,company_currency, float('%.*f' % (2,debit_amount)), round=False, context=context))
                                if invoice.type=='out_invoice':## considerar que hacer con refund
                                    account=tax.tax_id.account_paid_voucher_id.id
                                    credit_amount, debit_amount=debit_amount, credit_amount
                                move_line={
                                    'journal_id': voucher.journal_id.id,
                                    'period_id': voucher.period_id.id,
                                    'name': tax.name or '/',
                                    'account_id': tax.account_id.id,
                                    'move_id': int(new_move),
                                    'partner_id': voucher.partner_id.id,
                                    'company_id':company_currency,
                                    'currency_id': line.move_line_id and (company_currency <> current_currency and current_currency) or False,
                                    'quantity': 1,
                                    'credit': credit_amount,
                                    'debit': debit_amount,
                                    'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
                                    'date': voucher.date,
                                    
                                    }
                                if company_currency!=current_currency:
                                    move_line['amount_currency']=currency_obj.compute(cr, uid, company_currency, current_currency,credit_amount, round=False, context=context)
                                move_ids.append(move_line_obj.create(cr,uid,move_line,context=context))
                                move_line={
                                    'journal_id': voucher.journal_id.id,
                                    'period_id': voucher.period_id.id,
                                    'name': tax.name or '/',
                                    'account_id': account,
                                    'move_id': int(new_move),
                                    'partner_id': voucher.partner_id.id,
                                    'company_id':company_currency,
                                    #'currency_id': line.move_line_id and (company_currency <> line.move_line_id.currency_id.id and line.move_line_id.currency_id.id) or False,
                                    'currency_id': line.move_line_id and (company_currency <> current_currency and current_currency) or False,
                                    'quantity': 1,
                                    'credit': debit_amount,
                                    'debit': credit_amount,
                                    'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
                                    'date': voucher.date,
                                    }
                                if company_currency!=current_currency:
                                    move_line['amount_currency']=currency_obj.compute(cr, uid, company_currency, current_currency,credit_amount, round=False, context=context)
                                move_line_obj.create(cr,uid,move_line,context=context)

                                account_income_id = voucher.company_id.income_currency_exchange_account_id.id
                                account_expense_id = voucher.company_id.expense_currency_exchange_account_id.id
                                for m in move_obj.browse(cr,uid,[move_id],context=context):
                                    for mlines in m.line_id:
                                        dif=0
                                        if mlines.account_id.id==account_income_id:
                                            account=account_expense_id
                                            if invoice.type=='out_invoice':
                                                debit=(debit_amount-tax.tax_amount)
                                                credit=0.0
                                                dif=1
                                            else:
                                                debit=0.0
                                                credit=(credit_amount-tax.tax_amount)
                                                dif=1
                                        if mlines.account_id.id==account_expense_id:
                                            account=account_income_id
                                            if invoice.type=='out_invoice':
                                                debit=0.0
                                                credit=(credit_amount-tax.tax_amount)
                                                dif=1
                                            else:
                                                debit=(debit_amount-tax.tax_amount)
                                                credit=0.0
                                                dif=1
                                        if dif:
                                            move_line = {
                                                'journal_id': voucher.journal_id.id,
                                                'period_id': voucher.period_id.id,
                                                'name': _('change')+': '+(line.name or '/'),
                                                'account_id': account,
                                                'move_id': int(new_move),
                                                'partner_id': voucher.partner_id.id,
                                                'currency_id': line.move_line_id and (company_currency <> current_currency and current_currency) or False,
                                                'amount_currency': 0.0,
                                                'quantity': 1,
                                                'credit': credit,
                                                'debit': debit,
                                                'date': line.voucher_id.date,
                                            }
                                            if company_currency!=current_currency:
                                                move_line['amount_currency']=currency_obj.compute(cr, uid, company_currency, current_currency,credit, round=False, context=context)
                                            move_line_obj.create(cr,uid,move_line,context=context)
                                            move_line_counterpart = {
                                                'journal_id': voucher.journal_id.id,
                                                'period_id': voucher.period_id.id,
                                                'name': _('change')+': '+(line.name or '/'),
                                                'account_id': tax.account_id.id,
                                                'move_id': int(new_move),
                                                'amount_currency': 0.0,
                                                'partner_id': voucher.partner_id.id,
                                                'currency_id': line.move_line_id and (company_currency <> current_currency and current_currency) or False,
                                                'quantity': 1,
                                                'debit': credit,
                                                'credit': debit,
                                                'date': line.voucher_id.date,
                                            }
                                            if company_currency!=current_currency:
                                                move_line['amount_currency']=currency_obj.compute(cr, uid, company_currency, current_currency,credit, round=False, context=context)
                                            move_ids.append(move_line_obj.create(cr,uid,move_line_counterpart,context=context))
                                for mov_line in invoice.move_id.line_id:
                                    if mov_line.account_id.id==tax.account_id.id:
                                        move_ids.append(mov_line.id)
                                if line.amount==line.amount_original:
                                    self.pool.get('account.move.line').reconcile(cr, uid, move_ids, 'manual', writeoff_acc_id=tax.account_id.id, writeoff_period_id=voucher.period_id.id, writeoff_journal_id=voucher.journal_id.id)
                                else:
                                    self.pool.get('account.move.line').reconcile_partial(cr, uid, move_ids, 'manual', context)

        return res
account_voucher()