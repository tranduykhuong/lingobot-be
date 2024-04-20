from http import HTTPStatus
from itertools import groupby

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import LimitOffsetPagination

from history.models import ParaphraseHistory
from history.serializers.paraphrase_history_serializer import ParaphraseHistorySerializer


class ParaphraseHistoryViewset(viewsets.ModelViewSet):
    queryset = ParaphraseHistory.objects.all()
    serializer_class = ParaphraseHistorySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = LimitOffsetPagination

    def list(self, request, *args, **kwargs):
        user = request.user

        queryset = ParaphraseHistory.objects.filter(
            user=user
        ).order_by('-created_at')

        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.serializer_class(queryset, many=True)
        return Response(data=serializer.data, status=HTTPStatus.OK)
    
    def create(self, request, *args, **kwargs):
        user = request.user
        data = request.data

        instance = ParaphraseHistory.objects.create(
            user=user,
            model_type=data['modelType'],
            text_style=data['textStyle'],
            input=data['input'],
            output=data['output'],
        )
        serializer = self.serializer_class(instance)

        return Response(data=serializer.data, status=HTTPStatus.OK)
