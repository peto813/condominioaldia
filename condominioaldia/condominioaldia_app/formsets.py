from django.forms import formset_factory
from condominioaldia_app.forms import Mass_Email_Form

Mass_MarkettingFormset = formset_factory(Mass_Email_Form)