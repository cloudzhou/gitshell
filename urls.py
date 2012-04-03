from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('gitshell',
    # gitshell web app, nginx port 8000
    url(r'^/?$', 'index.views.home'),

    # gitshell keyauth and dist, keep private, nginx port 9000
    url(r'^private/keyauth/fp/(\S+)/?$', 'keyauth.views.fingerprint'),
    url(r'^private/dist/pj/(\S+)/?$', 'dist.views.project'),
    url(r'^private/dist/refresh/?$', 'dist.views.refresh'),
    url(r'^private/dist/print/?$', 'dist.views.print_project_partition'),
)
