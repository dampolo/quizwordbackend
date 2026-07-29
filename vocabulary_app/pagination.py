from rest_framework.pagination import PageNumberPagination


class VocabularyWordsPagination(PageNumberPagination):
    page_size = 5