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
    url(r'^join/(\d)/?$', 'gsuser.views.join'),
    url(r'^resetpassword/(\d)/?$', 'gsuser.views.resetpassword'),

    # help
    url(r'^help/?$', 'help.views.default'),
    url(r'^help/quickstart/?$', 'help.views.quickstart'),

    # gitshell openssh keyauth and dist, private for subnetwork access by iptables, nginx port 9000
    url(r'^private/keyauth/fp/(\S+)/?$', 'keyauth.views.fingerprint'),
    url(r'^private/dist/pj/(\S+)/?$', 'dist.views.repos'),
    url(r'^private/dist/refresh/?$', 'dist.views.refresh'),
    url(r'^private/dist/echo/?$', 'dist.views.echo_repos_partition'),

    # third part
    url(r'^captcha/', include('captcha.urls')),

    # write middleware to rewrite urlconf, by add 'urlconf' attribute to HttpRequest
    # gsuser
    url(r'^([A-Za-z0-9_]+)/?$', 'gsuser.views.user'),
    url(r'^([A-Za-z0-9_]+)/repos/?$', 'gsuser.views.repos'),
    # repos
    url(r'^([A-Za-z0-9_]+)/([A-Za-z0-9_]+)?$', 'repos.views.repos'),
)
