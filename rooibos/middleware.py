from django.conf import settings

class Middleware:
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        return None
    
    def process_request(self, request):
        return
    
    def process_response(self, request, response):
        # Remove the Vary header for content loaded into Flash, otherwise caching is broken
        if request.GET.get('flash') == '1':
            try:
                del response['Vary']
            except KeyError:
                pass
        return response