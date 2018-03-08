# -*- coding: utf-8 -*-
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.translation import gettext, gettext_lazy as _

#import re

def validate_category_name(value):
	forbidden = ['todos', 'especificos', 'especifico', 'retrasados', 'retrasado', 'todo', 'junta de condominio', 'junta', 'juntas', 'propietario', 'propietarios', 'no miembro', 'no miembros', 'no-miembros','arrendatario', 'arrendatarios']
	if (value).lower().strip() in forbidden:
		raise ValidationError(_("This category name is not allowed."))


#DEFINE YOUR VALIDATION METHODS BELOW
# class Validador():
# 	password_regex = RegexValidator(regex=r'^(?=.*[0-9])(?=.*[a-zA-Z])([a-zA-Z0-9]+)$', message="Clave no debe contener espacios en blanco, al menos una letra y un numero")
# 	name_regex = RegexValidator(regex=r'^[a-zA-Z ]*$', 
#         message="Su nombre solo puede contener letras!")
# 	phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', 
#         message="Numero telefonico debe ser grabado de la siguiente forma: '+999999999'. Max 15 digitos.")
# 	def image_valid_extension(self):
# 	    if (not value.name.endswith('.png') or not value.name.endswith('.jpeg') or 
# 	        not value.name.endswith('.gif') or
# 	        not value.name.endswith('.bmp') or
# 	        not value.name or
# 	        not value.name.endswith('.jpg')):
# 	        	raise ValidationError("Archivos permitidos: .jpg, .jpeg, .png, .gif, .bmp")


#user_validator = Validador()

#rif_validator = RegexValidator(regex='^[a-zA-Z0-9]*$',message='Rif Invalido')
