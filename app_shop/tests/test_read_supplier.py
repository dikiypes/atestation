from rest_framework import status
from rest_framework.test import APIClient

from app_shop.models import Supplier
from app_shop.tests.base_test import BaseTestCase


class SupplierReadAPITestCase(BaseTestCase):
    """Просмотр звеньев"""

    def setUp(self):
        super().setUp()

        response_factory_1 = self.user_client.post(self.URL, self.FACTORY_1_DATA)
        self.factory_1_id = response_factory_1.json()['id']

        response_factory_2 = self.user_client.post(self.URL, self.FACTORY_2_DATA)
        self.factory_2_id = response_factory_2.json()['id']

        retail_data = self.RETAIL_DATA.copy()
        retail_data['parent'] = self.factory_1_id
        response_retail = self.user_client.post(self.URL, retail_data)
        self.retail_id = response_retail.json()['id']

        ent_data = self.ENT_DATA.copy()
        ent_data['parent'] = self.factory_2_id
        response_ip = self.user_client.post(self.URL, self.ENT_DATA)
        self.ent_id = response_ip.json()['id']

    def test_supplier_hierarchy_and_ordering(self):
        """Тест иерархии и порядка узлов"""

        response = self.user_client.get(self.URL)
        suppliers = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for supplier in suppliers:
            if supplier["parent"]:
                parent_supplier = next(s for s in suppliers if s["id"] == supplier["parent"])
                self.assertTrue(parent_supplier, f"Родитель для {supplier['name']} не найден")
                self.assertEqual(parent_supplier["level"] + 1, supplier["level"],
                                 f"Некорректный уровень иерархии для {supplier['name']}")

        suppliers = sorted(suppliers, key=lambda x: (x["tree_id"], x["lft"]))

        for supplier in suppliers:
            same_tree_nodes = [s for s in suppliers if s["tree_id"] == supplier["tree_id"]]
            same_tree_nodes_sorted = sorted(same_tree_nodes, key=lambda x: x["lft"])

            self.assertEqual(same_tree_nodes, same_tree_nodes_sorted, "Узлы некорректно упорядочены")

    def test_supplier_attributes(self):
        """Проверка атрибутов у созданных узлов"""

        response = self.user_client.get(self.URL)
        suppliers = sorted(response.json(), key=lambda x: x["id"])

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_attributes = [
            self.FACTORY_1_DATA,
            self.FACTORY_2_DATA,
            self.RETAIL_DATA,
            self.ENT_DATA
        ]

        for supplier, expected_attrs in zip(suppliers, expected_attributes):
            self.assertEqual(supplier['type_supplier'], expected_attrs['type_supplier'])
            self.assertEqual(supplier['name'], expected_attrs['name'])
            self.assertEqual(supplier['email'], expected_attrs['email'])
            self.assertEqual(supplier['country'], expected_attrs['country'])
            self.assertEqual(supplier['city'], expected_attrs['city'])
            self.assertEqual(supplier['street'], expected_attrs['street'])
            self.assertEqual(supplier['house_number'], expected_attrs['house_number'])
            self.assertEqual(float(supplier['debt']), expected_attrs['debt'])

    def test_get_node_by_id(self):
        """Получение узла по его ID и проверка атрибутов"""

        ent_id = Supplier.objects.get(name=self.ENT_DATA["name"]).id
        response = self.user_client.get(f"{self.URL}{ent_id}/")
        ent_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ent_data['type_supplier'], self.ENT_DATA['type_supplier'])
        self.assertEqual(ent_data['name'], self.ENT_DATA['name'])
        self.assertEqual(ent_data['email'], self.ENT_DATA['email'])
        self.assertEqual(ent_data['country'], self.ENT_DATA['country'])
        self.assertEqual(ent_data['city'], self.ENT_DATA['city'])
        self.assertEqual(ent_data['street'], self.ENT_DATA['street'])
        self.assertEqual(ent_data['house_number'], self.ENT_DATA['house_number'])
        self.assertEqual(float(ent_data['debt']), self.ENT_DATA['debt'])

    def test_unauthorized_user_cannot_read_suppliers(self):
        """Неавторизованный пользователь не может просматривать список звеньев"""
        client = APIClient()
        response = client.get(self.URL)
        response_data = response.json()

        self.assertEqual(response_data.get("detail"), "Учетные данные не были предоставлены.")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthorized_user_cannot_read_supplier_by_id(self):
        """Неавторизованный пользователь не может просматривать звено по ID"""
        ent_id = Supplier.objects.get(name=self.ENT_DATA["name"]).id
        client = APIClient()
        response = client.get(f"{self.URL}{ent_id}/")
        response_data = response.json()

        self.assertEqual(response_data.get("detail"), "Учетные данные не были предоставлены.")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
