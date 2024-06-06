from django.contrib.messages import get_messages
from django.urls import reverse

from app_shop.models import Supplier
from app_shop.tests.test_admin_create_supplier import BaseAdminTestCase


class AdminUpdateTestCase(BaseAdminTestCase):
    UPDATE_URL = '/admin/app_shop/supplier/{}/change/'
    ADD_URL = reverse('admin:app_shop_supplier_add')

    def test_cyclic_relationship_is_prevented(self):
        """Нельзя создать зацикленные отношения"""

        self.admin_client.post(self.ADD_URL, self.RETAIL_DATA)
        retail_id = Supplier.objects.latest('id').id

        ent_data = self.ENT_DATA.copy()
        ent_data['parent'] = retail_id
        self.admin_client.post(self.ADD_URL, ent_data)
        ip_id = Supplier.objects.latest('id').id

        retail_data_updated = self.RETAIL_DATA.copy()
        retail_data_updated['parent'] = ip_id
        response_retail_updated = self.admin_client.post(self.UPDATE_URL.format(retail_id), retail_data_updated)

        self.assertNotEqual(response_retail_updated.status_code, 200)
        messages = list(get_messages(response_retail_updated.wsgi_request))
        self.assertIn('Ошибка: нельзя создать циклическую зависимость между поставщиками',
                      [str(message) for message in messages])

    def test_self_as_parent_is_prevented(self):
        """Нельзя указать элемент в качестве родителя самому себе"""

        self.admin_client.post(self.ADD_URL, self.RETAIL_DATA)
        retail_id = Supplier.objects.latest('id').id

        retail_data_updated = self.RETAIL_DATA.copy()
        retail_data_updated['parent'] = retail_id
        response_retail_updated = self.admin_client.post(self.UPDATE_URL.format(retail_id), retail_data_updated)

        self.assertNotEqual(response_retail_updated.status_code, 200)
        messages = list(get_messages(response_retail_updated.wsgi_request))
        self.assertIn('Ошибка: нельзя создать циклическую зависимость между поставщиками',
                      [str(message) for message in messages])
