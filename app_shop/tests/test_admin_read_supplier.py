from django.urls import reverse

from app_shop.admin import SupplierAdmin
from app_shop.models import Supplier
from app_shop.tests.test_admin_create_supplier import BaseAdminTestCase


class AdminReadTestCase(BaseAdminTestCase):
    UPDATE_URL = '/admin/app_shop/supplier/{}/change/'
    ADD_URL = reverse('admin:app_shop_supplier_add')

    def test_number_of_intermediaries(self):
        """
        Проверка получения количества посредников
        """
        parent = Supplier.objects.create(**self.FACTORY_1_DATA)
        parent_admin = SupplierAdmin(parent, None)
        self.assertEqual(parent_admin.number_of_intermediaries(parent), 'Первое звено в цепочке')

        child = Supplier.objects.create(parent=parent, **self.RETAIL_DATA)
        child_admin = SupplierAdmin(child, None)
        self.assertEqual(child_admin.number_of_intermediaries(child), 0)

        grandchild = Supplier.objects.create(parent=child, **self.ENT_DATA)
        grandchild_admin = SupplierAdmin(grandchild, None)
        self.assertEqual(grandchild_admin.number_of_intermediaries(grandchild), 1)

    def test_clear_child_debt(self):
        """
        Проверка очистки долга через действие
        """
        response_create_parent = self.admin_client.post(self.ADD_URL, self.FACTORY_1_DATA)
        self.assertEqual(response_create_parent.status_code, 302)
        parent_id = Supplier.objects.latest('id').id

        child_with_debt = self.SUPPLIER_WITH_DEBT.copy()
        child_with_debt['parent'] = parent_id
        response_create_child = self.admin_client.post(self.ADD_URL, child_with_debt)
        self.assertEqual(response_create_child.status_code, 302)
        child_id = Supplier.objects.latest('id').id

        changelist_url = reverse('admin:app_shop_supplier_changelist')
        post_data = {
            'action': 'clear_debt',
            '_selected_action': [str(child_id)],
            'post': 'yes',
        }

        self.admin_client.post(changelist_url, post_data)
        self.assertEqual(Supplier.objects.get(id=child_id).debt, 0)

    def test_link_to_parent(self):
        """
        Проверка наличия ссылки на родителя в админке.
        """
        parent = Supplier.objects.create(**self.FACTORY_1_DATA)

        child_data = self.RETAIL_DATA.copy()
        child_data['parent'] = parent
        child = Supplier.objects.create(**child_data)

        child_admin = SupplierAdmin(child, None)
        parent_admin = SupplierAdmin(parent, None)

        self.assertEqual(parent_admin.link_to_parent(parent), "Первое звено в цепочке")

        link = reverse("admin:app_shop_supplier_change", args=[parent.id])
        expected_html = '<a href="{}">{}</a>'.format(link, parent)
        self.assertEqual(child_admin.link_to_parent(child), expected_html)
