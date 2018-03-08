# -*- coding: utf-8 -*-
from rest_framework.permissions import BasePermission, SAFE_METHODS
from django.contrib.auth import logout
from django.contrib.auth.models import User
from rest_framework.exceptions import APIException
from rest_framework import status
from utils import get_user_type
from condominioaldia_app.models import Inmueble
from django.utils.translation import gettext, gettext_lazy as _


class AbiertoOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.cerrado==False or (request.method in SAFE_METHODS)

class IsreadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

class NoAprobadoCustomException(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = {'non_field_errors':[_("Your condominium is being evaluated by our analysts")]}


class IsRelatedToCondominio(BasePermission):

    def has_object_permission(self, request, view, obj):
        if get_user_type(request) == 'condominio':
            return obj.condominio.pk ==request.user.condominio.pk
        else:
            return obj.inquilino.pk ==request.user.inquilino.pk
        return request.user.is_staff


class InmuebleOwner(BasePermission):
    def has_permission(self, request, view):
        for item in request.data:
            try:
                inmueble = Inmueble.objects.get(id=item)
                response = True if (inmueble.condominio == request.user.condominio or request.user.is_staff) else False
                return response
            except Inmueble.DoesNotExist:
                return False



class IsBancoOwnerOrReadonly(BasePermission): 
    def has_object_permission(self, request, view, obj):
        granted = False
        if request.method in SAFE_METHODS:
            granted = True
        else:
            # Check permissions for write request
            granted = (obj.condominio == request.user.condominio)
        return granted

class IsOwner(BasePermission): 

    # def has_permission(self, request, view):
    #     for item in request.data:
    #         try:
    #             inmueble = Inmueble.objects.get(id=item)
    #             response = True if not inmueble.condominio == request.user.condominio else False
    #             return response
    #         except Inmueble.DoesNotExist:
    #             return False


    def has_object_permission(self, request, view, obj):
        model = obj.__class__.__name__ 
        if model == 'User':
            return  obj.id == request.user.id
        # elif model == 'Inmueble':
        #     return  obj.service.user.id == request.user.id
        # elif model == 'Maintenance':
        #     return  obj.service.user.id == request.user.id
        # elif model == 'Inspections':
        #     return  obj.service.user.id == request.user.id
        # elif model == 'Auction_Products':
        #     return  obj.user.id == request.user.id
        # elif model == 'Services':
        #     return  obj.user.id == request.user.id  
        # elif model == 'Payments':
        #     return  obj.user.id == request.user.id
        # elif model == 'Inspection_Reports':
        #     return  obj.inspection.service.user.id == request.user.id   
        return obj.user == request.user

class InquilinoHasChosenInmueble(BasePermission): 
    def has_permission(self, request, view):
        key = request.session.get('inmueble', None)
        if key:
            return True
        else:
            try:
                condominio = request.user.condominio.pk
                if condominio:
                    return True
            except:
                pass

        return False


class IsCondominio(BasePermission): 
    def has_permission(self, request, view):
        try:
            if request.user.condominio.pk:
                return True
        except:
            return False
        return False

    def has_object_permission(self, request, view, obj):
        #permission = True if (obj.condominio == request.user.condominio or request.method in SAFE_METHODS) else False
        return get_user_type(request.user) =='condominio'

class IsCondominioOrReadonly(BasePermission): 
    def has_permission(self, request, view):
        permission = False
        try:
            permission = True if request.user.condominio or request.user.staff else False
        except:
            permission = True if  request.method in SAFE_METHODS else False
        return permission

    def has_object_permission(self, request, view, obj):
        permission = True if (obj.condominio == request.user.condominio or request.method in SAFE_METHODS) else False
        return permission


class IsOwnerOrReadOnly(BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """

    def has_object_permission(self, request, view, obj):
        model = obj.__class__.__name__ 
        if model == 'Egreso_Condominio' or 'Ingreso_Condominio':
            if request.method in SAFE_METHODS:
                return True
            return  obj.condominio.user == request.user
        return obj.user == request.user

class UsuarioAprobado(BasePermission): 
    message = _('Your condominium is being evaluated by our analysts')
    def has_permission(self, request, view):
        aprobado = False
        # IF USER IS ATTEMPTING A LOGIN
        if request.user.is_anonymous:
            user = User.objects.get(email = request.data['email'])
        else:
            user = request.user

        if hasattr(user, 'condominio'):
            aprobado= user.condominio.aprobado
        elif hasattr(user, 'inquilino'):
            aprobado= True

        if aprobado ==False:
            raise NoAprobadoCustomException
        return aprobado

  #   def has_object_permission(self, request, view, obj):
		# user = request.user
		# aprobado = False
		# try:
		# 	condominio = user.condominio
		# 	user_type = 'condominio'
		# 	aprobado = not condominio.aprobado ==True
		# except:
		# 	pass
		# try:
		# 	inquilino = user.inquilino
		# 	user_type = 'inquilino'
		# 	aprobado = True
		# except:
		# 	pass
		# return aprobado