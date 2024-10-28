from odoo import http
import base64
import json
class Etiquetas(http.Controller):
    
    
    @http.route('/usomarca/datamax/print',auth='none',csrf=False)
    def imprimir(self,**kw):

        linea=http.request.env['impresion.etiquetas.lines'].sudo().obtener_linea_solicitud()
        #linea={'nombre':'REGIMIENTO 8 S.A.','numero':'3293676','licencia':'ONC N\xba 400S-026','qr':'HTTP://EINTN.COM/XBRJXSGZQRHYPNJ726STLE5PRM','impresora':'dm2'}
        if linea:
            #if kw.get('test') and kw.get('test')=='1':
            #    b64=self.convertir_base64(linea,test=True)
            #else:
            b64=self.convertir_base64(linea)
            linea_id=http.request.env['impresion.etiquetas.lines'].sudo().browse(int(linea.get('id')))
            if linea_id:
                linea_id.sudo().hecho()
            print(b64)
            res={"base64PrintContent":b64,"printerName":linea.get('impresora'),"commandToPrint":""}
            return json.dumps(res)
        else:
            res={}
            return json.dumps(res)

    def convertir_base64(self,linea,test=False):

        print(linea.get('qr'))
        str_original="\x02L\r\nA1\r\nm\r\nySU8\r\n4W1D22000070004752,MM,A%s\r\nm\r\nySU8\r\n4900S5003320320P007P007%s\r\nm\r\nySU8\r\n4900S5003320470P007P007%s\r\nm\r\nySU8\r\n4900S5003320397P007P007%s\r\nE\r\n\x02qD\r\n"%(linea.get('qr',),linea.get('nombre'),linea.get('numero'),linea.get('licencia'))
        #if not test:
        bytes_original=str_original.encode()
        #else:
        #    bytes_original=b'\x02L\r\nA1\r\nm\r\nySU8\r\n4W1D22000070004752,MM,AHTTP://EINTN.COM/XBRJXSGZQRHYPNJ726STLE5PRM\r\nm\r\nySU8\r\n4900S5003320320P007P007REGIMIENTO 8 S.A.\r\nm\r\nySU8\r\n4900S5003320470P007P0073293676\r\nm\r\nySU8\r\n4900S5003320397P007P007ONC N\xba 400S-026\r\nE\r\n\x02qD\r\n'
        b64_encoded=base64.b64encode(bytes_original)
        return b64_encoded.decode('utf-8')
