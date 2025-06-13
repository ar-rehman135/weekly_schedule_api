from django.db import models


DAYS_OF_WEEK = [
    ("monday", "Monday"),
    ("tuesday", "Tuesday"),
    ("wednesday", "Wednesday"),
    ("thursday", "Thursday"),
    ("friday", "Friday"),
    ("saturday", "Saturday"),
    ("sunday", "Sunday"),
]


class TimeSlot(models.Model):
    """
    Represents a time slot in the weekly schedule.
    Each time slot is associated with specific camera IDs for that period.
    """

    day = models.CharField(max_length=10, choices=DAYS_OF_WEEK)
    start = models.TimeField(help_text="Start time of the slot (HH:MM)")
    stop = models.TimeField(help_text="End time of the slot (HH:MM)")
    camera_ids = models.JSONField(
        default=list, help_text="List of camera IDs associated with this time slot"
    )

    class Meta:
        verbose_name = "Time Slot"
        verbose_name_plural = "Time Slots"
        indexes = [
            models.Index(fields=["day", "start"]),
            models.Index(fields=["day", "stop"]),
        ]

    def __str__(self):
        return f"{self.day} {self.start}-{self.stop}"
