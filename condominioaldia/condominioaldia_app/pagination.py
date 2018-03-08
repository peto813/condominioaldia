from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import status
from condominioaldia_app.serializers import BlogSerializer
from django.utils import timezone

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    #page_size_query_param = 'page_size'
    #max_page_size = 1000

class BlogPagination(PageNumberPagination):
	page_size = 10
	def get_paginated_response(self, context):
		response = {}
		pagination_dict = {
			'next_link':self.get_next_link(),
			'previous_link' :self.get_previous_link(),
			'count': self.page.paginator.count,
			'page_count':self.page.paginator.num_pages,
			'current_page' :self.page.number,
			'page_size' :self.page_size
		}
		serializer = BlogSerializer(context.pop('blog'), many= True)

		for key, value in pagination_dict.iteritems():
			response[key] =value
		for key, value in context.iteritems():
			response[key] =value
		response['results'] = serializer.data
		return Response(response, status =status.HTTP_200_OK)
