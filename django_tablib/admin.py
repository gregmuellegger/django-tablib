import datetime
from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.core.urlresolvers import reverse
from django.http import Http404
from django.utils.functional import update_wrapper
from django_tablib.views import export

class TablibAdmin(admin.ModelAdmin):
    change_list_template = 'tablib/change_list.html'
    formats = []
    export_filename = 'export'
    
    def get_urls(self):
        from django.conf.urls.defaults import patterns, url

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.module_name
        
        urlpatterns = patterns('',
            url(r'^tablib-export/(?P<format>\w+)/$',
                wrap(self.tablib_export),
                name='%s_%s_tablib_export' % info),
        )
        urlpatterns += super(TablibAdmin, self).get_urls()
        return urlpatterns
    
    def tablib_export(self, request, format):
        if format not in self.formats:
            raise Http404
        queryset = self.get_tablib_queryset(request)
        filename = datetime.datetime.now().strftime(self.export_filename)
        return export(request, queryset=queryset, model=self.model, format=format, filename=filename)
    
    def get_tablib_queryset(self, request):
        cl = ChangeList(request,
            self.model,
            self.list_display,
            self.list_display_links,
            self.list_filter,
            self.date_hierarchy,
            self.search_fields,
            self.list_select_related,
            self.list_per_page,
            self.list_editable,
            self,
        )
        return cl.get_query_set()
        
    def changelist_view(self, request, extra_context=None):
        info = self.model._meta.app_label, self.model._meta.module_name
        extra_context = {'request': request}
        urls = []
        for format in self.formats:
            urls.append((format, reverse('admin:%s_%s_tablib_export' % info, kwargs={'format': format}),))
        extra_context['urls'] = urls
        return super(TablibAdmin, self).changelist_view(request, extra_context)