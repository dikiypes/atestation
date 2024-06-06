from rest_framework import status
from rest_framework.test import APIClient

from app_shop.models import Supplier
from app_shop.tests.base_test import BaseTestCase


class SupplierPartialUpdateAPITestCase(BaseTestCase):
    """Частичное обновление звена"""

    def test_unauthorized_user_cannot_partial_update_supplier(self):
        """Неавторизованный пользователь не может частично обновлять данные о звене"""

        response_create = self.user_client.post(self.URL, self.FACTORY_1_DATA)
        supplier_id = response_create.json()['id']

        update_data = {
            "name": "Новое название"
        }

        client = APIClient()
        response = client.patch(f"{self.URL}{supplier_id}/", update_data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        supplier = Supplier.objects.get(id=supplier_id)
        self.assertNotEqual(supplier.name, update_data["name"])

    def test_cannot_partial_update_supplier_debt(self):
        """Нельзя обновить поле 'debt' звена при частичном обновлении"""

        response_create_parent = self.user_client.post(self.URL, self.FACTORY_1_DATA)
        parent_id = response_create_parent.json()['id']

        retail_data = self.RETAIL_DATA.copy()
        retail_data['parent'] = parent_id
        retail = self.user_client.post(self.URL, retail_data)
        retail_id = retail.json()['id']

        update_data = {
            "debt": 7000.50,
        }

        response = self.user_client.patch(f"{self.URL}{retail_id}/", update_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json().get('non_field_errors')[0], "Ошибка: нельзя изменять значение долга через API")
        supplier = Supplier.objects.get(id=retail_id)
        self.assertNotEqual(float(supplier.debt), update_data["debt"])
        self.assertEqual(float(supplier.debt), self.RETAIL_DATA["debt"])

    def test_partial_update_supplier_with_blank_or_spaces_fields(self):
        """Проверка, что нельзя частично обновить звено с пустыми или состоящими из пробелов полями"""

        response = self.user_client.post(self.URL, self.FACTORY_1_DATA)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        supplier_id = response.json()['id']

        fields_to_test = ["name", "country", "city", "street", "house_number"]

        for field in fields_to_test:
            data = {field: ""}
            response = self.user_client.patch(f"{self.URL}{supplier_id}/", data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.json().get(field)[0], 'Это поле не может быть пустым.')

            data = {field: "   "}
            response = self.user_client.patch(f"{self.URL}{supplier_id}/", data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.json().get(field)[0], 'Это поле не может быть пустым.')

        response = self.user_client.get(f"{self.URL}{supplier_id}/")
        updated_supplier = response.json()

        for field in fields_to_test:
            self.assertEqual(updated_supplier[field], self.FACTORY_1_DATA[field])

    def test_update_supplier_unique_constraints(self):
        """
        Проверка, что поставщик с одинаковой комбинацией 'country', 'city', 'name', 'email' не может быть обновлен.
        """

        response_1 = self.user_client.post(self.URL, self.FACTORY_1_DATA, format='json')
        self.assertEqual(response_1.status_code, status.HTTP_201_CREATED)

        response_2 = self.user_client.post(self.URL, self.FACTORY_2_DATA, format='json')
        self.assertEqual(response_2.status_code, status.HTTP_201_CREATED)

        update_data = self.FACTORY_1_DATA.copy()
        response_update = self.user_client.patch(
            f"{self.URL}{response_2.json()['id']}/", update_data, format='json'
        )

        self.assertEqual(response_update.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response_update.json().get('non_field_errors')[0],
            'Поля country, city, name, email должны производить массив с уникальными значениями.'
        )

    def test_partial_update_factory_with_parent(self):
        """Проверка, что завод не может иметь родителя при частичном обновлении"""

        response_factory_1 = self.user_client.post(self.URL, self.FACTORY_1_DATA)
        self.assertEqual(response_factory_1.status_code, status.HTTP_201_CREATED)
        factory_1_id = response_factory_1.json()['id']

        response_factory_2 = self.user_client.post(self.URL, self.FACTORY_2_DATA)
        self.assertEqual(response_factory_2.status_code, status.HTTP_201_CREATED)
        factory_2_id = response_factory_2.json()['id']

        partial_update_data = {"parent": factory_1_id}
        response = self.user_client.patch(f"{self.URL}{factory_2_id}/", partial_update_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json().get('non_field_errors')[0], 'Ошибка: завод не может иметь родителя')

        response = self.user_client.get(f"{self.URL}{factory_2_id}/")
        updated_factory = response.json()
        self.assertIsNone(updated_factory['parent'])

    def test_cyclic_relationship_is_prevented(self):
        """Нельзя создать зацикленные отношения"""

        retail_data = self.RETAIL_DATA.copy()
        response_retail = self.user_client.post(self.URL, retail_data)
        retail_id = response_retail.json()['id']

        ip_data = self.ENT_DATA.copy()
        ip_data['parent'] = retail_id
        response_ip = self.user_client.post(self.URL, ip_data)
        ip_id = response_ip.json()['id']

        retail_data_updated = self.RETAIL_DATA.copy()
        retail_data_updated['parent'] = ip_id
        retail_data_updated.pop('debt', None)
        response_retail_updated = self.user_client.patch(f"{self.URL}{retail_id}/", retail_data_updated)

        self.assertEqual(response_retail_updated.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_retail_updated.json().get('error'), 'Зацикленные отношения не допустимы')

    def test_self_as_parent_is_prevented(self):
        """Нельзя указать элемент в качестве родителя самому себе"""

        response_retail = self.user_client.post(self.URL, self.RETAIL_DATA)
        retail_id = response_retail.json()['id']

        retail_data_updated = self.RETAIL_DATA.copy()
        retail_data_updated['parent'] = retail_id
        retail_data_updated.pop('debt', None)
        response_retail_updated = self.user_client.patch(f"{self.URL}{retail_id}/", retail_data_updated)

        self.assertEqual(response_retail_updated.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_retail_updated.json().get('error'), 'Зацикленные отношения не допустимы')

    def test_patch_node_parent(self):
        """
        Проверка корректного перестроения дерева при изменении родительского узла
        """

        parent1 = self.user_client.post(self.URL, self.FACTORY_1_DATA).json()
        parent2 = self.user_client.post(self.URL, self.FACTORY_2_DATA).json()

        retail_data = self.RETAIL_DATA.copy()
        retail_data['parent'] = parent1['id']
        retail = self.user_client.post(self.URL, retail_data).json()

        self.user_client.patch(f"{self.URL}{retail['id']}/", {"parent": parent2['id']})
        updated_node = Supplier.objects.get(id=retail['id'])

        self.assertEqual(updated_node.parent.id, parent2['id'])
        self.assertNotEqual(updated_node.parent.id, parent1['id'])

    def test_patch_node_to_become_parent(self):
        """
        Узел без долга может стать родителем.
        """
        response_create = self.user_client.post(self.URL, self.SUPPLIER_WITHOUT_DEBT)
        node_id = response_create.json()['id']

        child_data = self.SUPPLIER_WITHOUT_DEBT.copy()
        child_data['name'] = 'Child'
        response_child = self.user_client.post(self.URL, child_data)
        child_id = response_child.json()['id']

        patch_data = {'parent': node_id}
        response_patch = self.user_client.patch(f"{self.URL}{child_id}/", patch_data)
        self.assertEqual(response_patch.status_code, status.HTTP_200_OK)
        child_after_patch = Supplier.objects.get(id=child_id)
        self.assertEqual(child_after_patch.parent.id, node_id)

    def test_patch_node_change_level(self):
        """
        При изменении уровня узла, его дочерние узлы также должны корректно изменять свой уровень.

        Исходная структура:
            [Parent]
                |
            [Middle Node]
                |
            [Child Node]

        Операция PATCH изменяет уровень [Middle Node], удаляя его родителя (Parent) и делая его корневым узлом.

        Ожидаемая структура после PATCH:
            [Parent]

            [Middle Node]
                |
            [Child Node]

        В этой структуре:
        - [Parent] стоит отдельно.
        - [Middle Node] стал корневым узлом.
        - [Child Node] остался дочерним узлом для [Middle Node].
        """
        response_create_parent = self.user_client.post(self.URL, self.FACTORY_1_DATA)
        parent_id = response_create_parent.json()['id']

        middle_node_data = self.SUPPLIER_WITHOUT_DEBT.copy()
        middle_node_data['parent'] = parent_id
        middle_node_data['name'] = 'middle'
        response_middle_node = self.user_client.post(self.URL, middle_node_data)
        middle_node_id = response_middle_node.json()['id']

        child_data = self.SUPPLIER_WITHOUT_DEBT.copy()
        child_data['parent'] = middle_node_id
        child_data['name'] = 'child'
        child_response = self.user_client.post(self.URL, child_data)
        child_id = child_response.json()['id']

        patch_data = {'parent': ""}
        response_patch = self.user_client.patch(f"{self.URL}{middle_node_id}/", patch_data)
        self.assertEqual(response_patch.status_code, status.HTTP_200_OK)

        middle_node_after_patch = Supplier.objects.get(id=middle_node_id)
        self.assertIsNone(middle_node_after_patch.parent)
        self.assertEqual(middle_node_after_patch.level, 0)
        child_after_patch = Supplier.objects.get(id=child_id)
        self.assertEqual(child_after_patch.level, 1)

    def test_patch_supplier_with_debt(self):
        """
        Нельзя убрать родителя у звена с долгом.

        Исходная структура:

           [Родитель (без долга)]
               |
           [Ребенок (с долгом)]

        Попытка обновления родителя у ребенка:

           [Родитель (без долга)]
           [Ребенок (с долгом)] <-- Ошибка! Невозможно удалить родителя, пока у ребенка есть долг.
        """

        factory = self.user_client.post(self.URL, self.FACTORY_1_DATA)
        factory_id = factory.json()['id']

        child_with_debt_data = self.SUPPLIER_WITH_DEBT.copy()
        child_with_debt_data["parent"] = factory_id
        child_with_debt = self.user_client.post(self.URL, child_with_debt_data)
        child_with_debt_id = child_with_debt.json()['id']

        patch_data = {"parent": ""}
        response_patch = self.user_client.patch(f"{self.URL}{child_with_debt_id}/", patch_data)

        self.assertEqual(response_patch.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_patch.json().get('non_field_errors')[0],
                         'Ошибка: у звена без родителя не может быть долга')

    ...

    def test_node_change_level_and_children_update(self):
        """
        При изменении уровня узла, его дочерние узлы также должны корректно изменять свой уровень

        Схема:
            Parent --> Middle --> Child

        Создается NewParent.
        Middle меняет родителя с Parent на NewParent.
        Проверка:
            Parent
            NewParent --> Middle --> Child
        """

        parent = self.user_client.post(self.URL, self.FACTORY_1_DATA).json()

        middle_data = self.RETAIL_DATA.copy()
        middle_data['parent'] = parent['id']
        middle = self.user_client.post(self.URL, middle_data).json()

        child_data = self.ENT_DATA.copy()
        child_data['parent'] = middle['id']
        child = self.user_client.post(self.URL, child_data).json()

        new_parent = self.user_client.post(self.URL, self.FACTORY_2_DATA).json()

        patch_data = {'parent': new_parent['id']}
        self.user_client.patch(f"{self.URL}{middle['id']}/", patch_data)

        middle_refreshed = Supplier.objects.get(id=middle['id'])
        child_refreshed = Supplier.objects.get(id=child['id'])

        self.assertNotEqual(middle_refreshed.parent.id, parent['id'])
        self.assertEqual(middle_refreshed.parent.id, new_parent['id'])
        self.assertEqual(child_refreshed.parent.id, middle_refreshed.id)

    def test_subtree_restructure_on_node_update(self):
        """
        Если узел с дочерними узлами обновляется, все поддерево корректно перестраивается

        Схема:
            Parent --> Middle --> Child
        Создается NewParent.
        Parent меняет родителя на NewParent.
        Проверка:
            NewParent --> Parent --> Middle --> Child
        """

        parent = self.user_client.post(self.URL, self.SUPPLIER_WITHOUT_DEBT).json()

        middle_data = self.RETAIL_DATA.copy()
        middle_data['parent'] = parent['id']
        middle = self.user_client.post(self.URL, middle_data).json()

        child_data = self.ENT_DATA.copy()
        child_data['parent'] = middle['id']
        child = self.user_client.post(self.URL, child_data).json()

        new_parent = self.user_client.post(self.URL, self.FACTORY_2_DATA).json()

        patch_data = {'parent': new_parent['id']}
        self.user_client.patch(f"{self.URL}{parent['id']}/", patch_data)

        parent_refreshed = Supplier.objects.get(id=parent['id'])
        middle_refreshed = Supplier.objects.get(id=middle['id'])
        child_refreshed = Supplier.objects.get(id=child['id'])

        self.assertEqual(parent_refreshed.parent.id, new_parent['id'])
        self.assertEqual(middle_refreshed.parent.id, parent_refreshed.id)
        self.assertEqual(child_refreshed.parent.id, middle_refreshed.id)

    def test_change_supplier_parent_with_correct_hierarchy(self):
        """Изменение родителя с сохранением порядка иерархии"""

        response_factory_1 = self.user_client.post(self.URL, self.FACTORY_1_DATA)
        response_factory_2 = self.user_client.post(self.URL, self.FACTORY_2_DATA)

        factory_1_id = response_factory_1.json()['id']
        factory_2_id = response_factory_2.json()['id']

        retail_data = self.RETAIL_DATA.copy()
        retail_data['parent'] = factory_1_id
        response_retail = self.user_client.post(self.URL, retail_data)
        retail_id = response_retail.json()['id']

        update_data = {'parent': factory_2_id}
        self.user_client.patch(f"{self.URL}{retail_id}/", update_data)

        updated_retail = Supplier.objects.get(id=retail_id)

        self.assertEqual(updated_retail.parent.id, factory_2_id)
