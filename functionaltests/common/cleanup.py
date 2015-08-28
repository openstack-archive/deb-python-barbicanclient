"""
Copyright 2015 IBM

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""


class CleanUp(object):

    def __init__(self, barbicanclient):
        self.created_entities = {
            'secret': [],
            'container': [],
            'order': []
        }

        self.barbicanclient = barbicanclient

    def delete_all_entities(self):
        """Helper method to delete all containers and secrets used for
        testing"""
        self._delete_all_containers()
        self._delete_all_orders()
        self._delete_all_secrets()

    def add_entity(self, entity):
        """Stores an entity in Barbican to be used for testing
        and keeps track of entity for removal after tests are
        run"""
        entity_type = str(type(entity)).lower()
        if 'secret' in entity_type:
            entity_ref = entity.store()
            entity_type = 'secret'
        elif 'container' in entity_type:
            entity_ref = entity.store()
            entity_type = 'container'
        else:
            entity_ref = entity.submit()
            entity_type = 'order'

        self.created_entities[entity_type].append(entity_ref)
        return entity_ref

    def _delete_all_containers(self):
        """Helper method to delete all containers used for
        testing"""
        for container_ref in self.created_entities['container']:
            self.barbicanclient.containers.delete(container_ref)

    def _delete_all_secrets(self):
        """Helper method to delete all secrets used for testing"""
        for secret_ref in self.created_entities['secret']:
            self.barbicanclient.secrets.delete(secret_ref)

    def _delete_all_orders(self):
        """Helper method to delete all orders and secrets used for testing"""
        for order_ref in self.created_entities['order']:
            order = self.barbicanclient.orders.get(order_ref)
            if order.secret_ref:
                self.barbicanclient.secrets.delete(order.secret_ref)
            # see if containers are supported
            container_attr_exists = getattr(order, "container_ref", None)
            if container_attr_exists and order.container_ref:
                self.barbicanclient.containers.delete(order.container_ref)

            self.barbicanclient.orders.delete(order_ref)
