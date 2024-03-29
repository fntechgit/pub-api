from rest_framework import serializers
from ..models import AbstractPubManager
import logging
import time

from ..utils.inject import inject
from django.utils.translation import ugettext_lazy as _
from rest_framework.serializers import ValidationError
from api.tasks import create_snapshot_cancellable


# Serializer without model
class EntityUpdateWriteSerializer(serializers.Serializer):

    @inject
    def __init__(self, pub_manager: AbstractPubManager, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pub_manager = pub_manager

    entity_id = serializers.IntegerField(required=True)
    entity_type = serializers.CharField(required=True, max_length=255)
    entity_operator = serializers.CharField(required=True, max_length=255)

    def validate(self, data):
        entity_id = data['entity_id'] if 'entity_id' in data else None
        entity_type = data['entity_type'] if 'entity_type' in data else None
        entity_operator = data['entity_operator'] if 'entity_operator' in data else None

        if entity_id is None:
            raise ValidationError(_("entity_id is mandatory."))

        if not isinstance(entity_id, int):
            raise ValidationError(_("entity_id should be integer."))

        if entity_type is None:
            raise ValidationError(_("entity_type is mandatory."))

        if not isinstance(entity_type, str):
            raise ValidationError(_("entity_type should be string."))

        valid_entity_types = ["SummitEvent", "Presentation"]

        if entity_type not in valid_entity_types:
            raise ValidationError(
                _('entity_type is not valid ({values})'.format(values=' '.join(map(str, valid_entity_types)))))

        if entity_operator is None:
            raise ValidationError(_("entity_operator is mandatory."))

        if not isinstance(entity_operator, str):
            raise ValidationError(_("entity_operator should be string."))

        valid_entity_operators = ["INSERT", "UPDATE", "DELETE"]

        if entity_operator not in valid_entity_operators:
            raise ValidationError(
                _('entity_operator is not valid ({values})'.format(values=' '.join(map(str, valid_entity_operators)))))

        return data

    def update(self, instance, validated_data):
        return instance

    def get_summit_id(self):
        summit_id = self.context.get('summit_id')
        return summit_id

    def create(self, validated_data):
        try:

            summit_id = self.get_summit_id()
            entity_id = validated_data['entity_id']
            entity_type = validated_data['entity_type']
            entity_operator = validated_data['entity_operator']

            # publish
            self.pub_manager.pub(summit_id, entity_id, entity_type, entity_operator, round(time.time() * 1000))

            create_snapshot_cancellable(summit_id)

            return {"summit_id": summit_id,
                    "entity_id": entity_id,
                    "entity_type": entity_type,
                    "entity_operator": entity_operator}

        except Exception as e:
            logging.getLogger('api').error(e)
            raise
