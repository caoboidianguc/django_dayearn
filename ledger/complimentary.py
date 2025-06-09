from django.shortcuts import render, redirect, get_object_or_404
from .models import Complimentary
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from .forms import ComplimentaryForm

class ComplimentaryListView(LoginRequiredMixin, ListView):
    model = Complimentary
    template_name = 'complimentary/complimentary_list.html'
    context_object_name = 'complimentary_list'

    def get_queryset(self):
        return Complimentary.objects.filter(owner=self.request.user)
    
class ComplimentaryCreateView(LoginRequiredMixin, CreateView):
    model = Complimentary
    # add this to template post-> enctype="multipart/form-data"
    template_name = 'complimentary/complimentary_form.html'
    form_class = ComplimentaryForm
    success_url = reverse_lazy('ledger:complimentary_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

   
def complimentary_is_available(request, pk):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    complimentary = get_object_or_404(Complimentary, pk=pk, owner=request.user)
    if request.method == 'POST':
        complimentary.is_available = not complimentary.is_available
        complimentary.save()
        return JsonResponse({'success': True, 'is_available': complimentary.is_available}, status=200)
    return JsonResponse({'error': 'Invalid request'}, status=400)

