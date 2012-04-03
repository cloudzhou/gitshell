from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('gitshell',
    url(r'^/?$', 'auth.views.home'),
    url(r'^private/auth/fp/(\S+)/?$', 'auth.views.fingerprint'),
    url(r'^private/dist/pj/(\S+)/?$', 'dist.views.project'),
    url(r'^private/dist/refresh/?$', 'dist.views.refresh'),
    url(r'^private/dist/print/?$', 'dist.views.print_project_partition'),
)
