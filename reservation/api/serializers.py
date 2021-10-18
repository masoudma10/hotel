from rest_framework import serializers
from ..models import Reservation, Room
from django.utils.translation import ugettext_lazy as _



class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = '__all__'


    def validate(self, attrs):
        if hasattr(self, 'request'):
            if hasattr(self.request, "reservation"):
                raise serializers.ValidationError(
                    _("You can not create reservation with active reservation"))
            super(ReservationSerializer, self).validate(attrs)



class RoomSerializer(serializers.ModelSerializer):
    model_instance = serializers.CharField()
    available_amount = serializers.FloatField()


    class Meta:
        model = Room
        fields = ['amount',]


    def validate(self, attrs):
        cleaned_data = super(RoomSerializer, self).validate(attrs)

        if cleaned_data['amount'] <= 0:
            raise serializers.ValidationError(
                _("You amount correct, requested 0 or negative value"))

        if cleaned_data['amount'] > cleaned_data['available_amount']:
            raise serializers.ValidationError(
                _("You requested more than product available"))