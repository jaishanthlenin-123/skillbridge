from rest_framework import serializers
from .models import FAQ, FAQCategory

class FAQCategorySerializer(serializers.ModelSerializer):
    faq_count = serializers.IntegerField(source='faqs.count', read_only=True)

    class Meta:
        model = FAQCategory
        fields = ('id', 'name', 'slug', 'order_index', 'faq_count')

class FAQSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True, default='')

    class Meta:
        model = FAQ
        fields = ('id', 'category', 'category_name', 'question', 'answer', 'order_index', 'is_active', 'created_at')
