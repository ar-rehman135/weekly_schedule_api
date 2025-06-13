from rest_framework import viewsets, permissions
from .models import TimeSlot
from .serializers import TimeSlotSerializer
from rest_framework.response import Response


class TimeSlotViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing weekly schedule time slots.

    Each time slot represents a period during which specific cameras are active.
    The schedule is organized by days of the week, with each day containing
    multiple time slots.
    """

    queryset = TimeSlot.objects.all()
    serializer_class = TimeSlotSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        # Get all timeslots, ordered by day + start ascending
        queryset = self.get_queryset().order_by("day", "start")

        # Group by day
        grouped = {}
        for day_key, _ in dict(
            self.queryset.model._meta.get_field("day").choices
        ).items():
            grouped[day_key] = []

        for timeslot in queryset:
            day = timeslot.day
            # Serialize single timeslot
            serialized = TimeSlotSerializer(timeslot).data
            grouped[day].append(serialized)

        return Response({"schedule": grouped})
