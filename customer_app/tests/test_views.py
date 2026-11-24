from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO
from django.test import override_settings
from tempfile import TemporaryDirectory
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from django.core import mail
User = get_user_model()


class ChangePasswordViewTest(APITestCase):
    def test_change_password_saves_new_password(self):
        password = "StrongPass123!"
        user = User.objects.create_user(
            username="existing-user",
            email="test@example.com",
            password=password,
            is_active=True
        )

        self.client.force_authenticate(user=user)

        payload = {
            "old_password": password,
            "new_password": "NewPassword123!",
            "repeated_new_password": "NewPassword123!",
        }

        response = self.client.post(
            reverse("change-password"),
            payload,
            format="json"
        )

        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, response.data)

        user.refresh_from_db()

        self.assertTrue(user.check_password(payload["new_password"]))
        self.assertFalse(user.check_password(password))

    def test_wrong_old_password_does_not_change_password(self):
        password = "StrongPass123!"
        user = User.objects.create_user(
            username="existing-user",
            email="test@example.com",
            password=password,
            is_active=True
        )

        self.client.force_authenticate(user=user)

        payload = {
            "old_password": "WrongPass123!",
            "new_password": "NewPassword123!",
            "repeated_new_password": "NewPassword123!",
        }

        response = self.client.post(
            reverse("change-password"),
            payload,
            format="json"
        )

        self.assertEqual(response.status_code,
                         status.HTTP_400_BAD_REQUEST, response.data)

        user.refresh_from_db()

        self.assertFalse(user.check_password(payload["new_password"]))
        self.assertTrue(user.check_password(password))
        self.assertIn("old_password", response.data)

    def test_unauthenticated_user_cannot_change_password(self):
        payload = {
            "old_password": "WrongPass123!",
            "new_password": "NewPassword123!",
            "repeated_new_password": "NewPassword123!",
        }

        response = self.client.post(
            reverse("change-password"),
            payload,
            format="json"
        )

        self.assertEqual(response.status_code,
                         status.HTTP_401_UNAUTHORIZED, response.data)

    def test_mismatched_new_passwords_do_not_change_password(self):
        old_password = "StrongPass123!"
        user = User.objects.create_user(
            username="old-name",
            email="test@example.com",
            password=old_password,
            is_active=True
        )

        self.client.force_authenticate(user=user)

        payload = {
            "old_password": old_password,
            "new_password": "NewPassword123!",
            "repeated_new_password": "NewPassword123!!",
        }

        response = self.client.post(
            reverse("change-password"),
            payload,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("repeated_new_password", response.data)
        user.refresh_from_db()
        self.assertFalse(user.check_password(payload["new_password"]))
        self.assertTrue(user.check_password(old_password))


class ChangeUsernameViewTest(APITestCase):
    def test_change_username_saves_new_username_and_sends_email(self):
        user = User.objects.create_user(
            username="old-name",
            email="test@example.com",
            password="StrongPass123!",
            is_active=True
        )

        self.client.force_authenticate(user=user)

        payload = {
            "username": "newname"
        }

        response = self.client.patch(
            reverse("change-username"),
            payload,
            format="json"
        )
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, response.data)

        user.refresh_from_db()

        self.assertEqual(user.username, payload["username"])
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [user.email])

    def test_duplicate_username_is_rejected_without_sending_email(self):
        user1 = User.objects.create_user(
            username="oldname",
            email="test@example1.com",
            password="StrongPass123!",
            is_active=True
        )

        user2 = User.objects.create_user(
            username="newname",
            email="test@example2.com",
            password="StrongPass123!",
            is_active=True
        )

        self.client.force_authenticate(user=user1)

        payload = {
            "username": "NewName"
        }

        response = self.client.patch(
            reverse("change-username"),
            payload,
            format="json"
        )

        self.assertEqual(response.status_code,
                         status.HTTP_400_BAD_REQUEST, response.data)

        user1.refresh_from_db()

        self.assertEqual(user1.username, "oldname")
        self.assertEqual(len(mail.outbox), 0)

    def test_unauthenticated_user_cannot_change_username(self):
        payload = {
            "username": "newname"
        }

        response = self.client.patch(
            reverse("change-username"),
            payload,
            format="json"
        )

        self.assertEqual(response.status_code,
                         status.HTTP_401_UNAUTHORIZED, response.data)

        self.assertEqual(len(mail.outbox), 0)


class DeleteAccountViewTest(APITestCase):
    def test_wrong_password_does_not_delete_account(self):
        user = User.objects.create_user(
            username="old-name",
            email="test@example.com",
            password="StrongPass123!",
            is_active=True
        )

        self.client.force_authenticate(user=user)

        payload = {
            "password": "WrongPass123!"
        }

        response = self.client.delete(
            reverse("delete-account"),
            payload,
            format="json"
        )

        self.assertIn("password", response.data)
        self.assertEqual(response.status_code,
                         status.HTTP_400_BAD_REQUEST, response.data)
        self.assertTrue(User.objects.filter(pk=user.pk).exists())
        self.assertEqual(len(mail.outbox), 0)

    def test_correct_password_deletes_account_and_sends_email(self):
        user = User.objects.create_user(
            username="old-name",
            email="test@example.com",
            password="StrongPass123!",
            is_active=True
        )

        self.client.force_authenticate(user=user)

        payload = {
            "password": "StrongPass123!"
        }

        user_id = user.pk

        response = self.client.delete(
            reverse("delete-account"),
            payload,
            format="json"
        )

        self.assertEqual(response.status_code,
                         status.HTTP_200_OK)
        self.assertFalse(User.objects.filter(pk=user_id).exists())
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [user.email])

    def test_superuser_cannot_delete_account_even_with_correct_password(self):
        user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="StrongPass123!",
        )
        user_id = user.pk
        self.client.force_authenticate(user=user)

        payload = {
            "password": "StrongPass123!"
        }

        response = self.client.delete(
            reverse("delete-account"),
            payload,
            format="json"
        )

        self.assertEqual(response.status_code,
                         status.HTTP_400_BAD_REQUEST)

        self.assertEqual(
            response.data["detail"][0],
            "Ein Superuser-Konto kann nicht gelöscht werden.",
        )

        self.assertTrue(User.objects.filter(pk=user_id).exists())
        self.assertEqual(len(mail.outbox), 0)

    def test_unauthenticated_user_cannot_delete_account(self):
        user = User.objects.create_user(
            username="old-name",
            email="test@example.com",
            password="StrongPass123!",
            is_active=True
        )

        payload = {
            "password": "StrongPass123!"
        }

        response = self.client.delete(
            reverse("delete-account"),
            payload,
            format="json"
        )

        self.assertEqual(response.status_code,
                         status.HTTP_401_UNAUTHORIZED)

        self.assertTrue(User.objects.filter(pk=user.pk).exists())
        self.assertEqual(len(mail.outbox), 0)


class CustomerProfileViewTest(APITestCase):
    def test_authenticated_user_can_update_subscription(self):
        user = User.objects.create_user(
            username="old-name",
            email="test@example.com",
            password="StrongPass123!",
            is_active=True,
            has_subscription=False
        )
        self.client.force_authenticate(user=user)

        payload = {
            "has_subscription": True
        }

        response = self.client.patch(
            reverse("profile-customer"),
            payload,
            format="json"
        )

        self.assertEqual(response.status_code,
                         status.HTTP_200_OK)

        user.refresh_from_db()

        self.assertTrue(user.has_subscription)

    def test_authenticated_user_can_disable_subscription(self):
        user = User.objects.create_user(
            username="old-name",
            email="test@example.com",
            password="StrongPass123!",
            is_active=True,
            has_subscription=True
        )
        self.client.force_authenticate(user=user)

        payload = {
            "has_subscription": False
        }

        response = self.client.patch(
            reverse("profile-customer"),
            payload,
            format="json"
        )

        self.assertEqual(response.status_code,
                         status.HTTP_200_OK)

        user.refresh_from_db()

        self.assertFalse(user.has_subscription)

    def test_authenticated_user_can_retrieve_own_profile(self):
        user1 = User.objects.create_user(
            username="newname1",
            email="test@example1.com",
            password="StrongPass123!",
            is_active=True,
            has_subscription=True
        )

        user2 = User.objects.create_user(
            username="newname2",
            email="test@example2.com",
            password="StrongPass123!",
            is_active=True,
            has_subscription=True
        )

        self.client.force_authenticate(user=user2)

        response = self.client.get(reverse("profile-customer"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], user2.id)
        self.assertEqual(response.data["email"], user2.email)

        self.client.force_authenticate(user=user1)
        response = self.client.get(reverse("profile-customer"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], user1.id)
        self.assertEqual(response.data["email"], user1.email)

    def test_authenticated_user_can_not_retrieve_other_profile(self):
        user1 = User.objects.create_user(
            username="newname1",
            email="test@example1.com",
            password="StrongPass123!",
            is_active=True,
            has_subscription=True
        )

        user2 = User.objects.create_user(
            username="newname2",
            email="test@example2.com",
            password="StrongPass123!",
            is_active=True,
            has_subscription=True
        )

        self.client.force_authenticate(user=user1)
        response = self.client.get(
            reverse("profile-customer"),
            {"id": user2.pk},
        )

        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["id"], user1.pk)
        self.assertEqual(response.data["email"], user1.email)

    def test_profile_update_ignores_read_only_email(self):
        user = User.objects.create_user(
            username="newname",
            email="original@example.com",
            password="StrongPass123!",
            is_active=True,
        )

        self.client.force_authenticate(user=user)

        payload = {
            "email": "test@example.com",
            "first_name": "Anna"
        }

        response = self.client.patch(
            reverse("profile-customer"),
            payload,
            format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertEqual(user.first_name, "Anna")
        self.assertEqual(user.email, "original@example.com")

    def test_profile_update_rejects_invalid_phone(self):
        user = User.objects.create_user(
            username="newname",
            email="original@example.com",
            password="StrongPass123!",
            phone="+49 170 1234567",
            is_active=True,
        )

        self.client.force_authenticate(user=user)

        payload = {
            "phone": "abc",
        }

        response = self.client.patch(
            reverse("profile-customer"),
            payload,
            format="json")

        self.assertEqual(response.status_code,
                         status.HTTP_400_BAD_REQUEST, response.data)

        self.assertIn("phone", response.data)

        user.refresh_from_db()
        self.assertEqual(user.phone, "+49 170 1234567")

    def test_profile_update_saves_valid_phone(self):
        user = User.objects.create_user(
            username="newname",
            email="original@example.com",
            password="StrongPass123!",
            phone="+49 170 1234567",
            is_active=True,
        )

        self.client.force_authenticate(user=user)

        payload = {
            "phone": "+49 170 12312345"
        }

        response = self.client.patch(
            reverse("profile-customer"),
            payload,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("phone", response.data)
        user.refresh_from_db()
        self.assertEqual(user.phone, "+49 170 12312345")

    def test_unauthenticated_user_cannot_update_profile(self):

        payload = {"first_name": "Anna"}

        response = self.client.patch(
            reverse("profile-customer"),
            payload,
            format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_update_can_clear_phone(self):
        user = User.objects.create_user(
            username="newname",
            email="original@example.com",
            password="StrongPass123!",
            phone="+49 170 1234567",
            is_active=True,
        )

        self.client.force_authenticate(user=user)

        payload = {
            "phone": "",
        }

        response = self.client.patch(
            reverse("profile-customer"),
            payload,
            format="json")

        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, response.data)

        user.refresh_from_db()
        self.assertEqual(user.phone, "")

    def test_profile_update_preserves_omitted_phone(self):
        user = User.objects.create_user(
            first_name="Anna",
            username="newname",
            email="original@example.com",
            password="StrongPass123!",
            phone="+49 170 1234567",
            is_active=True,
        )

        self.client.force_authenticate(user=user)

        payload = {
            "first_name": "Maria"
        }
        response = self.client.patch(
            reverse("profile-customer"),
            payload,
            format="json")

        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, response.data)

        user.refresh_from_db()
        self.assertEqual(user.first_name, "Maria")
        self.assertEqual(user.phone, "+49 170 1234567")

    def test_profile_update_ignores_other_user_id(self):

        user1 = User.objects.create_user(
            first_name="Anna",
            username="user1",
            email="original1@example.com",
            password="StrongPass123!",
            phone="+49 170 1234567",
            is_active=True,
        )

        user2 = User.objects.create_user(
            first_name="Lisa",
            username="user2",
            email="original2@example.com",
            password="StrongPass123!",
            phone="+49 170 1234567",
            is_active=True,
        )

        self.client.force_authenticate(user=user1)

        payload = {"id": user2.pk, "first_name": "Maria"}

        response = self.client.patch(
            reverse("profile-customer"),
            payload,
            format="json")

        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, response.data)

        user1.refresh_from_db()
        user2.refresh_from_db()

        self.assertEqual(user1.first_name, "Maria")
        self.assertEqual(user2.first_name, "Lisa")

    @staticmethod
    def make_test_image(filename):
        with BytesIO() as buffer:
            Image.new("RGB", (10, 10), "blue").save(buffer, format="PNG")
            return SimpleUploadedFile(
                filename, buffer.getvalue(), content_type="image/png"
            )

    def test_profile_update_replaces_image_and_deletes_old_file(self):
        with TemporaryDirectory() as temp_media_root:
            with override_settings(MEDIA_ROOT=temp_media_root):
                user = User.objects.create_user(
                    username="newname",
                    email="original@example.com",
                    password="StrongPass123!",
                    phone="+49 170 1234567",
                    is_active=True,
                    image=self.make_test_image("old.png")
                )

                old_image_name = user.image.name

                self.client.force_authenticate(user=user)

                payload = {"image": self.make_test_image("new.png")}

                response = self.client.patch(
                    reverse("profile-customer"),
                    payload,
                    format="multipart")

                self.assertEqual(response.status_code,
                                 status.HTTP_200_OK)

                user.refresh_from_db()
                self.assertNotEqual(user.image.name, old_image_name)
                self.assertTrue(user.image.storage.exists(user.image.name))
                self.assertFalse(user.image.storage.exists(old_image_name))

    def test_profile_update_with_invalid_image_preserves_existing_image(self):
        def make_test_image(filename):
            with BytesIO() as buffer:
                Image.new("RGB", (10, 10), "blue").save(buffer, format="PNG")
                return SimpleUploadedFile(
                    filename, b"This is not picture", content_type="image/png"
                )

        with TemporaryDirectory() as temp_media_root:
            with override_settings(MEDIA_ROOT=temp_media_root):
                user = User.objects.create_user(
                    username="newname",
                    email="original@example.com",
                    password="StrongPass123!",
                    phone="+49 170 1234567",
                    is_active=True,
                    image=make_test_image("old.png")
                )

                old_image_name = user.image.name

                self.client.force_authenticate(user=user)

                payload = {"image": make_test_image("newone.png")}

                response = self.client.patch(
                    reverse("profile-customer"),
                    payload,
                    format="multipart")

                self.assertEqual(response.status_code,
                                 status.HTTP_400_BAD_REQUEST, response.data)
                self.assertIn("image", response.data)

                user.refresh_from_db()
                self.assertEqual(user.image.name, old_image_name)
                self.assertTrue(user.image.storage.exists(old_image_name))

    def test_profile_update_without_image_preserves_existing_image(self):
        with TemporaryDirectory() as temp_media_root:
            with override_settings(MEDIA_ROOT=temp_media_root):
                user = User.objects.create_user(
                    username="newname",
                    email="original@example.com",
                    password="StrongPass123!",
                    first_name="Anna",
                    image=self.make_test_image("old.png"),
                )
                old_image_name = user.image.name
                self.assertTrue(user.image.storage.exists(old_image_name))
                self.client.force_authenticate(user=user)

                payload = {"first_name": "Maria"}

                response = self.client.patch(
                    reverse("profile-customer"),
                    payload,
                    format="json",
                )

                self.assertEqual(response.status_code,
                                 status.HTTP_200_OK, response.data)
                user.refresh_from_db()
                self.assertEqual(user.first_name, "Maria")
                self.assertEqual(user.image.name, old_image_name)
                self.assertTrue(user.image.storage.exists(old_image_name))

    def test_profile_update_can_upload_first_image(self):
        with TemporaryDirectory() as temp_media_root:
            with override_settings(MEDIA_ROOT=temp_media_root):
                user = User.objects.create_user(
                    username="newname",
                    email="original@example.com",
                    password="StrongPass123!",
                    phone="+49 170 1234567",
                    is_active=True,
                )

                self.client.force_authenticate(user=user)

                payload = {"image": self.make_test_image("newone.png")}

                response = self.client.patch(
                    reverse("profile-customer"),
                    payload,
                    format="multipart")

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                user.refresh_from_db()
                self.assertTrue(user.image.name)
                self.assertTrue(user.image.storage.exists(user.image.name))

    def test_profile_update_can_remove_image_and_deletes_file(self):
        with TemporaryDirectory() as temp_media_root:
            with override_settings(MEDIA_ROOT=temp_media_root):
                user = User.objects.create_user(
                    username="newname",
                    email="original@example.com",
                    password="StrongPass123!",
                    phone="+49 170 1234567",
                    is_active=True,
                    image=self.make_test_image("old.png"),
                )

                self.client.force_authenticate(user=user)

                payload = {"image": ""}

                response = self.client.patch(
                    reverse("profile-customer"),
                    payload,
                    format="multipart")

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                user.refresh_from_db()
                self.assertFalse(user.image.name)

    def test_profile_update_ignores_is_superuser(self):
        user = User.objects.create_user(
            username="newname",
            first_name="Anna",
            email="original@example.com",
            password="StrongPass123!",
            phone="+49 170 1234567",
            is_active=True,
            is_superuser=False
        )

        self.client.force_authenticate(user=user)

        payload = {
            "is_superuser": True,
            "first_name": "Maria",
        }
        response = self.client.patch(
            reverse("profile-customer"),
            payload,
            format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user.refresh_from_db()
        self.assertFalse(user.is_superuser)
        self.assertEqual(user.first_name, "Maria")

    def test_unauthenticated_user_cannot_retrieve_profile(self):
        response = self.client.get(reverse("profile-customer"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_update_ignores_read_only_is_active(self):
        user = User.objects.create_user(
            username="newname",
            first_name="Anna",
            email="original@example.com",
            password="StrongPass123!",
            phone="+49 170 1234567",
            is_active=True,
        )

        self.client.force_authenticate(user=user)

        payload = {"is_active": False, "first_name": "Maria"}

        response = self.client.patch(
            reverse("profile-customer"),
            payload,
            format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user.refresh_from_db()
        self.assertEqual(user.first_name, "Maria")
        self.assertTrue(user.is_active)
