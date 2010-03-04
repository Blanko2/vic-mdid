
PAGEHELP = 'HELP'

class PageHelp:
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        print "Help processing"
        if PAGEHELP in view_kwargs:
            print "found"
            request.pagehelp = view_kwargs[PAGEHELP]
            del view_kwargs[PAGEHELP]
