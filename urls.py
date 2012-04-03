from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('gitshell',
    url(r'^/?$', 'auth.views.home'),
    url(r'^auth/fp/(\S+)/?$', 'auth.views.fingerprint'),
    url(r'^dist/pj/(\S+)/?$', 'dist.views.project'),
    url(r'^dist/refresh/?$', 'dist.views.refresh'),
    url(r'^dist/print/?$', 'dist.views.print_project_partition'),
)
