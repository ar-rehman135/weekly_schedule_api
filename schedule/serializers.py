from rest_framework import serializers
from .models import TimeSlot
from django.db.models import Q
from functools import lru_cache


class TimeSlotSerializer(serializers.ModelSerializer):
    # Cache valid days to avoid repeated database lookups
    _valid_days = None

    class Meta:
        model = TimeSlot
        fields = ("id", "day", "start", "stop", "camera_ids")
        extra_kwargs = {
            "camera_ids": {"help_text": "List of camera IDs for this time slot"}
        }

    @classmethod
    def get_valid_days(cls):
        """Get valid days with caching."""
        if cls._valid_days is None:
            cls._valid_days = [
                choice[0] for choice in TimeSlot._meta.get_field("day").choices
            ]
        return cls._valid_days

    def validate_camera_ids(self, value):
        """Validate that camera_ids is a list of positive integers."""
        if not isinstance(value, list):
            raise serializers.ValidationError("camera_ids must be a list")

        if not value:  # Check for empty list
            raise serializers.ValidationError("camera_ids cannot be empty")

        # Use set for faster duplicate checking
        seen = set()
        for item in value:
            if not isinstance(item, int):
                raise serializers.ValidationError("All camera IDs must be integers")
            if item < 0:
                raise serializers.ValidationError(
                    "Camera IDs must be positive integers"
                )
            if item in seen:
                raise serializers.ValidationError("Camera IDs must be unique")
            seen.add(item)

        return value

    def validate_day(self, value):
        """Validate that day is one of the allowed choices."""
        if value not in self.get_valid_days():
            raise serializers.ValidationError(
                f"Invalid day. Must be one of: {', '.join(self.get_valid_days())}"
            )
        return value

    @lru_cache(maxsize=128)
    def _check_overlap(self, day, start, stop, instance_id=None):
        """Cached method to check for overlapping timeslots."""
        overlapping = (
            TimeSlot.objects.filter(
                day=day,
            )
            .exclude(id=instance_id)
            .filter(Q(start__lt=stop) & Q(stop__gt=start))
            .values_list("id", flat=True)
        )
        return list(overlapping)

    def validate(self, data):
        """Validate the entire data set."""
        # Check required fields
        required_fields = ["day", "start", "stop", "camera_ids"]
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise serializers.ValidationError(
                {field: "This field is required." for field in missing_fields}
            )

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

        # Check for overlapping timeslots using cached method
        overlapping_ids = self._check_overlap(day, start, stop, instance_id)
        if overlapping_ids:
            raise serializers.ValidationError(
                f"TimeSlot overlaps with existing timeslot(s) in the schedule. Overlapping TimeSlot ID(s): {overlapping_ids}"
            )

        return data
