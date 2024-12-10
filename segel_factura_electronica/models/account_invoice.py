# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
import datetime, math
import re
import json
from odoo.exceptions import ValidationError, UserError


class accountInvoice(models.Model):
    _inherit = 'account.invoice'

    cdc = fields.Char(string='CDC')

    qr_fe = fields.Char(string='ekuatia', readonly=True)

    #qr_image_fe = fields.Binary(string='QR', readonly=True)

    descuento = fields.Integer(string="Descuento (%)")

    limite_excedido = fields.Boolean(string="Limite Excedido", compute="get_lineas", default=False)

    descripcion_detalle = fields.Char(default=" Factura según expediente N° ", readonly=True)

    detalle_pago = fields.Char(string="Descripción del Pago")

    monto_pago = fields.Monetary(string="Monto")

    comisionIVA = fields.Integer(compute='_comisionIVA')

    barcode = fields.Char(compute='_barcode')

    fecha_letras = fields.Char(compute='_fechaLetras')

    monto_interes = fields.Monetary('Intereses Acumulados', compute='_get_intereses_acumulados')

    factura_mora = fields.Many2one(
        'account.invoice', string='Factura mora', copy=False)

    factura_origen_mora = fields.Many2one(
        'account.invoice', string='Factura origen', copy=False)

    facturas_origen_mora = fields.Many2many('account.invoice', 'facturas_origen_multiples', 'id',
                                            'facturas_origen_mora', string="Facturas Origen", copy=False)
    dias_atraso = fields.Integer(string="Días de atraso", compute="_get_intereses_acumulados")

    desactivar_mora = fields.Boolean(default=False, copy=False)

    interes_diario_base = fields.Monetary(
        string="Interés por Dia", compute='_get_intereses_acumulados')

    cantidadImpresiones = fields.Integer(default=0, copy=False)

    autorizado = fields.Boolean(string="Autorizado por Jefe de Tesoreria", default=False)

    state = fields.Selection(selection_add=[('cancelation', 'Anulado por N/C')])

    json_enviado = fields.Text(string="JSON Enviado")

    status_invoice = fields.Char(string="Estado e-Invoice", readonly=True)


    # retencion30 = fields.Boolean(string="Pago Retencion 30%",default=False, copy=False)

    # retencion70 = fields.Boolean(string="Pago Retencion 70%", default=False, copy=False)

    def autorizar_factura(self):
        for record in self:
            if record.autorizado == True:
                raise UserError("La Factura ya esta autorizada")
            else:
                record.autorizado = True
                record.message_post(body="Factura autorizada por el usuario.")

    def simuladorSifen(self):
        for this in self:
            fechaHora = this.date_invoice  # Fecha de Factura
            fechaVencimiento = this.date_due  # Fecha de Vencimiento
            status_invoice = this.state
            if (fechaVencimiento > fechaHora):
                tipo_factura = 'CRED'
                this.obtenerQr()
            elif (fechaVencimiento == fechaHora and status_invoice != 'paid' ):
                raise ValidationError("Una factura contado debe estar en estado pagado para emitir el Documento Electronico")
            else:
                raise ValidationError("Verifique fechas de factura, fecha factura o fecha vencimiento no pueden ser nulos")

    def eliminarCaracteresEspeciales(self, texto):
        return re.sub(r'[^\w\s]', ' ', texto).replace('\n', ' ').replace('\t', ' ')

    def verJsonNotaCredito(self):
        import json
        from datetime import datetime
        import pytz

        # produccion FE
        contribuyenteid_producction = 5
        pass_producction = "3bd7e0750d20f5e6b2d6a462e44e312c450bbf841e20c46b86c2bfef831ce566"

        # Test FE
        contribuyenteid_test = 4
        pass_test = "6afd034014b2c82a0b0976319dc13101326456399f878d490073ec89e023eeeb"
        fecha_ini_test = "2024-01-02T08:51:00-03:00"
        timbrado_test = "16930296"

        for this in self:
            id_factura_origen = self.refund_invoice_id
            num_factura = this.fake_number
            separado = num_factura.split("-")
            establecimiento = separado[0]
            puntoExpedicion = separado[1]
            documentoNro = separado[2]
            # numero de factura origen
            fechaHora = this.date_invoice  # Fecha de Factura
            server_timezone = pytz.timezone('America/Argentina/Buenos_Aires')
            current_datetime = datetime.now(server_timezone)
            formatted_datetime = current_datetime.strftime('T%H:%M:%S%z')
            formatted_date = fechaHora.strftime('%Y-%m-%d')
            final_date = formatted_date + formatted_datetime
            razon_social = this.partner_id.parent_name

            ruc = this.partner_id.vat
            rucSplit = ruc.split("-")
            docNro = rucSplit[0]
            dv = rucSplit[1]
            detalle_list = this.calculate_detalle()

            payload = json.dumps({
                "contribuyente": {
                    "contribuyenteid": contribuyenteid_producction,
                    "pass": pass_producction,
                },
                "timbrado": {
                    "timbrado": timbrado_test,
                    "establecimiento": establecimiento,
                    "puntoExpedicion": puntoExpedicion,
                    "documentoNro": documentoNro,
                    "fecIni": fecha_ini_test
                },
                "sucursal": "Central",
                "receptor": {
                    "docNro": docNro,
                    "dv": dv,
                    "razonSocial": razon_social
                },
                "fecha": final_date,
                "notaCreditoDebito": {
                    "motivoEmision": 1

                },
                "docAsociados": this.docAsociadosNotaCredito(id_factura_origen),
                "detalles": detalle_list,
                "totalComprobante": this.amount_total
            })
            raise ValidationError(payload)

    def docAsociadosNotaCredito(self, id_factura_origen):
        from datetime import datetime, date
        import pytz
        doc_asociados = []
        if id_factura_origen:
            date_object = id_factura_origen.date_invoice
            comparison_date = date(2024, 2, 1)
            if (date_object < comparison_date):
                num_factura = id_factura_origen.fake_number
                separado = num_factura.split("-")
                establecimiento = separado[0]
                puntoExpedicion = separado[1]
                documentoNro = separado[2]
                fechaHora = date_object  # Fecha de Factura
                server_timezone = pytz.timezone('America/Argentina/Buenos_Aires')
                current_datetime = datetime.now(server_timezone)
                formatted_datetime = current_datetime.strftime('T%H:%M:%S%z')
                formatted_date = fechaHora.strftime('%Y-%m-%d')
                final_date = formatted_date + formatted_datetime
                documentos = {
                    "tipo": 2,
                    "timbrado": id_factura_origen.journal_id.timbrados_ids.name,
                    "establecimiento": establecimiento,
                    "puntoExpedicion": puntoExpedicion,
                    "docNro": documentoNro,
                    "tipoDocAsociado": "1",
                    "fechaEmision": final_date,
                }
                doc_asociados.append(documentos)
            else:
                documentos = {
                    "tipo": 1,
                    "cdc": id_factura_origen.cdc,
                    "tipoDocAsociado": "1"
                }
                doc_asociados.append(documentos)
            return doc_asociados
        else:
            raise ValidationError("No se puede generar JSON para Sifen, la nota de credito no tiene una factura asociada")


    def obtenerQr(self):
        import os
        import qrcode
        import base64

        qr_value = 'https://ekuatia.set.gov.py/consultas/qr?nVersion=150&Id=014444440170010010014528'
        cdc_value = '01444444017001001001452822017012515873260988'
        estado_factura_value = 'Enviado a Sifen'

        # Create a QR code instance
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )

        # Add data to the QR code
        qr.add_data(qr_value)
        qr.make(fit=True)

        # Create an image from the QR code instance
        img = qr.make_image(fill_color="black", back_color="white")

        # Specify the directory for saving the image
        directory = "images/"

        # Ensure that the directory exists; if not, create it
        os.makedirs(directory, exist_ok=True)

        # Save the image
        name = cdc_value + ".png"
        img_path = os.path.join(directory, name)
        img.save(img_path)

        # Read the image as binary data and encode it
        with open(img_path, "rb") as img_file:
            img_binary = base64.b64encode(img_file.read())

        # Update the object properties
        self.update({
            'qr_fe': qr_value,
            'cdc': cdc_value,
            'status_invoice': estado_factura_value,
            #'qr_image_fe': img_binary,
        })
        self.read_properties_file()


    def get_lineas(self):
        for this in self:
            lineas_para_reporte = []
            for linea in this.invoice_line_ids:
                lineas_para_reporte += this.format_linea(linea.name)
            if this.comment:
                lineas_para_reporte += this.format_linea(this.comment)
            lineas = math.ceil(len(lineas_para_reporte))
            if this.comment:
                lineas += 1
            if lineas >= 20:
                this.limite_excedido = True
            else:
                this.limite_excedido = False
            return lineas

    def format_linea(self, linea=False):
        limite = int(self.env['ir.config_parameter'].sudo().get_param('interfaces_facturas.limite_caracteres'))  # 27
        if not linea:
            return False
        else:
            linea_limitada = []
            linea_actual = ''
            c = 0
            for i in linea:
                c += 1
                linea_actual += i
                if c == limite:
                    linea_limitada.append(linea_actual)
                    linea_actual = ''
                    c = 0
            if linea_actual: linea_limitada.append(linea_actual)
            return linea_limitada

    def read_properties_file(file_path):
        properties = {}

        with open(file_path, 'r') as file:
            for line in file:
                # Ignore comments and empty lines
                if line.strip() == '' or line.startswith('#'):
                    continue
                # Split the line into key and value
                key, value = line.strip().split('=')

                # Remove leading and trailing whitespaces
                key = key.strip()
                value = value.strip()

                # Store the key-value pair in the dictionary
                properties[key] = value

        return properties

    # Example usage
    # file_path = 'segel_factura_electronica/factura_electronica.properties'
    # config_properties = read_properties_file(file_path)

    # Now you can access the configuration settings
    # for key, value in config_properties.items():
    #     print(f'{key}: {value}')

    @api.multi
    def cancelacion_interna(self):
        canceled = None
        canceled = self.filtered(lambda inv: inv.state != 'cancel').action_cancel()
        return canceled

    def action_send_efactura(self):
        import requests
        import json
        from datetime import datetime
        import pytz

        # produccion FE
        contribuyenteid_producction= 5
        pass_producction= "3bd7e0750d20f5e6b2d6a462e44e312c450bbf841e20c46b86c2bfef831ce566"

        # Test FE
        contribuyenteid_test= 4
        pass_test= "6afd034014b2c82a0b0976319dc13101326456399f878d490073ec89e023eeeb"
        fecha_ini_test = "2023-11-06T08:51:00-03:00"
        timbrado_test = "80000638"

        # Authenticate
        for this in self:
            url = "http://68.183.118.119:8080/fcws/factura"
            num_factura = this.fake_number
            separado = num_factura.split("-")
            establecimiento = separado[0]
            puntoExpedicion = separado[1]
            documentoNro = separado[2]
            fechaHora = this.date_invoice  # Fecha de Factura
            fechaVencimiento = this.date_due  # Fecha de Vencimiento
            server_timezone = pytz.timezone('America/Argentina/Buenos_Aires')
            current_datetime = datetime.now(server_timezone)
            formatted_datetime = current_datetime.strftime('T%H:%M:%S%z')
            formatted_date = fechaHora.strftime('%Y-%m-%d')
            final_date = formatted_date + formatted_datetime
            razon_social = this.partner_id.name

            ruc = this.partner_id.vat
            rucSplit = ruc.split("-")
            if len(rucSplit) > 1:
                docNro = rucSplit[0]
                dv = rucSplit[1]
                qty = 1
            else:
                docNro = ruc
                dv = None
                qty = 0
            #docNro = rucSplit[0]
            #qty = 0
            if this.partner_id.obviar_validacion is True:
                dv = None
                qty = 0
            if this.partner_id.es_extranjero is True:
                qty = 2
            monto_pago = this.monto_pago
            detalle_list = this.calculate_detalle()
            if (not fechaHora):
                raise UserError(_('No se puede dejar en blanco Fecha Factura'))

            receptor = None
            if (fechaVencimiento > fechaHora):
                tipo_factura = 'CRED'
            elif (fechaVencimiento == fechaHora):
                tipo_factura = 'CON'
            elif (fechaVencimiento is null or fechaHora is null):
                raise ValidationError(
                    "Verifique fechas de factura, fecha factura o fecha vencimiento no pueden ser nulos")
            if (docNro is not None and qty == 1):
                receptor = {
                    "docNro": docNro,
                    "dv": dv,
                    "razonSocial": razon_social
                }
            elif(docNro is not None and qty > 1):
                receptor = {
                    "tipoDocumento": "3",
                    "docNro": ruc,
                    "razonSocial": razon_social
                }
            elif (docNro is not None and qty == 0):
                receptor = {
                    "tipoDocumento": "1",
                    "docNro": docNro,
                    "razonSocial": razon_social
                }
            else:
                receptor = {
                    "tipoDocumento": "5",
                    "docNro": "0",
                    "razonSocial": "Sin Nombre"
                }

            if tipo_factura == 'CON':
                # if this.state == 'paid':
                payload = json.dumps({
                    "contribuyente": {
                        "contribuyenteid": contribuyenteid_producction,
                        "pass": pass_producction,
                    },
                    "timbrado": {
                        "timbrado": "16930296",
                        "establecimiento": establecimiento,
                        "puntoExpedicion": puntoExpedicion,
                        "documentoNro": documentoNro,
                        "fecIni": "2024-01-02T13:26:00-03:00"
                    },
                    "sucursal": "Central",
                    "receptor": receptor,
                    "fecha": final_date,
                    "condicionOperacion": {
                        "condicion": 1,
                        "tiposPagos": [
                            {
                                "tipoPagoCodigo": 1,
                                "monto": this.amount_total
                            }
                        ]
                    },
                    "detalles": detalle_list,
                    "totalComprobante": this.amount_total
                })
                headers = {
                    'Content-Type': 'application/json'
                }
                print("Json enviado: ", payload)
                # else:
                #     raise UserError("No se puede validar una factura contado sin pago, favor registre el pago")
                #     this.button_pago()
            elif (tipo_factura == 'CRED'):
                payload = json.dumps({
                    "contribuyente": {
                        "contribuyenteid": contribuyenteid_producction,
                        "pass": pass_producction,
                    },
                    "timbrado": {
                        "timbrado": "16930296",
                        "establecimiento": establecimiento,
                        "puntoExpedicion": puntoExpedicion,
                        "documentoNro": documentoNro,
                        "fecIni": "2024-01-02T13:26:00-03:00"
                    },
                    "sucursal": "Central",
                    "receptor": receptor,
                    "fecha": final_date,
                    "condicionOperacion": {

                        "condicion": 2,

                        "operacionTipo": 1,

                        "plazoCredito": this.payment_term_id.name

                    },
                    "detalles": detalle_list,
                    "totalComprobante": this.amount_total
                })
                headers = {
                    'Content-Type': 'application/json'
                }
                print("Json enviado: ", payload)
            self.guardar_json_enviado(payload)
            response = requests.request("POST", url, headers=headers, data=payload)

            # Check response
            if response.status_code == 401:
                print("Error 401")
                raise ValidationError(
                    "Error de Autenticación")
                continue

            # Load eFactura Record
            print("Response status : ", response.status_code)
            if response.status_code == 201 or response.status_code == 200:
                try:
                    data = json.loads(response.text)
                    qr_value = data.get('qr', '')
                    cdc_value = data.get('cdc', '')
                    estado_factura_value = "Enviado a Sifen"
                    print("Respuesta Servicio envio Sifen: ", response.text)
                    result = json.loads(response.text)
                    self.update({
                        'qr_fe': qr_value,
                        'cdc': cdc_value,
                        'status_invoice': estado_factura_value,
                    })
                except json.JSONDecodeError as e:
                    print("Error decoding JSON response:", str(e))
                    raise ("Error decoding JSON response:", str(e))
            else:
                print("El resultado del envío no fue exitoso.")
                print("Response status : ", response.status_code)
                print("Response : ", response.text)
                raise ValidationError(payload)

    def guardar_json_enviado(self, payload):
        if payload:
            # json_data = json.dumps(payload)  # Convertir a string JSON si es necesario
            self.json_enviado = payload  # Guardar directamente en el campo JSON
            # print("Json enviado: ", json_data)
        else:
            raise ValueError("El payload debe ser un diccionario válido.")

    def calculate_detalle(self):
        detalle = []
        for this in self:
            for line in this.invoice_line_ids:
                product_code = line.product_id
                descripcion = this.eliminarCaracteresEspeciales(line.name)
                cantidad = line.quantity
                iva = 0
                afectacion = 0
                proporcion = 0
                if (not product_code):
                    if (descripcion and cantidad):
                        print(line.invoice_line_tax_ids)
                        if (line.invoice_line_tax_ids and line.invoice_line_tax_ids[0].amount == 10):
                            iva = 10
                            afectacion = 1
                            proporcion = 100
                        elif (line.invoice_line_tax_ids and line.invoice_line_tax_ids[0].amount == 0):
                            iva = 0
                            afectacion = 3
                            proporcion = 0
                        invoice_line = {
                            'itemCodigo': "AS",  # arrastre de saldo
                            'cantidad': line.quantity,
                            'itemDescripcion': this.eliminarCaracteresEspeciales(line.name),
                            'precioUnitario': int(line.price_unit),
                            'afectacionTributaria': afectacion,
                            'proporcionIVA': proporcion,
                            'tasaIVA': iva
                        }
                        detalle.append(invoice_line)
                elif product_code:
                    print(line.invoice_line_tax_ids)
                    if (line.invoice_line_tax_ids and line.invoice_line_tax_ids[0].amount == 10):
                        iva = 10
                        afectacion = 1
                        proporcion = 100
                    elif (line.invoice_line_tax_ids and line.invoice_line_tax_ids[0].amount == 0):
                        iva = 0
                        afectacion = 3
                        proporcion = 0
                    invoice_line = {
                        'itemCodigo': line.product_id.id,
                        'cantidad': line.quantity,
                        'itemDescripcion': this.eliminarCaracteresEspeciales(line.name),
                        'precioUnitario': int(line.price_unit),
                        'afectacionTributaria': afectacion,
                        'proporcionIVA': proporcion,
                        'tasaIVA': iva
                    }
                    detalle.append(invoice_line)
        print(detalle)
        return detalle

    def getFormasPago(self):
        tiposPagos = []
        for this in self:
            payments = this.payment_ids
            for payment in payments:
                payment_name = payment.tipo_pago
                if payment_name == 'cheque':
                    pagos = {
                        'monto': payment.amount,
                        'tipoPagoCodigo': 2,
                        'cheque': this.getChequeDetails()
                    }
                elif(payment_name == 'efectivo'):
                    pagos = {
                        'monto': payment.amount,
                        'tipoPagoCodigo': 1,
                    }
                elif (payment_name == 'transferencia'):
                    pagos = {
                        'monto': payment.amount,
                        'tipoPagoCodigo': 5,
                    }


    def getChequeDetails(self):
        detalle = []
        for this in self:
            cheques = this.payment_ids
            for cheque in cheques:
                cheq = {
                    'banco': cheque.bank_id.name,
                    'nro': cheque.nro_cheque
                }
                detalle.append(cheq)
                print(detalle)
        return detalle





    def _fechaLetras(self):
        meses = [
            'Enero',
            'Febrero',
            'Marzo',
            'Abril',
            'Mayo',
            'Junio',
            'Julio',
            'Agosto',
            'Setiembre',
            'Octubre',
            'Noviembre',
            'Diciembre',
        ]
        for this in self:
            if this.date_invoice:
                fecha_letras = this.date_invoice.strftime("%d de __mes__ de %Y")
                fecha_letras = fecha_letras.replace('__mes__', meses[this.date_invoice.month - 1])
                this.fecha_letras = fecha_letras
            else:
                this.fecha_letras = this.date_invoice

    def cantImpresiones(self):
        for this in self:
            if this.state == 'draft' or this.state == 'cancel':
                return True
            if this.type == 'out_invoice' and this.state != 'draft':
                this.cantidadImpresiones = this.cantidadImpresiones + 1
                if this.cantidadImpresiones > 6:
                    return True
                else:
                    return False

    def resetearImpresiones(self):
        for this in self:
            this.cantidadImpresiones = 0

    def _comisionIVA(self):
        for this in self:
            if this.amount_total <= 750000:
                this.comisionIVA = 8250
            elif 750000 < this.amount_total <= 2000000:
                this.comisionIVA = 11000
            elif 2000000 < this.amount_total <= 8000000:
                this.comisionIVA = 16500
            elif 8000000 < this.amount_total <= 15000000:
                this.comisionIVA = 19250
            elif 15000000 < this.amount_total <= 30000000:
                this.comisionIVA = 22000
            elif 30000000 < this.amount_total <= 40000000:
                this.comisionIVA = 27500
            elif 40000000 < this.amount_total <= 50000000:
                this.comisionIVA = 33000
            elif 50000000 < this.amount_total <= 60000000:
                this.comisionIVA = 38500
            elif this.amount_total > 60000000:
                this.comisionIVA = 71500

    def _barcode(self):
        for this in self:
            num_factura = this.fake_number
            num_factura_array = num_factura.split("-")
            for index, elemento in enumerate(num_factura_array):
                # print(index)
                if len(elemento) < 3:
                    num_factura_array[index] = '0' + elemento
            num_factura_string = ''.join(num_factura_array)
            ##########################################################
            monto_total = str(this.amount_total + this.comisionIVA)
            importe_total_string = monto_total.replace('.', '') + "0"
            if len(importe_total_string) < 11:
                for digit in range(len(importe_total_string), 11):
                    importe_total_string = '0' + importe_total_string
            ##########################################################
            comisionIVA = str(this.comisionIVA)
            comisionIVA = comisionIVA + '00'
            # print(comisionIVA)
            if len(comisionIVA) < 7:
                for digit in range(len(comisionIVA), 7):
                    comisionIVA = '0' + comisionIVA
            ##########################################################
            fecha_deseada_string = ""
            if this.date_due:
                fecha_deseada_string = datetime.datetime.strftime(this.date_due, '%Y%m%d')
            ##########################################################

            barcode = '01114' + num_factura_string + fecha_deseada_string + importe_total_string + comisionIVA
            suma = 0
            for digit in range(1, len(barcode)):
                if int(digit) % 2 == 0:
                    producto = int(barcode[digit]) * 1
                else:
                    producto = int(barcode[digit]) * 3
                suma = suma + producto
            resto = suma % 10

            digito_verificador = 10 - resto

            if digito_verificador == 10:
                digito_verificador = 0

            this.barcode = barcode + str(digito_verificador)

    def button_wizard_pago(self):
        if self.type == 'out_invoice':
            view = self.env.ref('intn_intereses_mora.wizard_pago_form')
            return {
                'name': 'Registrar pago de intereses',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'intn_intereses_mora.wizard_pago',
                'context': {'default_factura_origen': self.id},
                'view_id': view.id,
                'target': 'new',
            }

    def get_factura_mora_pagada(self):
        for i in self:
            if (i.factura_mora and ((i.factura_mora.state == 'paid' and i.factura_mora.state != 'cancel') or (
                    i.factura_mora.state == 'open' and i.factura_mora.date_invoice != i.factura_mora.date_due))) or i.desactivar_mora or i.partner_id.es_entidad_estado:
                return True
            return False

    def action_invoice_cancel(self):
        for i in self:
            if i.factura_origen_mora:
                i.factura_origen_mora.write({'factura_mora': None})
            res = super(accountInvoice, i).action_invoice_cancel()
            return res

    @api.model
    def calcular_intereses(self, invoice, date_payment):
        dias_atraso = (date_payment - invoice.date_due).days
        # fecha_exonerada = datetime.strptime('2017-01-01', '%Y-%m-%d').date()
        # if invoice.date_due < fecha_exonerada:
        #     dias_atraso = 0
        if dias_atraso > 0 and not invoice.get_factura_mora_pagada():
            porcentaje_mensual = float(
                self.sudo().env['ir.config_parameter'].get_param('interes_mora_parameter'))
            interes_mensual_base = invoice.amount_total_company_signed * porcentaje_mensual / 100
            interes_diario_base = float(interes_mensual_base / 30)
            interes = dias_atraso * interes_diario_base
            return {
                'interes': interes,
                'dias_atraso': dias_atraso,
                'interes_diario_base': interes_diario_base
            }
        else:
            return {
                'interes': 0,
                'dias_atraso': 0
            }

    def _get_intereses_acumulados(self):
        for invoice in self:
            if invoice.state == 'open':
                data = invoice.calcular_intereses(
                    invoice, date_payment=fields.Date.today())
                invoice.monto_interes = data.get('interes')
                invoice.dias_atraso = data.get('dias_atraso')
                invoice.interes_diario_base = data.get('interes_diario_base')
            else:
                invoice.monto_interes = 0
                invoice.dias_atraso = 0

    def button_pago(self):
        for i in self:
            if i.monto_interes > 0:
                raise exceptions.ValidationError(
                    'No se puede registrar un pago a una factura con intereses por mora. Primero registre la factura de la mora')
            return super(accountInvoice, i).button_pago()

    @api.model
    def button_pago_multi(self, facturas):
        for i in facturas:
            if i.monto_interes > 0:
                raise exceptions.ValidationError(
                    'No se puede registrar un pago a una factura con intereses por mora. Primero registre la factura de la mora')
            return super(accountInvoice, i).button_pago_multi(facturas)

    @api.model
    def button_pago_multi_intereses(self, facturas):
        if facturas[0].type == 'out_invoice':
            flag = self.env.user.has_group(
                'intn_intereses_mora.grupo_facturas_mora')
            if flag:
                view = self.env.ref('intn_intereses_mora.wizard_pago_form')
                return {
                    'name': 'Registrar pago de intereses',
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'intn_intereses_mora.wizard_pago',
                    'context': {'default_facturas_origen': [(6, 0, facturas.ids)]},
                    'view_id': view.id,
                    'target': 'new',
                }
            else:
                raise UserError(
                    'Su usuario no cuenta con permisos para registrar facturas por mora')

    def pago_multi_intereses(self, facturas):
        if self.type == 'out_invoice':
            flag = self.env.user.has_group(
                'intn_intereses_mora.grupo_facturas_mora')
            if flag:
                view = self.env.ref('intn_intereses_mora.wizard_pago_form')
                return {
                    'name': 'Registrar pago de intereses',
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'intn_intereses_mora.wizard_pago',
                    'context': {'default_facturas_origen': [(6, 0, self.ids)]},
                    'view_id': view.id,
                    'target': 'new',
                }
            else:
                raise UserError(
                    'Su usuario no cuenta con permisos para registrar facturas por mora')

    @api.multi
    def action_invoice_cancel(self):
        from datetime import datetime
        canceled = None
        for this in self:
            cdc = this.cdc
            # fecha_factura = datetime.strptime(this.date_invoice, "%Y-%m-%d").date()
            # fecha_limite = datetime.strptime('2024-02-28', "%Y-%m-%d").date()
            # estado = this.estado_factura_electronica
            # Verifica que fecha_factura sea una fecha válida
            if (cdc == ''):
                # raise UserError('No de puede anular factura, debe generar nota de credito Electronico')
                canceled = self.filtered(lambda inv: inv.state != 'cancel').action_cancel()
            elif(cdc != ''):
                this.cancelarDocumento(cdc)
                canceled = self.filtered(lambda inv: inv.state != 'cancel').action_cancel()
                # else:
                #     raise UserError('No se puede cancelar la factura si no posee CDC o no esta Aprobada por Sifen')
        return canceled

    def arregloNotasCredito(self):
        lista = [112425, 112400, 112407, 112664, 112660, 112666, 112711, 112890, 113362, 113400, 113431, 113398, 113432,
                 113394, 113676, 113613, 113653, 113641, 113649, 113650, 113664, 113642, 113645, 113656, 113657, 113658,
                 113667, 113669, 113670, 113672, 113675, 113673, 113595, 113619, 113623, 113633, 113651, 113624, 113621,
                 113655, 113659, 113628, 113630, 113632, 113629, 113654, 113638, 113639, 113848, 114002, 114077, 114157,
                 114132, 114096, 114093, 114081, 114084, 114269, 114240, 114249, 114214, 114251, 114216, 114190, 114244]
        for consulta in lista:
            id_factura = consulta
            cdc = id_factura.cdc
            self.verificarEstadoEfacturaLista(cdc)


    def verificarEstadoEfacturaLista(self, cdc):
        import requests
        import json
        for this in self:
            qty1 = 0
            qty2 = 0
            url = "http://68.183.118.119:8080/fcws/consultar/comprobante/"
            if cdc:
                url_final = url + cdc
                response = requests.get(url_final)
            else:
                raise ValidationError("No existe CDC no se puede obtener estado")
            # Check response
            if response.status_code == 401:
                print("Error 401")
                raise ValidationError("Error de Autenticación ")
                continue
            # Load eFactura Record
            print("Response status : ", response.status_code)
            if response.status_code == 201 or response.status_code == 200:
                try:
                    data = json.loads(response.text)
                    estado = data["estado"]
                    respuesta = data["respuesta"]
                    self.update({
                        'status_invoice': estado,
                    })
                    if respuesta == Aprobado:
                        qty1 = qty1 + 1
                    else:
                        qty2 = qty2 + 1
                    raise ValidationError("Cantidad de aprobados: " + str(qty1) + " Rechazadas: " + str(qty2))
                except json.JSONDecodeError as e:
                    raise ("Error decoding JSON response:", str(e))
            else:
                raise ValidationError(response.text)

    def verificarEstadoEfactura(self):
        import requests
        import json
        for this in self:
            url = "http://68.183.118.119:8080/fcws/consultar/comprobante/"
            if self.cdc:
                url_final = url + self.cdc
                response = requests.get(url_final)
            else:
                raise ValidationError("No existe CDC no se puede obtener estado")
            # Check response
            if response.status_code == 401:
                print("Error 401")
                raise ValidationError("Error de Autenticación ")
                continue
            # Load eFactura Record
            print("Response status : ", response.status_code)
            if response.status_code == 201 or response.status_code == 200:
                try:
                    data = json.loads(response.text)
                    estado = data["estado"]
                    respuesta = data["respuesta"]
                    if respuesta:
                        status = estado + " - " + respuesta
                    else:
                        status = estado + " - Pendiente de Aprobacion"
                    return self.update({
                        'status_invoice': status,
                    })
                    # if respuesta:
                    #     raise ValidationError(estado + " - " + respuesta)
                    # else:
                    #     raise ValidationError
                    # (estado + " - Pendiente de Aprobacion")
                except json.JSONDecodeError as e:
                    raise ("Error decoding JSON response:", str(e))
            else:
                raise ValidationError(response.text)

    def button_pago(self):
        if self.type == 'out_invoice':
            flag = self.env.user.has_group(
                'grupo_account_payment.grupo_cobrador')
            if flag:
                view = self.env.ref(
                    'grupo_account_payment.grupo_account_payment_form_view')
                return {
                    'name': 'Registrar pago',
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'grupo_account_payment.payment.group',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    # 'target': 'new',
                    'context': {'default_payment_type': 'inbound', 'default_partner_id': self.partner_id.id,
                                'default_invoice_ids': self.ids},
                }
            else:
                raise UserError(
                    'Su usuario no cuenta con permisos para registrar pagos')
        elif self.type == 'in_invoice':
            flag = self.env['res.users'].has_group(
                'grupo_account_payment.grupo_orden_pago')
            if flag:
                view = self.env.ref(
                    'grupo_account_payment.grupo_account_payment_orden_form_view')
                return {
                    'name': 'Registrar pago',
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'grupo_account_payment.payment.group',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    # 'target': 'new',
                    'context': {'default_payment_type': 'outbound', 'default_partner_id': self.partner_id.id,
                                'default_invoice_ids': [(4, self.id, 0)]},
                }
            else:
                raise UserError(
                    'Su usuario no cuenta con permisos para registrar órdenes de pago')

    def generarNotaCredito(self):
        import requests
        import json
        from datetime import datetime
        import pytz

        # produccion FE
        contribuyenteid_producction = 5
        pass_producction = "3bd7e0750d20f5e6b2d6a462e44e312c450bbf841e20c46b86c2bfef831ce566"

        # Test FE
        contribuyenteid_test = 4
        pass_test = "6afd034014b2c82a0b0976319dc13101326456399f878d490073ec89e023eeeb"
        fecha_ini_test = "2024-01-02T08:51:00-03:00"
        timbrado_test = "16930296"

        for this in self:
            url = "http://68.183.118.119:8080/fcws/notacredito"
            id_factura_origen = self.refund_invoice_id
            num_factura = this.fake_number
            separado = num_factura.split("-")
            establecimiento = separado[0]
            puntoExpedicion = separado[1]
            documentoNro = separado[2]
            # numero de factura origen
            fechaHora = this.date_invoice  # Fecha de Factura
            server_timezone = pytz.timezone('America/Argentina/Buenos_Aires')
            current_datetime = datetime.now(server_timezone)
            formatted_datetime = current_datetime.strftime('T%H:%M:%S%z')
            formatted_date = fechaHora.strftime('%Y-%m-%d')
            final_date = formatted_date + formatted_datetime
            razon_social = this.partner_id.parent_name

            ruc = this.partner_id.vat
            rucSplit = ruc.split("-")
            docNro = rucSplit[0]
            dv = rucSplit[1]
            detalle_list = this.calculate_detalle()

            payload = json.dumps({
                "contribuyente": {
                    "contribuyenteid": contribuyenteid_producction,
                    "pass": pass_producction,
                },
                "timbrado": {
                    "timbrado": timbrado_test,
                    "establecimiento": establecimiento,
                    "puntoExpedicion": puntoExpedicion,
                    "documentoNro": documentoNro,
                    "fecIni": fecha_ini_test
                },
                "sucursal": "Central",
                "receptor": {
                    "docNro": docNro,
                    "dv": dv,
                    "razonSocial": razon_social
                },
                "fecha": final_date,
                "notaCreditoDebito": {
                    "motivoEmision": 1

                },
                "docAsociados": this.docAsociadosNotaCredito(id_factura_origen),
                "detalles": detalle_list,
                "totalComprobante": this.amount_total
            })
            headers = {'Content-Type': 'application/json'}
            print("Json enviado: ", payload)
            self.guardar_json_enviado(payload)
            response = requests.request("POST", url, headers=headers, data=payload)

            # Check response
            if response.status_code == 401:
                print("Error 401")
                raise ValidationError(
                    "Error de Autenticación ")
                continue

            # Load eFactura Record
            print("Response status : ", response.status_code)
            if response.status_code == 201 or response.status_code == 200:
                try:
                    data = json.loads(response.text)
                    qr_value = data.get('qr', '')
                    cdc_value = data.get('cdc', '')
                    # estado_factura_value = "Enviado a Sifen"
                    print("Respuesta Servicio envio Sifen: ", response.text)
                    result = json.loads(response.text)
                    self.update({
                        'qr_fe': qr_value,
                        'cdc': cdc_value,
                        # 'estado_factura_electronica': estado_factura_value,
                    })
                except json.JSONDecodeError as e:
                    print("Error decoding JSON response:", str(e))
                    raise("Error decoding JSON response:", str(e))
            else:
                print("El resultado del envío no fue exitoso.")
                print("Response status : ", response.status_code)
                print("Response : ", response.text)
                raise ValidationError(response.text)

    @api.multi
    def invoice_validate(self):
        for invoice in self:
            if invoice.partner_id not in invoice.message_partner_ids:
                invoice.message_subscribe([invoice.partner_id.id])

            # Auto-compute reference, if not already existing and if configured on company
            if not invoice.reference and invoice.type == 'out_invoice':
                invoice.reference = invoice._get_computed_reference()

            if invoice.type == 'out_refund':
                self.generarNotaCredito()

            # DO NOT FORWARD-PORT.
            # The reference is copied after the move creation because we need the move to get the invoice number but
            # we need the invoice number to get the reference.
            invoice.move_id.ref = invoice.reference

            if invoice.type == 'out_invoice':
                self.action_send_efactura()
        self._check_duplicate_supplier_reference()

        return self.write({'state': 'open'})

    # def estado_factura_electronica(self):
    #     for this in self:
    #         if this.estado_factura_electronica == 'RECHAZADO':
    #             return True
    #         else:
    #             return False

