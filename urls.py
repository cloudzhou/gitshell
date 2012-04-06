from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('gitshell',
    # gitshell web app, nginx port 8000, proxy by haproxy, public
    url(r'^/?$', 'index.views.default'),

    # main
    url(r'^home/?$', 'index.views.home'),
    url(r'^repos/?$', 'index.views.home'),
    url(r'^skills/?$', 'index.views.home'),
    url(r'^stats/?$', 'index.views.home'),
    url(r'^login/?$', 'gsuser.views.login'),
    url(r'^join/?$', 'gsuser.views.join'),

    # help
    url(r'^help/?$', 'help.views.default'),
    url(r'^help/about/?$', 'help.views.about'),
    url(r'^help/faq/?$', 'help.views.faq'),
    url(r'^help/mission/?$', 'help.views.mission'),
    url(r'^help/contact/?$', 'help.views.contact'),
    url(r'^help/quickstart/?$', 'help.views.quickstart'),

    # gitshell openssh keyauth and dist, private for subnetwork access by iptables, nginx port 9000
    url(r'^private/keyauth/fp/(\S+)/?$', 'keyauth.views.fingerprint'),
    url(r'^private/dist/pj/(\S+)/?$', 'dist.views.repos'),
    url(r'^private/dist/refresh/?$', 'dist.views.refresh'),
    url(r'^private/dist/print/?$', 'dist.views.print_repos_partition'),

    # write middleware to rewrite urlconf, by add 'urlconf' attribute to HttpRequest
    # gsuser
    url(r'^([A-Za-z0-9_]+)/?$', 'gsuser.views.user'),
    url(r'^([A-Za-z0-9_]+)/repos/?$', 'gsuser.views.repos'),
    # repos
    url(r'^([A-Za-z0-9_]+)/([A-Za-z0-9_]+)?$', 'repos.views.repos'),
)
