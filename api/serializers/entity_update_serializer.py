from rest_framework import serializers
from ..models import AbstractPubService
import logging
from ..utils.inject import inject


# Serializer without model
class EntityUpdateWriteSerializer(serializers.Serializer):

    @inject
    def __init__(self, service: AbstractPubService,  *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = service

    entity_id = serializers.IntegerField(required=True)
    entity_type = serializers.CharField(required=True, max_length=255)
    entity_operator = serializers.CharField(required=True, max_length=255)

    def validate(self, data):
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
            res = self.service.pub(summit_id, entity_id, entity_type, entity_operator)
            if not res:
                raise Exception("SUPABASE Exception")

            return {"summit_id": summit_id, "entity_id": entity_id, "entity_type": entity_type, "entity_operator" : entity_operator}
        except Exception as e:
            logging.getLogger('api').error(e)
            raise

