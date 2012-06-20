from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('gitshell',
    # gitshell web app, nginx port 8000, proxy by haproxy, public
    url(r'^/?$', 'index.views.index'),

    # main
    url(r'^repos/?$', 'index.views.home'),
    url(r'^warehouse/?$', 'index.views.warehouse'),
    url(r'^folder/?$', 'index.views.folder'),
    url(r'^file/?$', 'index.views.file'),

    # skills
    # url(r'^skills/?$', 'skills.views.skills'),

    # stats
    url(r'^stats/?$', 'stats.views.stats'),

    # ajax
    url(r'^ajax/feed/ids/?$', 'feed.views.feedbyids'),
    url(r'^ajax/repo/(\w+)/(\w+)/refs/?$', 'repos.views.repo_refs'),

    # gsuser
    url(r'^home/?$', 'feed.views.home'),
    url(r'^home/feed/?$', 'feed.views.feed'),
    url(r'^home/git/?$', 'feed.views.git'),
    url(r'^home/issues/?$', 'feed.views.issues'),
    url(r'^home/explore/?$', 'feed.views.explore'),
    url(r'^home/notif/?$', 'feed.views.notif'),
    url(r'^login/?$', 'gsuser.views.login'),
    url(r'^logout/?$', 'gsuser.views.logout'),
    url(r'^join/?(\w+)?/?$', 'gsuser.views.join'),
    url(r'^resetpassword/?(\w+)?/?$', 'gsuser.views.resetpassword'),

    # help
    url(r'^help/?$', 'help.views.default'),
    url(r'^help/quickstart/?$', 'help.views.quickstart'),

    # settings
    url(r'^settings/?$', 'gssettings.views.profile'),
    url(r'^settings/profile/?$', 'gssettings.views.profile'),
    url(r'^settings/changepassword/?$', 'gssettings.views.changepassword'),
    url(r'^settings/sshpubkey/?$', 'gssettings.views.sshpubkey'),
    url(r'^settings/sshpubkey/remove/?$', 'gssettings.views.sshpubkey_remove'),
    url(r'^settings/email/?$', 'gssettings.views.email'),
    url(r'^settings/repos/?$', 'gssettings.views.repos'),
    url(r'^settings/destroy/?$', 'gssettings.views.destroy'),

    # gitshell openssh keyauth and dist, private for subnetwork access by iptables, nginx port 9000
    url(r'^private/keyauth/([A-Za-z0-9:]+)/?$', 'keyauth.views.pubkey'),
    url(r'^private/keyauth/([A-Za-z0-9:]+)/([A-Za-z0-9_ \-\'"\/]+)$', 'keyauth.views.keyauth'),
    url(r'^private/dist/repos/(\w+)/(\w+)/?$', 'dist.views.repos'),
    url(r'^private/dist/refresh/?$', 'dist.views.refresh'),
    url(r'^private/dist/echo/?$', 'dist.views.echo'),

    # third part
    url(r'^captcha/', include('captcha.urls')),

    # write middleware to rewrite urlconf, by add 'urlconf' attribute to HttpRequest
    # gsuser
    url(r'^(\w+)/?$', 'gsuser.views.user'),
    # repos
    url(r'^(\w+)/repos/?$', 'repos.views.user_repos'),
    url(r'^(\w+)/repos/(\d+)/?$', 'repos.views.user_repos_paging'),
    url(r'^\w+/repos/edit/(\d+)/?$', 'repos.views.edit'),
    url(r'^(\w+)/(\w+)/?$', 'repos.views.repos'),
    url(r'^(\w+)/(\w+)/tree/([a-zA-Z0-9_\.\-]+)/([a-zA-Z0-9_\.\-/]*)$', 'repos.views.repos_tree'),
    url(r'^(\w+)/(\w+)/network/?$', 'repos.views.repos_network'),
    url(r'^(\w+)/(\w+)/issues/?$', 'repos.views.repos_issues'),
    url(r'^(\w+)/(\w+)/stats/?$', 'repos.views.repos_stats'),
    url(r'^(\w+)/(\w+)/commits/?$', 'repos.views.repos_commits'),
    url(r'^(\w+)/(\w+)/branches/?$', 'repos.views.repos_branches'),
)
