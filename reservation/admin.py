from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.template.loader import render_to_string
from django.utils.html import format_html_join
from django.utils.safestring import mark_safe

from .email import send_reservation_email
from .models import Reservation, Observation, Room
from .room_manager import proccess_reservation

# Register your models here.


class ObservationInline(admin.StackedInline):
    model = Observation
    #fields = '__all__'
    extra = 0


def different(l1, l2):
    l1 = list(l1)
    l2 = list(l2)
    for x in l1:
        if x in l2:
            l1.remove(x)
            l2.remove(x)

    for x in l2:
        if x in l1:
            l1.remove(x)
            l2.remove(x)
    return l1 + l2


class ReservationAdmin(admin.ModelAdmin):
    readonly_fields = ["user", "updated_datetime",
                       "list_of_rooms"]

    list_display = [
        'user', 'status', "reserved_start_date", "reserved_end_date"]
    list_filter = ['status']
    search_fields = ['user__firstname', "user__lastname"]
    inlines = [ObservationInline]
    date_hierarchy = 'reserved_start_date'
    fieldsets = (
        (None, {
            'fields': (
                ("user", "status", "updated_datetime"),
                ("reserved_start_date", "reserved_end_date"),
                ("list_of_rooms")
            )
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        readonly =  admin.ModelAdmin.get_readonly_fields(self, request, obj=obj)
        if obj and obj.status == obj.RETURNED:
            readonly= ("user", "status", "updated_datetime",
                "reserved_start_date", "reserved_end_date",
                "list_of_rooms")
        return readonly

    def get_queryset(self, request):
        queryset = admin.ModelAdmin.get_queryset(self, request)
        queryset = queryset.exclude(status=Reservation.BUILDING)
        return queryset

    def list_of_rooms(self, instance):

        return mark_safe(render_to_string(
            'djreservation/rooms_admin_reservation.html',
            {"instance": instance}
        ))

    list_of_rooms.short_description = "list of rooms"

    def save_model(self, request, obj, form, change):
        differ_obj = []
        old_status, room_change = -1, False
        if change:
            old_status = obj.__class__.objects.filter(
                pk=obj.pk).values_list('status')[0][0]
        dev = admin.ModelAdmin.save_model(self, request, obj, form, change)
        if 'djreservation_room_list' in request.POST:
            room_pks = request.POST.getlist("djreservation_room_list")
            old_pks = list(map(lambda x: str(x[0]),
                               obj.room_set.all().filter(
                borrowed=True).values_list("pk")))
            differ_obj = different(room_pks, old_pks)
            if any(differ_obj):
                obj.room_set.all().exclude(
                    pk__in=room_pks).update(borrowed=False)

                obj.rooms_set.all().filter(
                    pk__in=room_pks).update(borrowed=True)
                room_change = True

        change_status = int(old_status) != obj.status
        if room_change or change_status:
            #            send_reservation_email(obj, request.user)
            proccess_reservation(obj, differ_obj, change_status)
        return dev

admin.site.register(Reservation, ReservationAdmin)