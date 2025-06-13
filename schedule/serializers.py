from rest_framework import serializers
from .models import TimeSlot
from django.db.models import Q


class TimeSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeSlot
        fields = ("id", "day", "start", "stop", "camera_ids")
        extra_kwargs = {
            "camera_ids": {"help_text": "List of camera IDs for this time slot"}
        }

    def validate_camera_ids(self, value):
        """Validate that camera_ids is a list of positive integers."""
        if not isinstance(value, list):
            raise serializers.ValidationError("camera_ids must be a list")

        if not value:  # Check for empty list
            raise serializers.ValidationError("camera_ids cannot be empty")

        # Check if all elements are integers and positive
        for item in value:
            if not isinstance(item, int):
                raise serializers.ValidationError("All camera IDs must be integers")
            if item < 0:
                raise serializers.ValidationError(
                    "Camera IDs must be positive integers"
                )

        # Check for duplicates
        if len(value) != len(set(value)):
            raise serializers.ValidationError("Camera IDs must be unique")

        return value

    def validate_day(self, value):
        """Validate that day is one of the allowed choices."""
        valid_days = [choice[0] for choice in TimeSlot._meta.get_field("day").choices]
        if value not in valid_days:
            raise serializers.ValidationError(
                f"Invalid day. Must be one of: {', '.join(valid_days)}"
            )
        return value

    def validate(self, data):
        """Validate the entire data set."""
        # Check required fields
        required_fields = ["day", "start", "stop", "camera_ids"]
        for field in required_fields:
            if field not in data:
                raise serializers.ValidationError({field: "This field is required."})

        day = data["day"]
        start = data["start"]
        stop = data["stop"]

        # Validate timeslot is valid within the day
        if start >= stop:
            raise serializers.ValidationError(
                "Invalid TimeSlot: start time must be before stop time (cannot cross midnight)."
            )

        # When updating, exclude current instance
        instance_id = self.instance.id if self.instance else None

        # Overlap within same timestamp
        overlapping = (
            TimeSlot.objects.filter(
                day=day,
            )
            .exclude(id=instance_id)
            .filter(Q(start__lt=stop) & Q(stop__gt=start))
        )

        if overlapping.exists():
            overlapping_ids = list(overlapping.values_list("id", flat=True))
            raise serializers.ValidationError(
                f"TimeSlot overlaps with existing timeslot(s) in the schedule. Overlapping TimeSlot ID(s): {overlapping_ids}"
            )

        return data
