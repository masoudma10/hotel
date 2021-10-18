from django.http import HttpResponseRedirect
from rest_framework import generics
from rest_framework.views import APIView, status
from ..models import *
from django.contrib import messages
from ..settings import END_RESERVATION_DATETIME, START_RESERVATION_DATETIME, TOKENIZE
from django.utils.translation import ugettext_lazy as _
from .serializers import ReservationSerializer, RoomSerializer
from ..email import send_reservation_email
from django.http.response import HttpResponseRedirect, Http404
from rest_framework.response import Response



def get_base_url(request):
    protocol = request.is_secure() and 'https://' or 'http://'
    domain = request.META['HTTP_HOST']
    return protocol + domain


class ReservationList(generics.ListAPIView):
    queryset = Reservation.objects.all()

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user).exclude(
            status=Reservation.BUILDING).order_by('-updated_datetime', 'status')
        return queryset


class CreateReservation(generics.CreateAPIView):
    model = Reservation
    serializer_class = ReservationSerializer


    def get_success_url(self):
        if self.request.GET.get('next'):
            return self.request.GET.get('next')
        return super(CreateReservation, self).get_success_url()

    def get_success_view(self):
        response = HttpResponseRedirect(self.get_success_url())
        response.set_cookie("reservation", str(self.object.pk))
        return response


    def get_serializer_class(self):
        serializer = ReservationSerializer(data=self.request.data)
        return serializer

    def serializer_valid(self, serializer):
        self.object = serializer.save(commit=False)
        self.object.user = self.request.user
        self.object.save()
        if TOKENIZE:
            ReservationToken.objects.create(
                reservation=self.object,
                base_url=get_base_url(self.request))
        send_reservation_email(self.object, self.request.user)

        messages.success(self.request, _('Reservation created'))

        return self.get_success_view()



class FinishReservationView(APIView):

    def get(self, request):
        if not hasattr(request, 'reservation'):
            raise Http404(_("No reservation object started"))

        return Response(request.reservation, status=status.HTTP_200_OK)

    def post(self, request):
        reservation = request.reservation
        reservation.status = reservation.REQUESTED
        reservation.save()
        request.reservation = None
        send_reservation_email(reservation, request.user)

class SimpleProductReservation(generics.CreateAPIView):
    model = Reservation
    form_class = ReservationSerializer
    success_url = "/"
    base_model = None
    amount_field = None
    max_amount_field = None
    extra_display_field = None
    template_name = 'djreservation/simple_reservation.html'
    room_serializer_class = RoomSerializer
    room_form = None


    def get_serializer(self, *args, **kwargs):
        self.room_serializer_class