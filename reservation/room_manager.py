from __future__ import unicode_literals
from .models import Reservation


def proccess_reservation(obj, differ_obj, change_status):
    if obj.status == Reservation.BUILDING or obj.status == Reservation.REQUESTED:
        return
    if obj.status == Reservation.ACCEPTED:
        accepted_reservation(obj, differ_obj, change_status)
    elif obj.status == Reservation.DENIED:
        denied_reservation(obj, differ_obj, change_status)
    elif obj.status == Reservation.BORROWED:
        borrowed_reservation(obj, differ_obj, change_status)
    elif obj.status == Reservation.RETURNED:
        returned_reservation(obj, differ_obj, change_status)


def denied_reservation(instance, differ_obj, change_status):
    pass


def accepted_reservation(instance, differ_obj, change_status):
    pass


def borrowed_reservation(instance, differ_obj, change_status):
    not_borrowed = []
    if change_status:
        query = instance.rooms_set.filter(borrowed=True)
    else:
        query = instance.rooms_set.filter(pk__in=differ_obj, borrowed=True)
        not_borrowed = instance.rooms_set.filter(
            pk__in=differ_obj, borrowed=False)
    for room in query:
        ref_obj = room.content_object
        setattr(ref_obj, room.amount_field,
                getattr(ref_obj, room.amount_field) - room.amount)
        ref_obj.save()

    for room in not_borrowed:
        ref_obj = room.content_object
        setattr(ref_obj, room.amount_field,
                getattr(ref_obj, room.amount_field) + room.amount)
        ref_obj.save()


def returned_reservation(instance, differ_obj, change_status):

    if change_status:
        query = instance.room_set.filter(borrowed=True)
    else:
        query = instance.room_set.filter(pk_in=differ_obj, borrowed=True)

    for room in query:
        ref_obj = room.content_object
        setattr(ref_obj, room.amount_field, getattr(
            ref_obj, room.amount_field) + room.amount)
        ref_obj.save()