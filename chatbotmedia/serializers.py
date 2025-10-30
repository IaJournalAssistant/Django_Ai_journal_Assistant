from rest_framework import serializers
from .models import ImageEntry

class ImageEntrySerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ImageEntry
        fields = '__all__'
        read_only_fields = ['extracted_text', 'sentiment', 'emotion', 'user']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url
