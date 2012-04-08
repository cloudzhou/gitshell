from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('gitshell',
    # gitshell web app, nginx port 8000, proxy by haproxy, public
    url(r'^/?$', 'index.views.default'),

    # main
    url(r'^home/?$', 'index.views.home'),
    url(r'^repos/?$', 'index.views.home'),
    url(r'^skills/?$', 'index.views.home'),
    url(r'^stats/?$', 'index.views.home'),

    # gsuser
    url(r'^login/?$', 'gsuser.views.login'),
    url(r'^logout/?$', 'gsuser.views.logout'),
    url(r'^join/?(\w+)?/?$', 'gsuser.views.join'),
    url(r'^resetpassword/?(\w+)?/?$', 'gsuser.views.resetpassword'),

    # help
    url(r'^help/?$', 'help.views.default'),
    url(r'^help/quickstart/?$', 'help.views.quickstart'),

    # settings
    url(r'^settings/?$', 'gssettings.views.default'),
    #url(r'^settings/profile/?$', 'gssettings.views.profile'),

    # gitshell openssh keyauth and dist, private for subnetwork access by iptables, nginx port 9000
    url(r'^private/keyauth/fp/(\w+)/?$', 'keyauth.views.fingerprint'),
    url(r'^private/dist/pj/(\w+)/?$', 'dist.views.repos'),
    url(r'^private/dist/refresh/?$', 'dist.views.refresh'),
    url(r'^private/dist/echo/?$', 'dist.views.echo_repos_partition'),

    # third part
    url(r'^captcha/', include('captcha.urls')),

    # write middleware to rewrite urlconf, by add 'urlconf' attribute to HttpRequest
    # gsuser
    url(r'^(\w+)/?$', 'gsuser.views.user'),
    url(r'^(\w+)/repos/?$', 'gsuser.views.repos'),
    # repos
    url(r'^(\w+)/(\w+)?$', 'repos.views.repos'),
)
