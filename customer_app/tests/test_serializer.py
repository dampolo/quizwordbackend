from io import BytesIO
from types import SimpleNamespace

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from PIL import Image
from rest_framework import serializers

from customer_app.api.serializer import CustomerProfileSerializer


class CustomerProfileSerializerTest(SimpleTestCase):
    def test_valid_phone_is_accepted(self):
        serializer = CustomerProfileSerializer(
            data={"phone": "+49 170 1234567"},
            partial=True,
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

        self.assertEqual(
            serializer.validated_data["phone"],
            "+49 170 1234567",
        )

    def test_phone_with_letters_is_rejected(self):
        serializer = CustomerProfileSerializer(
            data={"phone": "+49 ABC 1234567"},
            partial=True,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("phone", serializer.errors)

    def test_empty_phone_is_accepted(self):
        serializer = CustomerProfileSerializer(
            data={"phone": ""},
            partial=True,
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

        self.assertEqual(
            serializer.validated_data["phone"],
            "",
        )

    def test_phone_with_invalid_digit_count_is_rejected(self):
        for phone in ("123456", "1234567890123456"):
            with self.subTest(phone=phone):
                serializer = CustomerProfileSerializer(
                    data={"phone": phone},
                    partial=True,
                )

                self. assertFalse(serializer.is_valid())
                self.assertIn("phone", serializer.errors)

    def test_phone_digit_count_boundaries_are_accepted(self):
        for phone in ("1234567", "123456789012345"):
            with self.subTest(phone=phone):
                serializer = CustomerProfileSerializer(
                    data={"phone": phone},
                    partial=True,
                )

                self.assertTrue(
                    serializer.is_valid(),
                    serializer.errors,
                )
                self.assertEqual(
                    serializer.validated_data["phone"],
                    phone,
                )

    def test_phone_with_plus_in_middle_is_rejected(self):
        serializer = CustomerProfileSerializer(
            data={"phone": "49+170456123431"},
            partial=True,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("phone", serializer.errors)

    def test_names_without_letters_are_rejected(self):
        for field in ("first_name", "last_name"):
            for value in ("123", "!!!"):
                with self.subTest(field=field, value=value):
                    serializer = CustomerProfileSerializer(
                        data={field: value},
                        partial=True,
                    )

                    self.assertFalse(serializer.is_valid())
                    self.assertIn(field, serializer.errors)

    def test_valid_and_empty_names_are_accepted(self):
        for field in ("first_name", "last_name"):
            for value in ("", "José", "Anne-Marie", "O'Connor", "李"):
                with self.subTest(field=field, value=value):
                    serializer = CustomerProfileSerializer(
                        data={field: value},
                        partial=True,
                    )

                    self.assertTrue(
                        serializer.is_valid(),
                        serializer.errors,
                    )
                    self.assertEqual(
                        serializer.validated_data[field],
                        value,
                    )

    def test_valid_and_empty_city_and_street_are_accepted(self):
        examples = {
            "city": ("", "Berlin", "Frankfurt am Main", "東京"),
            "street": ("", "Hauptstraße", "Straße des 17. Juni", "5th Avenue"),
        }

        for field, values in examples.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    serializer = CustomerProfileSerializer(
                        data={field: value},
                        partial=True,
                    )

                    self.assertTrue(
                        serializer.is_valid(),
                        serializer.errors,
                    )
                    self.assertEqual(
                        serializer.validated_data[field],
                        value,
                    )

    def test_city_and_street_without_letters_are_rejected(self):
        for field in ("city", "street"):
            for value in ("123", "!!!"):
                with self.subTest(field=field, value=value):
                    serializer = CustomerProfileSerializer(
                        data={field: value},
                        partial=True,
                    )

                    self.assertFalse(serializer.is_valid())
                    self.assertIn(field, serializer.errors)

    def test_valid_and_empty_street_number_are_accepted(self):
        for value in ("", "12", "12a", "12-14", "12/1"):
            with self.subTest(value=value):
                serializer = CustomerProfileSerializer(
                    data={"street_number": value},
                    partial=True,
                )

                self.assertTrue(
                    serializer.is_valid(),
                    serializer.errors,
                )
                self.assertEqual(
                    serializer.validated_data["street_number"],
                    value,
                )

    def test_street_number_without_digits_is_rejected(self):
        for value in ("abc", "!?!"):
            with self.subTest(value=value):
                serializer = CustomerProfileSerializer(
                    data={"street_number": value},
                    partial=True,
                )

                self.assertFalse(serializer.is_valid())
                self.assertIn("street_number", serializer.errors)

    def test_valid_and_empty_postcodes_are_accepted(self):
        for value in ("", "10115", "SW1A 1AA", "H2X 1Y4", "12345-6789"):
            with self.subTest(value=value):
                serializer = CustomerProfileSerializer(
                    data={"postcode": value},
                    partial=True,
                )

                self.assertTrue(
                    serializer.is_valid(),
                    serializer.errors,
                )
                self.assertEqual(
                    serializer.validated_data["postcode"],
                    value,
                )

    def test_invalid_postcodes_are_rejected(self):
        for value in ("!!!", "---", "10115!", "AB/12"):
            with self.subTest(value=value):
                serializer = CustomerProfileSerializer(
                    data={"postcode": value},
                    partial=True,
                )

                self.assertFalse(serializer.is_valid())
                self.assertIn("postcode", serializer.errors)

    def test_image_at_size_limit_is_accepted(self):
        image = SimpleNamespace(size=2 * 1024 * 1024)
        serializer = CustomerProfileSerializer()

        result = serializer.validate_image(image)

        self.assertIs(result, image)

    def test_image_above_size_limit_is_rejected(self):
        image = SimpleNamespace(size=2 * 1024 * 1024 + 1)
        serializer = CustomerProfileSerializer()

        with self.assertRaises(serializers.ValidationError):
            serializer.validate_image(image)

    def test_valid_image_is_accepted(self):
        with BytesIO() as buffer:
            image = Image.new("RGB", (10, 10), color="blue")
            image.save(buffer, format="PNG")

            uploaded_image = SimpleUploadedFile(
                name="profile.png",
                content=buffer.getvalue(),
                content_type="image/png",
            )

        serializer = CustomerProfileSerializer(
            data={"image": uploaded_image},
            partial=True,
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )
        self.assertIn("image", serializer.validated_data)

    def test_fake_image_is_rejected(self):
        uploaded_file = SimpleUploadedFile(
            name="profile.png",
            content=b"This is text, not an image.",
            content_type="image/png",
        )

        serializer = CustomerProfileSerializer(
            data={"image": uploaded_file},
            partial=True,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("image", serializer.errors)
