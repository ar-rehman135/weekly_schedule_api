from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from schedule.models import TimeSlot


class TimeSlotAPITestCase(APITestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(username="testuser", password="testpass")
        # Obtain JWT token
        response = self.client.post(
            reverse("token_obtain_pair"),
            {"username": "testuser", "password": "testpass"},
            format="json",
        )
        self.token = response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.token)

    def test_create_valid_timeslot(self):
        data = {
            "day": "monday",
            "start": "09:00",
            "stop": "10:00",
            "camera_ids": [1, 2, 3],
        }
        response = self.client.post("/api/timeslots/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TimeSlot.objects.count(), 1)
        timeslot = TimeSlot.objects.first()
        self.assertEqual(timeslot.camera_ids, [1, 2, 3])

    def test_reject_invalid_camera_ids(self):
        # Test with non-list camera_ids
        data = {
            "day": "monday",
            "start": "09:00",
            "stop": "10:00",
            "camera_ids": "not-a-list",
        }
        response = self.client.post("/api/timeslots/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("camera_ids must be a list", str(response.data))

        # Test with non-integer camera_ids
        data["camera_ids"] = [1, 2, "3"]
        response = self.client.post("/api/timeslots/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("All camera IDs must be integers", str(response.data))

    def test_reject_overlapping_timeslot(self):
        # Create initial timeslot
        TimeSlot.objects.create(
            day="monday",
            start="09:00",
            stop="10:00",
            camera_ids=[1, 2],
        )
        # Try to create overlapping timeslot
        data = {
            "day": "monday",
            "start": "09:30",
            "stop": "10:30",
            "camera_ids": [3],
        }
        response = self.client.post("/api/timeslots/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Overlapping TimeSlot ID", str(response.data))

    def test_reject_invalid_timeslot_cross_midnight(self):
        data = {
            "day": "monday",
            "start": "23:00",
            "stop": "01:00",
            "camera_ids": [4, 5],
        }
        response = self.client.post("/api/timeslots/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("start time must be before stop time", str(response.data))

    def test_list_grouped_schedule(self):
        # Create multiple timeslots
        TimeSlot.objects.create(
            day="monday",
            start="08:00",
            stop="09:00",
            camera_ids=[1],
        )
        TimeSlot.objects.create(
            day="tuesday",
            start="10:00",
            stop="11:00",
            camera_ids=[2],
        )
        TimeSlot.objects.create(
            day="monday",
            start="09:00",
            stop="10:00",
            camera_ids=[3],
        )

        response = self.client.get("/api/timeslots/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        schedule = response.data["schedule"]
        self.assertIn("monday", schedule)
        self.assertIn("tuesday", schedule)
        self.assertEqual(len(schedule["monday"]), 2)
        self.assertEqual(len(schedule["tuesday"]), 1)

        # Verify timeslots are ordered by start time
        monday_slots = schedule["monday"]
        self.assertEqual(monday_slots[0]["start"], "08:00:00")
        self.assertEqual(monday_slots[1]["start"], "09:00:00")

    def test_update_timeslot_valid(self):
        # Create initial timeslot
        timeslot = TimeSlot.objects.create(
            day="monday", start="08:00", stop="09:00", camera_ids=[1]
        )

        url = f"/api/timeslots/{timeslot.id}/"

        # Update with valid new timeslot
        data = {
            "day": "monday",
            "start": "09:00",
            "stop": "10:00",
            "camera_ids": [1, 2, 3],
        }

        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify update happened
        timeslot.refresh_from_db()
        self.assertEqual(str(timeslot.start), "09:00:00")
        self.assertEqual(str(timeslot.stop), "10:00:00")
        self.assertEqual(timeslot.camera_ids, [1, 2, 3])

    def test_update_timeslot_reject_overlap(self):
        # Create two timeslots
        t1 = TimeSlot.objects.create(
            day="monday", start="08:00", stop="09:00", camera_ids=[1]
        )
        t2 = TimeSlot.objects.create(
            day="monday", start="09:00", stop="10:00", camera_ids=[2]
        )

        url = f"/api/timeslots/{t2.id}/"

        # Try to update t2 to overlap with t1
        data = {
            "day": "monday",
            "start": "08:30",  # Overlaps with t1
            "stop": "09:30",
            "camera_ids": [2],
        }

        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Overlapping TimeSlot ID", str(response.data))

    def test_delete_timeslot(self):
        # Create timeslot
        timeslot = TimeSlot.objects.create(
            day="wednesday", start="11:00", stop="12:00", camera_ids=[5, 6]
        )

        url = f"/api/timeslots/{timeslot.id}/"

        # Delete it
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify it is gone
        self.assertEqual(TimeSlot.objects.filter(id=timeslot.id).count(), 0)

    def test_retrieve_timeslot(self):
        # Create timeslot
        timeslot = TimeSlot.objects.create(
            day="friday", start="14:00", stop="15:00", camera_ids=[7, 8, 9]
        )

        url = f"/api/timeslots/{timeslot.id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["day"], "friday")
        self.assertEqual(response.data["start"], "14:00:00")
        self.assertEqual(response.data["stop"], "15:00:00")
        self.assertEqual(response.data["camera_ids"], [7, 8, 9])

    def test_reject_invalid_day(self):
        data = {
            "day": "invalid_day",
            "start": "09:00",
            "stop": "10:00",
            "camera_ids": [1, 2],
        }
        response = self.client.post("/api/timeslots/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("day", str(response.data))

    def test_reject_invalid_time_format(self):
        data = {
            "day": "monday",
            "start": "25:00",  # Invalid hour
            "stop": "10:00",
            "camera_ids": [1, 2],
        }
        response = self.client.post("/api/timeslots/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data["start"] = "09:00"
        data["stop"] = "10:61"  # Invalid minute
        response = self.client.post("/api/timeslots/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reject_empty_camera_ids(self):
        data = {
            "day": "monday",
            "start": "09:00",
            "stop": "10:00",
            "camera_ids": [],
        }
        response = self.client.post("/api/timeslots/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("camera_ids", str(response.data))

    def test_reject_duplicate_camera_ids(self):
        data = {
            "day": "monday",
            "start": "09:00",
            "stop": "10:00",
            "camera_ids": [1, 2, 1],  # Duplicate ID
        }
        response = self.client.post("/api/timeslots/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Camera IDs must be unique", str(response.data))

    def test_reject_negative_camera_ids(self):
        data = {
            "day": "monday",
            "start": "09:00",
            "stop": "10:00",
            "camera_ids": [-1, 2, 3],
        }
        response = self.client.post("/api/timeslots/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("camera_ids", str(response.data))

    def test_reject_missing_required_fields(self):
        # Test missing day
        data = {
            "start": "09:00",
            "stop": "10:00",
            "camera_ids": [1, 2],
        }
        response = self.client.post("/api/timeslots/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("day", str(response.data))

        # Test missing start
        data = {
            "day": "monday",
            "stop": "10:00",
            "camera_ids": [1, 2],
        }
        response = self.client.post("/api/timeslots/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("start", str(response.data))

        # Test missing stop
        data = {
            "day": "monday",
            "start": "09:00",
            "camera_ids": [1, 2],
        }
        response = self.client.post("/api/timeslots/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("stop", str(response.data))

        # Test missing camera_ids
        data = {
            "day": "monday",
            "start": "09:00",
            "stop": "10:00",
        }
        response = self.client.post("/api/timeslots/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("camera_ids", str(response.data))
