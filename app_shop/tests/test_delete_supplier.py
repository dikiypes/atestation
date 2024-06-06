from rest_framework import status

from app_shop.models import Supplier, Product
from app_shop.tests.base_test import BaseTestCase


class SupplierDeleteAPITestCase(BaseTestCase):

    def test_delete_supplier_without_debt_and_children(self):
        """
        Можно удалить звено без долга и без детей

        Исходная структура:
            [Родитель]
        После удаления:
            (Ничего не осталось)
        """
        response_create = self.user_client.post(self.URL, self.SUPPLIER_WITHOUT_DEBT)
        supplier_id = response_create.json()['id']
        initial_count = Supplier.objects.count()

        response_delete = self.user_client.delete(f"{self.URL}{supplier_id}/")
        final_count = Supplier.objects.count()
        self.assertEqual(response_delete.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(initial_count - 1, final_count)

    def test_delete_supplier_with_debt(self):
        """
        Нельзя удалить звено с долгом

        Исходная структура:

           [Родитель (без долга)]
               |
           [Ребенок (с долгом)]

        Попытка удаления родителя:

           [Родитель (без долга)] <-- Ошибка! Невозможно удалить, пока у ребенка есть долг.
               |
           [Ребенок (с долгом)]
        """
        factory = self.user_client.post(self.URL, self.FACTORY_1_DATA)
        factory_id = factory.json()['id']

        child_with_debt_data = self.SUPPLIER_WITH_DEBT.copy()
        child_with_debt_data["parent"] = factory_id
        child_with_debt = self.user_client.post(self.URL, child_with_debt_data)
        child_with_debt_id = child_with_debt.json()['id']

        response_delete = self.user_client.delete(f"{self.URL}{child_with_debt_id}/")
        self.assertEqual(response_delete.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_delete.json().get('error'),
                         f'Ошибка: нельзя удалить звено {child_with_debt_data["name"]} с долгом перед поставщиком')

    def test_delete_parent_with_child_having_debt(self):
        """
        Нельзя удалить родителя, у которого на следующем уровне иерархии есть ребенок с долгом.

        Исходная структура:

           [Родитель]
               |
           [Ребенок (с долгом)]

        Попытка удаления родителя:

           [Родитель] <-- Ошибка! Нельзя удалить, так как у ребенка на следующем уровне иерархии есть долг.
               |
           [Ребенок (с долгом)]
        """

        response_create_parent = self.user_client.post(self.URL, self.FACTORY_1_DATA)
        parent_id = response_create_parent.json()['id']

        child_with_debt = self.SUPPLIER_WITH_DEBT.copy()
        child_with_debt['parent'] = parent_id
        self.user_client.post(self.URL, child_with_debt)

        response_delete = self.user_client.delete(f"{self.URL}{parent_id}/")
        self.assertEqual(response_delete.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_delete.json().get('error'),
                         f'Ошибка: нельзя удалить звено {self.FACTORY_1_DATA["name"]}, '
                         f'так как у его поставщика {child_with_debt["name"]} на следующем уровне иерархии есть долг')

    def test_delete_parent_with_child_without_debt_and_check_mptt_restructuring(self):
        """
        Проверка корректного перестроения дерева после удаления родительского звена, имеющего ребенка без долга

        Исходная структура:

           [Родитель]
               |
           [Ребенок (без долга)]

        После удаления родителя:

            [Ребенок (без долга)] <-- Стал корневым узлом, уровень 0, нет родителя.
        """

        response_create_parent = self.user_client.post(self.URL, self.FACTORY_1_DATA)
        parent_id = response_create_parent.json()['id']

        child_without_debt_data = self.SUPPLIER_WITHOUT_DEBT.copy()
        child_without_debt_data['parent'] = parent_id
        child_without_debt = self.user_client.post(self.URL, child_without_debt_data)
        child_id = child_without_debt.json()['id']

        response_delete = self.user_client.delete(f"{self.URL}{parent_id}/")
        self.assertEqual(response_delete.status_code, status.HTTP_204_NO_CONTENT)

        child_after_delete = Supplier.objects.get(id=child_id)

        self.assertIsNone(child_after_delete.parent)
        self.assertEqual(child_after_delete.level, 0)

    def test_delete_parent_with_two_children_without_debt_and_check_mptt_restructuring(self):
        """
        Проверка корректного перестроения дерева после удаления родительского звена,
        имеющего двух детей без долга

        Исходная структура:

               [Родитель]
                /     \
            [child1] [child2]
            (без долга) (без долга)

        После удаления родителя:

            [child1]  [child2]
               |        |
              корень   корень

        Два отдельных дерева с корневыми узлами (child1 и child2), каждый на уровне 0, без родителей.
        """

        response_create_parent = self.user_client.post(self.URL, self.FACTORY_1_DATA)
        parent_id = response_create_parent.json()['id']

        child1_without_debt_data = self.SUPPLIER_WITHOUT_DEBT.copy()
        child1_without_debt_data['parent'] = parent_id
        child1_without_debt_data['name'] = 'child1'
        child1_without_debt = self.user_client.post(self.URL, child1_without_debt_data)
        child1_id = child1_without_debt.json()['id']

        child2_without_debt_data = self.SUPPLIER_WITHOUT_DEBT.copy()
        child2_without_debt_data['parent'] = parent_id
        child1_without_debt_data['name'] = 'child2'
        child2_without_debt = self.user_client.post(self.URL, child2_without_debt_data)
        child2_id = child2_without_debt.json()['id']

        response_delete = self.user_client.delete(f"{self.URL}{parent_id}/")
        self.assertEqual(response_delete.status_code, status.HTTP_204_NO_CONTENT)

        child1_after_delete = Supplier.objects.get(id=child1_id)
        child2_after_delete = Supplier.objects.get(id=child2_id)

        self.assertIsNone(child1_after_delete.parent)
        self.assertIsNone(child2_after_delete.parent)

        self.assertEqual(child1_after_delete.level, 0)
        self.assertEqual(child2_after_delete.level, 0)

        all_trees = Supplier.objects.all().order_by('tree_id').distinct('tree_id')
        self.assertEqual(all_trees.count(), 2)

    def test_fail_to_delete_parent_with_child1_and_child2_having_debt(self):
        """
        Проверка корректного перестроения дерева после удаления родителя,
        имеющего ребенка 1, а ребенок 1 имеет ребенка 2 с долгом

        Исходная структура:

            [Родитель]
                |
            [child1]
                |
            [child2]
            (с долгом)

        Так как у [child1] нет долга, удаление [Родитель] допустимо

        Ожидаемая структура после удаления:

            [child1]
                |
            [child2]
            (с долгом)

        [child1] становится корневым узлом с уровнем 0,
        а [child2] продолжает быть дочерним узлом для [child1] и находится на уровне 1.
        Остается одно дерево.
        """

        response_create_parent = self.user_client.post(self.URL, self.FACTORY_1_DATA)
        parent_id = response_create_parent.json()['id']

        child1_without_debt_data = self.SUPPLIER_WITHOUT_DEBT.copy()
        child1_without_debt_data['parent'] = parent_id
        child1 = self.user_client.post(self.URL, child1_without_debt_data)
        child1_id = child1.json()['id']

        child2_with_debt_data = self.SUPPLIER_WITH_DEBT.copy()
        child2_with_debt_data['parent'] = child1_id
        child2 = self.user_client.post(self.URL, child2_with_debt_data)
        child2_id = child2.json()['id']

        response_delete = self.user_client.delete(f"{self.URL}{parent_id}/")
        self.assertEqual(response_delete.status_code, status.HTTP_204_NO_CONTENT)

        child1_after_delete = Supplier.objects.get(id=child1_id)
        self.assertIsNone(child1_after_delete.parent)
        self.assertEqual(child1_after_delete.level, 0)

        child2_after_delete = Supplier.objects.get(id=child2_id)
        self.assertEqual(child2_after_delete.parent.id, child1_id)
        self.assertEqual(child2_after_delete.level, 1)

        distinct_tree_ids = Supplier.objects.values('tree_id').distinct().count()
        self.assertEqual(distinct_tree_ids, 1)

    def test_delete_node_having_parent_and_child(self):
        """
        Проверка корректного перестроения дерева при удалении узла, который имеет родителя и ребенка одновременно

        Исходная структура:

            [Родитель]
                |
            [middle_node]
                |
            [child_of_middle_node]

        При удалении [middle_node], [child_of_middle_node] становится прямым ребенком [Родитель]

        Ожидаемая структура после удаления:

            [Родитель]
                |
            [child_of_middle_node]

        [child_of_middle_node] теперь является дочерним узлом для [Родитель] и находится на уровне 1.
        """

        response_create_parent = self.user_client.post(self.URL, self.FACTORY_1_DATA)
        parent_id = response_create_parent.json()['id']

        middle_node_data = self.SUPPLIER_WITHOUT_DEBT.copy()
        middle_node_data['name'] = 'middle_node'
        middle_node_data['parent'] = parent_id
        response_middle_node = self.user_client.post(self.URL, middle_node_data)
        middle_node_id = response_middle_node.json()['id']

        child_data = self.SUPPLIER_WITHOUT_DEBT.copy()
        child_data['name'] = 'child_of_middle_node'
        child_data['parent'] = middle_node_id
        child_response = self.user_client.post(self.URL, child_data)
        child_id = child_response.json()['id']

        response_delete = self.user_client.delete(f"{self.URL}{middle_node_id}/")
        self.assertEqual(response_delete.status_code, status.HTTP_204_NO_CONTENT)

        child_after_delete = Supplier.objects.get(id=child_id)
        self.assertEqual(child_after_delete.parent.id, parent_id)
        self.assertEqual(child_after_delete.level, 1)

    def test_delete_node_with_multiple_children(self):
        """
        Проверка корректного перестроения дерева при удалении узла, который имеет несколько детей"

        Исходная структура:

                [Родитель]
                    |
                   [Node]
                   / | \
            Child1 Child2 Child3

        При удалении [Node], все дочерние элементы (Child1, Child2, Child3) становятся
        прямыми дочерними элементами [Родитель]

        Ожидаемая структура после удаления:

                [Родитель]
                  / | \
            Child1 Child2 Child3

        Теперь все Child1, Child2, Child3 являются прямыми дочерними элементами для [Родитель].
        """

        response_create_parent = self.user_client.post(self.URL, self.FACTORY_1_DATA)
        parent_id = response_create_parent.json()['id']

        node_data = self.SUPPLIER_WITHOUT_DEBT.copy()
        node_data['name'] = 'Node'
        node_data['parent'] = parent_id
        response_node = self.user_client.post(self.URL, node_data)
        node_id = response_node.json()['id']

        children_ids = []
        for i in range(1, 4):
            child_data = self.SUPPLIER_WITHOUT_DEBT.copy()
            child_data['name'] = f'Child{i}'
            child_data['parent'] = node_id
            child_response = self.user_client.post(self.URL, child_data)
            children_ids.append(child_response.json()['id'])

        self.user_client.delete(f"{self.URL}{node_id}/")

        for child_id in children_ids:
            child = Supplier.objects.get(id=child_id)
            self.assertEqual(child.parent.id, parent_id)
            self.assertIn(child.name, ['Child1', 'Child2', 'Child3'])

    def test_delete_node_c_with_children_on_multiple_levels(self):
        """
        Проверка корректного перестроения дерева при удалении узла в дерево с большим количеством уровней

        Исходная структура:
                A
               / \
              C   D
             / \ / \
            F   G H  I

        Ожидаемая структура после удаления:

                A
              / | \
             F  D  G
                / \
               H   I
        """

        # Создаем узел A
        data_a = self.SUPPLIER_WITHOUT_DEBT.copy()
        data_a['name'] = 'A'
        response_create_a = self.user_client.post(self.URL, data_a)
        a_id = response_create_a.json()['id']

        # Создаем узел C с родителем A
        data_c = self.SUPPLIER_WITHOUT_DEBT.copy()
        data_c['name'] = 'C'
        data_c['parent'] = a_id
        response_create_c = self.user_client.post(self.URL, data_c)
        c_id = response_create_c.json()['id']

        # Создаем узел D с родителем A
        data_d = self.SUPPLIER_WITHOUT_DEBT.copy()
        data_d['name'] = 'D'
        data_d['parent'] = a_id
        response_create_d = self.user_client.post(self.URL, data_d)
        d_id = response_create_d.json()['id']

        # Создаем узлы F и G с родителем C
        data_f = self.SUPPLIER_WITHOUT_DEBT.copy()
        data_f['name'] = 'F'
        data_f['parent'] = c_id
        response_create_f = self.user_client.post(self.URL, data_f)
        f_id = response_create_f.json()['id']

        data_g = self.SUPPLIER_WITHOUT_DEBT.copy()
        data_g['name'] = 'G'
        data_g['parent'] = c_id
        response_create_g = self.user_client.post(self.URL, data_g)
        g_id = response_create_g.json()['id']

        # Создаем узлы H и I с родителем D
        data_h = self.SUPPLIER_WITHOUT_DEBT.copy()
        data_h['name'] = 'H'
        data_h['parent'] = d_id
        response_create_h = self.user_client.post(self.URL, data_h)
        h_id = response_create_h.json()['id']

        data_i = self.SUPPLIER_WITHOUT_DEBT.copy()
        data_i['name'] = 'I'
        data_i['parent'] = d_id
        response_create_i = self.user_client.post(self.URL, data_i)
        i_id = response_create_i.json()['id']

        # Удаляем узел C
        self.user_client.delete(f"{self.URL}{c_id}/")

        # Проверяем структуру после удаления
        f_after_delete = Supplier.objects.get(id=f_id)
        g_after_delete = Supplier.objects.get(id=g_id)
        d_after_delete = Supplier.objects.get(id=d_id)
        h_after_delete = Supplier.objects.get(id=h_id)
        i_after_delete = Supplier.objects.get(id=i_id)

        self.assertEqual(f_after_delete.parent.id, a_id)
        self.assertEqual(g_after_delete.parent.id, a_id)
        self.assertEqual(d_after_delete.parent.id, a_id)
        self.assertEqual(h_after_delete.parent.id, d_id)
        self.assertEqual(i_after_delete.parent.id, d_id)

        # Проверка уровней узлов
        self.assertEqual(f_after_delete.level, 1)  # Уровень узла F после удаления
        self.assertEqual(g_after_delete.level, 1)  # Уровень узла G после удаления
        self.assertEqual(d_after_delete.level, 1)  # Уровень узла D после удаления
        self.assertEqual(h_after_delete.level, 2)  # Уровень узла H после удаления
        self.assertEqual(i_after_delete.level, 2)  # Уровень узла I после удаления

        # Проверка количества детей у каждого узла
        children_of_a = Supplier.objects.filter(parent=a_id)
        children_of_d = Supplier.objects.filter(parent=d_id)
        self.assertEqual(children_of_a.count(), 3)  # У узла A должно быть 3 дочерних узла
        self.assertEqual(children_of_d.count(), 2)  # У узла D должно быть 2 дочерних узла

    def test_add_node_after_deletion(self):
        """
        Исходная иерархия:
            Root
            |
            NodeA

        После удаления NodeA:
            Root

        После добавления NodeB:
            Root
            |
            NodeB
        """

        data_root = self.SUPPLIER_WITHOUT_DEBT.copy()
        data_root['name'] = 'Root'
        response_create_root = self.user_client.post(self.URL, data_root)
        root_id = response_create_root.json()['id']

        data_a = self.SUPPLIER_WITHOUT_DEBT.copy()
        data_a['name'] = 'NodeA'
        data_a['parent'] = root_id
        response_create_a = self.user_client.post(self.URL, data_a)
        a_id = response_create_a.json()['id']

        self.user_client.delete(f"{self.URL}{a_id}/")

        data_b = self.SUPPLIER_WITHOUT_DEBT.copy()
        data_b['name'] = 'NodeB'
        data_b['parent'] = root_id
        self.user_client.post(self.URL, data_b)

    def test_delete_and_add_nodes(self):
        """
        Исходная иерархия:
            Root1
            |
            Node1 - Node2

        После удаления Node2:
            Root1
            |
            Node1

        После добавления Node3:
            Root1
            |
            Node1 - Node3

        После удаления Root1:
            Node1 - Node3

        После добавления Node4 к Node3:
            Node3
            |
            Node4
        """
        # Создаем узел Root1
        data_root1 = self.SUPPLIER_WITHOUT_DEBT.copy()
        data_root1['name'] = 'Root1'
        response_create_root1 = self.user_client.post(self.URL, data_root1)
        root1_id = response_create_root1.json()['id']

        # Создаем узлы Node1 и Node2 с родителем Root1
        data_node1 = self.SUPPLIER_WITHOUT_DEBT.copy()
        data_node1['name'] = 'Node1'
        data_node1['parent'] = root1_id
        self.user_client.post(self.URL, data_node1)

        data_node2 = self.SUPPLIER_WITHOUT_DEBT.copy()
        data_node2['name'] = 'Node2'
        data_node2['parent'] = root1_id
        response_create_node2 = self.user_client.post(self.URL, data_node2)
        node2_id = response_create_node2.json()['id']

        # Удаляем узел Node2
        self.user_client.delete(f"{self.URL}{node2_id}/")

        # Создаем узел Node3 с родителем Root1
        data_node3 = self.SUPPLIER_WITHOUT_DEBT.copy()
        data_node3['name'] = 'Node3'
        data_node3['parent'] = root1_id
        response_create_node3 = self.user_client.post(self.URL, data_node3)
        node3_id = response_create_node3.json()['id']

        # Удаляем узел Root1
        self.user_client.delete(f"{self.URL}{root1_id}/")

        # Создаем узел Node4 с родителем Node3
        data_node4 = self.SUPPLIER_WITHOUT_DEBT.copy()
        data_node4['name'] = 'Node4'
        data_node4['parent'] = node3_id
        self.user_client.post(self.URL, data_node4)

    def test_delete_supplier_via_api_deletes_related_products(self):
        """При удалении поставщика, связанные с ним продукты также удаляются"""

        response = self.user_client.post(self.URL, self.FACTORY_1_DATA)
        supplier_id = response.json()['id']

        product_data = self.PRODUCT.copy()
        product_data['supplier'] = supplier_id
        self.user_client.post(self.URL_PRODUCT, product_data)

        self.assertEqual(Product.objects.filter(supplier_id=supplier_id).count(), 1)

        response = self.user_client.delete(f"{self.URL}{supplier_id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Product.objects.filter(supplier_id=supplier_id).count(), 0)
