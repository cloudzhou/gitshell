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
    url(r'^ajax/repo/find/?$', 'repo.views.find'),
    url(r'^ajax/repo/list/github/?$', 'repo.views.list_github_repos'),
    url(r'^ajax/network/watch/(\w+)/', 'gsuser.views.network_watch'),
    url(r'^ajax/network/unwatch/(\w+)/', 'gsuser.views.network_unwatch'),
    url(r'^ajax/home/do_issue/?$', 'issue.views.do_issue'),

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
    url(r'^login/oauth/github/apply/?$', 'gsuser.views.login_github_apply'),
    url(r'^login/oauth/github/relieve/?$', 'gsuser.views.login_github_relieve'),
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
    url(r'^settings/thirdparty/?$', 'gssettings.views.thirdparty'),
    url(r'^settings/change_username_email/?$', 'gssettings.views.change_username_email'),
    url(r'^settings/validate_email/(\w+)/?$', 'gssettings.views.validate_email'),
    url(r'^settings/destroy/?$', 'gssettings.views.destroy'),

    # gitshell openssh keyauth and dist, private for subnetwork access by iptables, nginx port 9000
    url(r'^private/http_auth/?$', 'keyauth.views.http_auth'),
    url(r'^private/keyauth/([a-zA-Z0-9:]+)/?$', 'keyauth.views.pubkey'),
    url(r'^private/keyauth/([a-zA-Z0-9:]+)/([a-zA-Z0-9_ "\-\'\/\.]+)$', 'keyauth.views.keyauth'),
    url(r'^private/dist/repo/(\w+)/([a-zA-Z0-9_\-]+)/?$', 'dist.views.repo'),
    url(r'^private/dist/refresh/?$', 'dist.views.refresh'),
    url(r'^private/dist/echo/?$', 'dist.views.echo'),
    # gitshell keep namespace
    url(r'^gitshell/list_latest_push_repo/(\w+)/?$', 'repo.views.list_latest_push_repo'),

    # third part
    url(r'^captcha/', include('captcha.urls')),

    # write middleware to rewrite urlconf, by add 'urlconf' attribute to HttpRequest
    # gsuser
    url(r'^(\w+)/?$', 'gsuser.views.user'),
    url(r'^(\w+)/active/?$', 'gsuser.views.active'),
    url(r'^(\w+)/star/repo/?$', 'gsuser.views.star_repo'),
    url(r'^(\w+)/watch/repo/?$', 'gsuser.views.watch_repo'),
    url(r'^(\w+)/watch/user/?$', 'gsuser.views.watch_user'),
    url(r'^(\w+)/recommend/?$', 'gsuser.views.recommend'),
    #url(r'^(\w+)/stats/?$', 'gsuser.views.stats'),
    # repo
    url(r'^(\w+)/repo/?$', 'repo.views.user_repo'),
    url(r'^(\w+)/repo/(\d+)/?$', 'repo.views.user_repo_paging'),
    url(r'^(\w+)/repo/create/?$', 'repo.views.create'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/?$', 'repo.views.repo'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/tree/?$', 'repo.views.tree_default'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/tree/([a-zA-Z0-9_\.\-]+)/([^\@\#\$\&\\\*\"\'\<\>\|\;]*)$', 'repo.views.tree'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/blob/([a-zA-Z0-9_\.\-]+)/([^\@\#\$\&\\\*\"\'\<\>\|\;]*)$', 'repo.views.blob'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/raw/blob/([a-zA-Z0-9_\.\-]+)/([^\@\#\$\&\\\*\"\'\<\>\|\;]*)$', 'repo.views.raw_blob'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/commits/?$', 'repo.views.commits_default'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/commits/([a-zA-Z0-9_\.\-]+)\.\.\.([a-zA-Z0-9_\.\-]+)/?$', 'repo.views.commits_log'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/commits/([a-zA-Z0-9_\.\-]+)/([^\@\#\$\&\\\*\"\'\<\>\|\;]*)$', 'repo.views.commits'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/branches/?$', 'repo.views.branches_default'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/branches/([a-zA-Z0-9_\.\-]+)/?$', 'repo.views.branches'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/tags/?$', 'repo.views.tags_default'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/tags/([a-zA-Z0-9_\.\-]+)/?$', 'repo.views.tags'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/compare/?$', 'repo.views.compare_default'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/compare/([a-zA-Z0-9_\.\-]+)\.\.\.([a-zA-Z0-9_\.\-]+)/?$', 'repo.views.compare_commit'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/compare/([a-zA-Z0-9_\.\-]+)/?$', 'repo.views.compare_master'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/merge/([a-zA-Z0-9_\.\-]+)\.\.\.([a-zA-Z0-9_\.\-]+)/?$', 'repo.views.merge'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/pulls/?$', 'repo.views.pulls'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/pull/new/?$', 'repo.views.pull_new_default'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/pull/new/(\w+):([a-zA-Z0-9_\.\-]+)\.\.\.(\w+):([a-zA-Z0-9_\.\-]+)/?$', 'repo.views.pull_new'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/pull/diff/(\w+):([a-zA-Z0-9_\.\-]+)\.\.(\w+):([a-zA-Z0-9_\.\-]+)/(\d+)/?$', 'repo.views.pull_diff'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/pull/commits/(\w+):([a-zA-Z0-9_\.\-]+)\.\.\.(\w+):([a-zA-Z0-9_\.\-]+)/?$', 'repo.views.pull_commits'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/pull/(\d+)/?$', 'repo.views.pull_show'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/pull/(\d+)/merge/?$', 'repo.views.pull_merge'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/pull/(\d+)/reject/?$', 'repo.views.pull_reject'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/pull/(\d+)/close/?$', 'repo.views.pull_close'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/edit/?$', 'repo.views.edit'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/delete/?$', 'repo.views.delete'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/network/?$', 'repo.views.network'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/clone_watch_star/?$', 'repo.views.clone_watch_star'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/stats/?$', 'repo.views.stats'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/settings/?$', 'repo.views.settings'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/log/graph/([a-zA-Z0-9_\.\-]+)/?$', 'repo.views.log_graph'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/refs/graph/([a-zA-Z0-9_\.\-]+)/?$', 'repo.views.refs_graph'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/refs/?$', 'repo.views.refs'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/fork/?$', 'repo.views.fork'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/watch/?$', 'repo.views.watch'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/unwatch/?$', 'repo.views.unwatch'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/star/?$', 'repo.views.star'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/unstar/?$', 'repo.views.unstar'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/generate_deploy_url/?$', 'repo.views.generate_deploy_url'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/forbid_dploy_url/?$', 'repo.views.forbid_dploy_url'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/enable_dropbox_sync/?$', 'repo.views.enable_dropbox_sync'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/disable_dropbox_sync/?$', 'repo.views.disable_dropbox_sync'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/diff/([a-zA-Z0-9_\.\-]+)\.\.([a-zA-Z0-9_\.\-]+)/(\d+)/([^\@\#\$\&\\\*\"\'\<\>\|\;]*)$', 'repo.views.diff'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/diff/([a-zA-Z0-9_\.\-]+)\.\.([a-zA-Z0-9_\.\-]+)/(\d+)/?', 'repo.views.diff_default'),
    
    # issue
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/issues/?$', 'issue.views.issues'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/issues/(\d+)/?$', 'issue.views.show_default'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/issues/(\d+)/(\d+)/?$', 'issue.views.show'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/issues/create/?$', 'issue.views.create'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/issues/edit/(\d+)/?$', 'issue.views.edit'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/issues/delete/(\d+)/?$', 'issue.views.delete'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/issues/update/(\d+)/(\w+)/?$', 'issue.views.update'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/issues/list/(\w+)/(\d+)/(\d+)/(\d+)/(\w+)/(\d+)/?$', 'issue.views.issues_list'),
    url(r'^(\w+)/([a-zA-Z0-9_\-]+)/issues/comment/delete/(\d+)/?$', 'issue.views.comment_delete'),
    
)
handler404 = 'gitshell.help.views.error'
handler500 = 'gitshell.help.views.error'

