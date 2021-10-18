from __future__ import unicode_literals
from .views import ProductReservationView
from django.conf.urls import url


class ModelsRegistered(object):
    views = []

    def register(self,
                 base_model,
                 amount_field,
                 extra_display_field=[],
                 view=ProductReservationView
                 ):

        self.views.append(
            view(
                base_model,
                amount_field,
                extra_display_field
            )
        )

    def get_urls(self):
        dev = []

        for i, view in enumerate(self.views):
            appname = view.base_model._meta.app_label
            modelname = view.base_model.__class__.__name__
            dev.append(
                url("regRoom/%s/%s/(?P<modelpk>)\d+$" % (
                    appname, modelname),
                    self.views[i].as_view(),
                    name="reserve_room_%s_%s" % (
                    appname, modelname))

            )
        return dev


register_room = ModelsRegistered()