from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('gitshell',
    # gitshell web app, nginx port 8000, proxy by haproxy, public
    url(r'^/?$', 'index.views.index'),
    # skills
    # url(r'^skills/?$', 'skills.views.skills'),

    # stats
    url(r'^stats/(\w+)/?$', 'stats.views.stats'),
    # explore
    url(r'^explore/?$', 'explore.views.explore'),

    # ajax
    url(r'^ajax/user/find/?$', 'gsuser.views.find'),
    url(r'^ajax/user/change/?$', 'gsuser.views.change'),
    url(r'^ajax/user/(\w+)/recommend/delete/(\d+)/?$', 'gsuser.views.recommend_delete'),
    url(r'^ajax/feed/ids/?$', 'feed.views.feed_by_ids'),
    url(r'^ajax/repo/list/github/?$', 'repo.views.list_github_repos'),
    url(r'^ajax/repo/(\w+)/(\w+)/refs/?$', 'repo.views.repo_refs'),
    url(r'^ajax/repo/(\w+)/(\w+)/refs/?$', 'repo.views.repo_refs'),
    url(r'^ajax/repo/(\w+)/(\w+)/fork/?$', 'repo.views.repo_fork'),
    url(r'^ajax/repo/(\w+)/(\w+)/watch/?$', 'repo.views.repo_watch'),
    url(r'^ajax/repo/(\d+)/unwatch/?$', 'repo.views.repo_unwatch_by_id'),
    url(r'^ajax/repo/(\w+)/(\w+)/unwatch/?$', 'repo.views.repo_unwatch'),
    url(r'^ajax/repo/(\w+)/(\w+)/diff/(\w+)/(\w+)/([a-zA-Z0-9_\.\-/]*)$', 'repo.views.repo_diff'),
    url(r'^ajax/network/watch/(\w+)/', 'gsuser.views.network_watch'),
    url(r'^ajax/network/unwatch/(\w+)/', 'gsuser.views.network_unwatch'),
    url(r'^ajax/home/doissues/?$', 'feed.views.doissues'),

    # gsuser
    url(r'^home/?$', 'feed.views.home'),
    url(r'^home/feed/?$', 'feed.views.feed'),
    url(r'^home/timeline/?$', 'feed.views.timeline'),

    # todolist
    url(r'^home/todo/?$', 'todolist.views.todo'),
    url(r'^home/todo/(\d+)/?$', 'todolist.views.todo_scene'),
    url(r'^home/todo/(\d+)/add/?$', 'todolist.views.add_scene'),
    url(r'^home/todo/(\d+)/remove/?$', 'todolist.views.remove_scene'),
    url(r'^home/todo/(\d+)/add_todo/?$', 'todolist.views.add_todo'),
    url(r'^home/todo/(\d+)/remove_todo/?$', 'todolist.views.remove_todo'),
    url(r'^home/todo/(\d+)/doing_todo/?$', 'todolist.views.doing_todo'),
    url(r'^home/todo/(\d+)/done_todo/?$', 'todolist.views.done_todo'),
    url(r'^home/todo/(\d+)/update_scene_meta/?$', 'todolist.views.update_scene_meta'),

    url(r'^home/issues/?$', 'feed.views.issues_default'),
    url(r'^home/issues/(\d+)/?$', 'feed.views.issues'),

    url(r'^home/pull/?$', 'feed.views.pull_merge'),
    url(r'^home/pull/merge/?$', 'feed.views.pull_merge'),
    url(r'^home/pull/request/?$', 'feed.views.pull_request'),

    url(r'^home/explore/?$', 'feed.views.explore'),
    url(r'^home/notif/?$', 'feed.views.notif'),
    url(r'^login/?$', 'gsuser.views.login'),
    url(r'^login/oauth/github/?$', 'gsuser.views.login_github'),
    url(r'^logout/?$', 'gsuser.views.logout'),
    url(r'^join/?(\w+)?/?$', 'gsuser.views.join'),
    url(r'^resetpassword/?(\w+)?/?$', 'gsuser.views.resetpassword'),

    # help
    url(r'^help/?$', 'help.views.default'),
    url(r'^help/quickstart/?$', 'help.views.quickstart'),
    url(r'^help/error/?$', 'help.views.error'),
    url(r'^help/access_out_of_limit/?$', 'help.views.access_out_of_limit'),
    url(r'^help/reset_access_limit/?$', 'help.views.reset_access_limit'),

    # settings
    url(r'^settings/?$', 'gssettings.views.profile'),
    url(r'^settings/profile/?$', 'gssettings.views.profile'),
    url(r'^settings/sshpubkey/?$', 'gssettings.views.sshpubkey'),
    url(r'^settings/sshpubkey/remove/?$', 'gssettings.views.sshpubkey_remove'),
    url(r'^settings/notif/?$', 'gssettings.views.notif'),
    url(r'^settings/changepassword/?$', 'gssettings.views.changepassword'),
    url(r'^settings/change_username_email/?$', 'gssettings.views.change_username_email'),
    url(r'^settings/validate_email/(\w+)/?$', 'gssettings.views.validate_email'),
    url(r'^settings/destroy/?$', 'gssettings.views.destroy'),

    # gitshell openssh keyauth and dist, private for subnetwork access by iptables, nginx port 9000
    url(r'^private/http_auth/?$', 'keyauth.views.http_auth'),
    url(r'^private/keyauth/([A-Za-z0-9:]+)/?$', 'keyauth.views.pubkey'),
    url(r'^private/keyauth/([A-Za-z0-9:]+)/([A-Za-z0-9_ "\-\'\/\.]+)$', 'keyauth.views.keyauth'),
    url(r'^private/dist/repo/(\w+)/(\w+)/?$', 'dist.views.repo'),
    url(r'^private/dist/refresh/?$', 'dist.views.refresh'),
    url(r'^private/dist/echo/?$', 'dist.views.echo'),

    # third part
    url(r'^captcha/', include('captcha.urls')),

    # write middleware to rewrite urlconf, by add 'urlconf' attribute to HttpRequest
    # gsuser
    url(r'^(\w+)/?$', 'gsuser.views.user'),
    url(r'^(\w+)/active/?$', 'gsuser.views.active'),
    url(r'^(\w+)/watch/repo/?$', 'gsuser.views.watch_repo'),
    url(r'^(\w+)/watch/user/?$', 'gsuser.views.watch_user'),
    url(r'^(\w+)/recommend/?$', 'gsuser.views.recommend'),
    #url(r'^(\w+)/stats/?$', 'gsuser.views.stats'),
    # repo
    url(r'^(\w+)/repo/?$', 'repo.views.user_repo'),
    url(r'^(\w+)/repo/(\d+)/?$', 'repo.views.user_repo_paging'),
    url(r'^(\w+)/repo/edit/(\d+)/?$', 'repo.views.edit'),
    url(r'^(\w+)/(\w+)/?$', 'repo.views.repo'),
    url(r'^(\w+)/(\w+)/tree/?$', 'repo.views.repo_default_tree'),
    url(r'^(\w+)/(\w+)/tree/([a-zA-Z0-9_\.\-]+)/([a-zA-Z0-9_\.\-/]*)$', 'repo.views.repo_tree'),
    url(r'^(\w+)/(\w+)/raw/tree/([a-zA-Z0-9_\.\-]+)/([a-zA-Z0-9_\.\-/]*)$', 'repo.views.repo_raw_tree'),
    url(r'^(\w+)/(\w+)/commits/?$', 'repo.views.repo_default_commits'),
    url(r'^(\w+)/(\w+)/commits/([a-zA-Z0-9_\.\-]+)/([a-zA-Z0-9_\.\-/]*)$', 'repo.views.repo_commits'),
    url(r'^(\w+)/(\w+)/pulls/?$', 'repo.views.repo_pulls'),
    url(r'^(\w+)/(\w+)/pull/new/?$', 'repo.views.repo_default_pull_new'),
    url(r'^(\w+)/(\w+)/pull/new/(\w+):([a-zA-Z0-9_\.\-]+)\.\.\.(\w+):([a-zA-Z0-9_\.\-/]+)$', 'repo.views.repo_pull_new'),
    url(r'^(\w+)/(\w+)/pull/(\d+)/?$', 'repo.views.repo_pull_show'),
    url(r'^(\w+)/(\w+)/pull/(\d+)/diff/?$', 'repo.views.repo_pull_diff'),
    url(r'^(\w+)/(\w+)/pull/(\d+)/commit/?$', 'repo.views.repo_pull_commit'),
    url(r'^(\w+)/(\w+)/pull/(\d+)/merge/?$', 'repo.views.repo_pull_merge'),
    url(r'^(\w+)/(\w+)/pull/(\d+)/reject/?$', 'repo.views.repo_pull_reject'),
    url(r'^(\w+)/(\w+)/pull/(\d+)/close/?$', 'repo.views.repo_pull_close'),
    url(r'^(\w+)/(\w+)/delete/?$', 'repo.views.delete'),
    url(r'^(\w+)/(\w+)/issues/?$', 'repo.views.issues'),
    url(r'^(\w+)/(\w+)/issues/(\d+)/?$', 'repo.views.issues_default_show'),
    url(r'^(\w+)/(\w+)/issues/(\d+)/(\d+)/?$', 'repo.views.issues_show'),
    url(r'^(\w+)/(\w+)/issues/create/(\d+)/?$', 'repo.views.issues_create'),
    url(r'^ajax/repo/(\w+)/(\w+)/issues/delete/(\w+)/?$', 'repo.views.issues_delete'),
    url(r'^ajax/repo/(\w+)/(\w+)/issues/update/(\w+)/(\w+)/?$', 'repo.views.issues_update'),
    url(r'^(\w+)/(\w+)/issues/list/(\w+)/(\d+)/(\d+)/(\d+)/(\w+)/(\d+)/?$', 'repo.views.issues_list'),
    url(r'^ajax/repo/(\w+)/(\w+)/issues/comment/delete/(\w+)/?$', 'repo.views.issues_comment_delete'),
    url(r'^(\w+)/(\w+)/network/?$', 'repo.views.repo_network'),
    url(r'^(\w+)/(\w+)/clone_watch/?$', 'repo.views.repo_clone_watch'),
    url(r'^(\w+)/(\w+)/stats/?$', 'repo.views.repo_stats'),
    
)
handler404 = 'gitshell.help.views.error'
handler500 = 'gitshell.help.views.error'
