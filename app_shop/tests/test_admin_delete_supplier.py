from django.urls import reverse

from app_shop.models import Supplier
from app_shop.tests.test_admin_create_supplier import BaseAdminTestCase


class SupplierDeleteAdminTestCase(BaseAdminTestCase):
    def setUp(self):
        super().setUp()
        self.ADD_URL = reverse('admin:app_shop_supplier_add')

    def test_admin_delete_supplier_without_debt_and_children(self):
        """
        Можно удалить звено без долга и без детей через админ-панель
        """

        response_create = self.admin_client.post(self.ADD_URL, self.SUPPLIER_WITHOUT_DEBT)
        self.assertEqual(response_create.status_code, 302)

        supplier_id = Supplier.objects.latest('id').id
        initial_count = Supplier.objects.count()

        delete_url = f"/admin/app_shop/supplier/{supplier_id}/delete/"

        post_data = {
            'post': 'yes',
        }
        response_delete = self.admin_client.post(delete_url, post_data)

        final_count = Supplier.objects.count()
        self.assertEqual(response_delete.status_code, 302)
        self.assertEqual(initial_count - 1, final_count)

    def test_admin_delete_supplier_with_debt(self):
        """
        Нельзя удалить звено с долгом через админ-панель
        """
        factory = self.admin_client.post(self.ADD_URL, self.FACTORY_1_DATA)
        self.assertEqual(factory.status_code, 302)

        factory_id = Supplier.objects.latest('id').id

        child_with_debt_data = self.SUPPLIER_WITH_DEBT.copy()
        child_with_debt_data["parent"] = factory_id
        child_with_debt = self.admin_client.post(self.ADD_URL, child_with_debt_data)
        self.assertEqual(child_with_debt.status_code, 302)

        child_with_debt_id = Supplier.objects.latest('id').id
        delete_url = f"/admin/app_shop/supplier/{child_with_debt_id}/delete/"

        post_data = {
            'post': 'yes',
        }
        self.admin_client.post(delete_url, post_data)
        self.assertTrue(Supplier.objects.filter(id=child_with_debt_id).exists())

    def test_admin_delete_parent_with_child_having_debt(self):
        """
        Нельзя удалить родителя через админ-панель, если у ребенка есть долг
        """
        response_create_parent = self.admin_client.post(self.ADD_URL, self.FACTORY_1_DATA)
        self.assertEqual(response_create_parent.status_code, 302)
        parent_id = Supplier.objects.latest('id').id

        child_with_debt = self.SUPPLIER_WITH_DEBT.copy()
        child_with_debt['parent'] = parent_id
        response_create_child = self.admin_client.post(self.ADD_URL, child_with_debt)
        self.assertEqual(response_create_child.status_code, 302)

        delete_url = f"/admin/app_shop/supplier/{parent_id}/delete/"
        post_data = {
            'post': 'yes',
        }
        self.admin_client.post(delete_url, post_data)
        self.assertTrue(Supplier.objects.filter(id=parent_id).exists())

    def test_admin_delete_parent_with_child_without_debt_and_check_mptt_restructuring(self):
        """
        Проверка корректного перестроения дерева после удаления родителя через админ-панель.
        """
        response_create_parent = self.admin_client.post(self.ADD_URL, self.FACTORY_1_DATA)
        self.assertEqual(response_create_parent.status_code, 302)
        parent_id = Supplier.objects.latest('id').id

        child_without_debt_data = self.SUPPLIER_WITHOUT_DEBT.copy()
        child_without_debt_data['parent'] = parent_id
        response_create_child = self.admin_client.post(self.ADD_URL, child_without_debt_data)
        self.assertEqual(response_create_child.status_code, 302)
        child_id = Supplier.objects.latest('id').id

        delete_url = f"/admin/app_shop/supplier/{parent_id}/delete/"

        post_data = {
            'post': 'yes',
        }
        self.admin_client.post(delete_url, post_data)

        with self.assertRaises(Supplier.DoesNotExist):
            Supplier.objects.get(id=parent_id)

        child_after_delete = Supplier.objects.get(id=child_id)

        self.assertIsNone(child_after_delete.parent)
        self.assertEqual(child_after_delete.level, 0)

    def test_admin_delete_parent_with_two_children_without_debt_and_check_mptt_restructuring(self):
        """
        Проверка корректного перестроения дерева после удаления родителя через админ-панель.
        """
        # 1. Создание объектов
        response_create_parent = self.admin_client.post(self.ADD_URL, self.FACTORY_1_DATA)
        self.assertEqual(response_create_parent.status_code, 302)
        parent_id = Supplier.objects.latest('id').id

        child1_without_debt_data = self.SUPPLIER_WITHOUT_DEBT.copy()
        child1_without_debt_data['parent'] = parent_id
        child1_without_debt_data['name'] = 'child1'
        response_create_child1 = self.admin_client.post(self.ADD_URL, child1_without_debt_data)
        self.assertEqual(response_create_child1.status_code, 302)
        child1_id = Supplier.objects.latest('id').id

        child2_without_debt_data = self.SUPPLIER_WITHOUT_DEBT.copy()
        child2_without_debt_data['parent'] = parent_id
        child2_without_debt_data['name'] = 'child2'
        response_create_child2 = self.admin_client.post(self.ADD_URL, child2_without_debt_data)
        self.assertEqual(response_create_child2.status_code, 302)
        child2_id = Supplier.objects.latest('id').id

        delete_url = f"/admin/app_shop/supplier/{parent_id}/delete/"

        post_data = {
            'post': 'yes',
        }
        response_delete = self.admin_client.post(delete_url, post_data)
        self.assertEqual(response_delete.status_code, 302)

        with self.assertRaises(Supplier.DoesNotExist):
            Supplier.objects.get(id=parent_id)

        child1_after_delete = Supplier.objects.get(id=child1_id)
        child2_after_delete = Supplier.objects.get(id=child2_id)

        self.assertIsNone(child1_after_delete.parent)
        self.assertIsNone(child2_after_delete.parent)
        self.assertEqual(child1_after_delete.level, 0)
        self.assertEqual(child2_after_delete.level, 0)

        all_trees = Supplier.objects.all().order_by('tree_id').distinct('tree_id')
        self.assertEqual(all_trees.count(), 2)

    def test_admin_fail_to_delete_parent_with_child1_and_child2_having_debt(self):
        """
        Проверка удаления родителя через админ-панель при наличии у ребенка 1 ребенка 2 с долгом.
        """
        response_create_parent = self.admin_client.post(self.ADD_URL, self.FACTORY_1_DATA)
        self.assertEqual(response_create_parent.status_code, 302)
        parent_id = Supplier.objects.latest('id').id

        child1_without_debt_data = self.SUPPLIER_WITHOUT_DEBT.copy()
        child1_without_debt_data['parent'] = parent_id
        response_create_child1 = self.admin_client.post(self.ADD_URL, child1_without_debt_data)
        self.assertEqual(response_create_child1.status_code, 302)
        child1_id = Supplier.objects.latest('id').id

        child2_with_debt_data = self.SUPPLIER_WITH_DEBT.copy()
        child2_with_debt_data['parent'] = child1_id
        response_create_child2 = self.admin_client.post(self.ADD_URL, child2_with_debt_data)
        self.assertEqual(response_create_child2.status_code, 302)
        child2_id = Supplier.objects.latest('id').id

        delete_url = f"/admin/app_shop/supplier/{parent_id}/delete/"
        post_data = {
            'post': 'yes',
        }
        response_delete = self.admin_client.post(delete_url, post_data)
        self.assertEqual(response_delete.status_code, 302)

        with self.assertRaises(Supplier.DoesNotExist):
            Supplier.objects.get(id=parent_id)

        child1_after_delete = Supplier.objects.get(id=child1_id)
        child2_after_delete = Supplier.objects.get(id=child2_id)

        self.assertIsNone(child1_after_delete.parent)
        self.assertEqual(child1_after_delete.level, 0)
        self.assertEqual(child2_after_delete.parent.id, child1_id)
        self.assertEqual(child2_after_delete.level, 1)

        distinct_tree_ids = Supplier.objects.values('tree_id').distinct().count()
        self.assertEqual(distinct_tree_ids, 1)

    def test_admin_delete_node_having_parent_and_child(self):
        """
        Проверка удаления узла через админ-панель при наличии родителя и ребенка у этого узла.
        """
        response_create_parent = self.admin_client.post(self.ADD_URL, self.FACTORY_1_DATA)
        self.assertEqual(response_create_parent.status_code, 302)
        parent_id = Supplier.objects.latest('id').id

        middle_node_data = self.SUPPLIER_WITHOUT_DEBT.copy()
        middle_node_data['name'] = 'middle_node'
        middle_node_data['parent'] = parent_id
        response_middle_node = self.admin_client.post(self.ADD_URL, middle_node_data)
        self.assertEqual(response_middle_node.status_code, 302)
        middle_node_id = Supplier.objects.latest('id').id

        child_data = self.SUPPLIER_WITHOUT_DEBT.copy()
        child_data['name'] = 'child_of_middle_node'
        child_data['parent'] = middle_node_id
        child_response = self.admin_client.post(self.ADD_URL, child_data)
        self.assertEqual(child_response.status_code, 302)
        child_id = Supplier.objects.latest('id').id

        delete_url = f"/admin/app_shop/supplier/{middle_node_id}/delete/"

        post_data = {
            'post': 'yes',
        }
        response_delete = self.admin_client.post(delete_url, post_data)
        self.assertEqual(response_delete.status_code, 302)

        with self.assertRaises(Supplier.DoesNotExist):
            Supplier.objects.get(id=middle_node_id)

        child_after_delete = Supplier.objects.get(id=child_id)
        self.assertEqual(child_after_delete.parent.id, parent_id)
        self.assertEqual(child_after_delete.level, 1)

    def test_admin_delete_node_with_multiple_children(self):
        """
        Проверка удаления узла с несколькими детьми через админ-панель.
        """

        response_create_parent = self.admin_client.post(self.ADD_URL, self.FACTORY_1_DATA)
        self.assertEqual(response_create_parent.status_code, 302)
        parent_id = Supplier.objects.latest('id').id

        node_data = self.SUPPLIER_WITHOUT_DEBT.copy()
        node_data['name'] = 'Node'
        node_data['parent'] = parent_id
        response_node = self.admin_client.post(self.ADD_URL, node_data)
        self.assertEqual(response_node.status_code, 302)
        node_id = Supplier.objects.latest('id').id

        children_ids = []
        for i in range(1, 4):
            child_data = self.SUPPLIER_WITHOUT_DEBT.copy()
            child_data['name'] = f'Child{i}'
            child_data['parent'] = node_id
            child_response = self.admin_client.post(self.ADD_URL, child_data)
            self.assertEqual(child_response.status_code, 302)
            children_ids.append(Supplier.objects.latest('id').id)

        delete_url = f"/admin/app_shop/supplier/{node_id}/delete/"
        post_data = {
            'post': 'yes',
        }
        response_delete = self.admin_client.post(delete_url, post_data)
        self.assertEqual(response_delete.status_code, 302)

        with self.assertRaises(Supplier.DoesNotExist):
            Supplier.objects.get(id=node_id)

        for child_id in children_ids:
            child = Supplier.objects.get(id=child_id)
            self.assertEqual(child.parent.id, parent_id)
            self.assertIn(child.name, ['Child1', 'Child2', 'Child3'])

    from django.urls import reverse

    def test_admin_delete_node_with_multiple_children_by_action(self):
        """
        Проверка удаления узла с несколькими детьми через действие админ-панели.
        """

        response_create_parent = self.admin_client.post(self.ADD_URL, self.FACTORY_1_DATA)
        self.assertEqual(response_create_parent.status_code, 302)
        parent_id = Supplier.objects.latest('id').id

        node_data = self.SUPPLIER_WITHOUT_DEBT.copy()
        node_data['name'] = 'Node'
        node_data['parent'] = parent_id
        response_node = self.admin_client.post(self.ADD_URL, node_data)
        self.assertEqual(response_node.status_code, 302)
        node_id = Supplier.objects.latest('id').id

        children_ids = []
        for i in range(1, 4):
            child_data = self.SUPPLIER_WITHOUT_DEBT.copy()
            child_data['name'] = f'Child{i}'
            child_data['parent'] = node_id
            child_response = self.admin_client.post(self.ADD_URL, child_data)
            self.assertEqual(child_response.status_code, 302)
            children_ids.append(Supplier.objects.latest('id').id)

        changelist_url = reverse('admin:app_shop_supplier_changelist')
        post_data = {
            'action': 'delete_selected',
            '_selected_action': [str(node_id)],
            'post': 'yes',
        }
        response_delete = self.admin_client.post(changelist_url, post_data)
        self.assertEqual(response_delete.status_code, 302)

        with self.assertRaises(Supplier.DoesNotExist):
            Supplier.objects.get(id=node_id)

        for child_id in children_ids:
            child = Supplier.objects.get(id=child_id)
            self.assertEqual(child.parent.id, parent_id)
            self.assertIn(child.name, ['Child1', 'Child2', 'Child3'])

    def test_admin_delete_parent_with_child_having_debt_by_action(self):
        """
        Нельзя удалить родителя через админ-панель, если у ребенка есть долг.
        """

        response_create_parent = self.admin_client.post(self.ADD_URL, self.FACTORY_1_DATA)
        self.assertEqual(response_create_parent.status_code, 302)
        parent_id = Supplier.objects.latest('id').id

        child_with_debt = self.SUPPLIER_WITH_DEBT.copy()
        child_with_debt['parent'] = parent_id
        response_create_child = self.admin_client.post(self.ADD_URL, child_with_debt)
        self.assertEqual(response_create_child.status_code, 302)

        changelist_url = reverse('admin:app_shop_supplier_changelist')
        post_data = {
            'action': 'delete_selected',
            '_selected_action': [str(parent_id)],
            'post': 'yes',
        }
        self.admin_client.post(changelist_url, post_data)
        self.assertTrue(Supplier.objects.filter(id=parent_id).exists())
