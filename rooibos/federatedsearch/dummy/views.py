from django.shortcuts import render_to_response

def search(request):
	query = request.GET.get('q', '') or request.POST.get('q', '')
	return render_to_response('dummy-results.html')
