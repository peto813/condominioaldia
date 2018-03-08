# -*- coding: utf-8 -*-
import os

def upload_logo_function(instance, filename):
	return os.path.join( '%s/%s/%s/%s' % ( 'user_files', instance.user.id, 'logo', filename ))

def upload_comprobante_rif(instance, filename):
	return os.path.join( '%s/%s/%s/%s' % ( 'user_files', instance.user.id, 'comprobante_rif', filename ))

def upload_pagos_condominio(instance, filename):
    return os.path.join( '%s/%s/%s/%s' % ( 'user_files', instance.factura.condominio.user.id, 'comprobantes_pagos', filename ))

def upload_pagos_inquilino(instance, filename):
    return os.path.join( '%s/%s/%s/%s' % ( 'user_files', instance.inmueble.inquilino.user.id, 'comprobante_pagos', filename ))

def upload_affiliate_payment(instance, filename):
    return os.path.join( '%s/%s/%s/%s' % ( 'user_files', instance.user.id, 'comprobante_pagos_comision', filename ))

def upload_req_carg_inmueble(instance, filename):
    return os.path.join( '%s/%s/%s/%s' % ( 'user_files', instance.condominio.user.id, 'archivo_carg_inmuebles', filename ))