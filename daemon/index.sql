create index userpubkey_uid_idx on keyauth_userpubkey (visibly, user_id);
create index userpubkey_fgp_idx on keyauth_userpubkey (visibly, fingerprint(8));

create index statsrepo_hid_idx on stats_statsrepo (repo_id, hash_id);
create index statsrepo_rid_types_date_idx on stats_statsrepo (repo_id, statstype, datetype, date);

create index statsuser_hid_idx on stats_statsuser (user_id, hash_id);
create index statsuser_uid_types_date_idx on stats_statsuser (user_id, statstype, datetype, date);

create index recommend_uid_idx on gsuser_recommend (visibly, user_id);
create unique index auth_user_email_idx on auth_user (email);

create index repo_uid_name_idx on repo_repo (visibly, user_id, name);
create index repo_forkid on repo_repo (visibly, fork_repo_id)

create index commithistory_rid_cid_idx on repo_commithistory (visibly, repo_id, commit_id);
create index repomember_rid_uid on repo_repomember (visibly, repo_id, user_id);
create index issues_cons_mtime_idx on repo_issues (visibly, repo_id, assigned, tracker, status, priority, modify_time desc);
create index issues_rid_mtime_idx on repo_issues (visibly, repo_id, modify_time desc);
create index issues_assigned_status_mtime_idx on repo_issues (visibly, assigned, status, modify_time desc);

create index issuescomment_iid_ctime_idx on repo_issuescomment (visibly, issues_id, create_time asc);
create index forkhistory_rid_mtime_idx on repo_forkhistory (visibly, repo_id, modify_time desc);
create index watchhistory_rid_mtime_idx on repo_watchhistory (visibly, watch_repo_id, modify_time desc);
create index scene_uid_idx on todolist_scene (visibly, user_id)
create index todolist_uid_idx on todolist_todolist (visibly, user_id)
