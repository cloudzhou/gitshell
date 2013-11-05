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

create index issue_cons_mtime_idx on issue_issue (visibly, repo_id, assigned, tracker, status, priority, modify_time desc);
create index issue_rid_mtime_idx on issue_issue (visibly, repo_id, modify_time desc);
create index issue_assigned_status_mtime_idx on issue_issue (visibly, assigned, status, modify_time desc);
create index issuecomment_iid_ctime_idx on issue_issuecomment (visibly, issue_id, create_time asc);

create index forkhistory_rid_mtime_idx on repo_forkhistory (visibly, repo_id, modify_time desc);
create index watchhistory_rid_mtime_idx on repo_watchhistory (visibly, watch_repo_id, modify_time desc);
create index scene_uid_idx on todolist_scene (visibly, user_id)
create index todolist_uid_idx on todolist_todolist (visibly, user_id)

alter table gsuser_userprofile add `username` varchar(30) NOT NULL after `visibly`;
alter table gsuser_userprofile add `email` varchar(30) NOT NULL after `username`;
alter table repo_repo add `username` varchar(30) NOT NULL after `fork_repo_id`;
update gsuser_userprofile as t1 inner join auth_user as t2 on t1.id = t2.id set t1.username = t2.username, t1.email = t2.email;
update repo_repo as t1 inner join auth_user as t2 on t1.user_id = t2.id set t1.username = t2.username;

alter table repo_repo add `star` INT NOT NULL DEFAULT 0 after `watch`;
alter table repo_repo add `deploy_url` varchar(40) NULL after `member`;
alter table repo_repo add `dropbox_sync` INT NOT NULL DEFAULT 0 after `deploy_url`;
alter table repo_repo add `dropbox_url` varchar(64) NULL after `dropbox_sync`;
alter table repo_repo add `last_push_time` datetime NOT NULL after `dropbox_url`;

update repo_repo set star = 0;
update repo_repo set deploy_url = '';
update repo_repo set dropbox_sync = 0;
update repo_repo set dropbox_url = '';
update repo_repo set last_push_time = now();

create index repo_last_push_time_idx on repo_repo (last_push_time DESC);

insert into gsuser_useremail select 0, now(), now(), 0, id, email, 1, 1, 1 from auth_user;
create index gsuser_useremail_uid_idx on gsuser_useremail (visibly, user_id)
create index feed_notifsetting_uid_idx on feed_notifsetting (visibly, user_id)

alter table issue_issue add COLUMN  `creator_user_id` int(11) NOT NULL after user_id;
update issue_issue set creator_user_id = user_id;
alter table issue_issue drop `user_id`;
alter table issue_issue add COLUMN `user_id` int(11) NOT NULL after `visibly`;
update issue_issue set user_id = (select user_id from repo_repo where repo_id=issue_issue.repo_id limit 1);

alter table feed_notifmessage add COLUMN `repo_id` int(11) NOT NULL after `visibly`
alter table feed_notifmessage add COLUMN `user_id` int(11) NOT NULL after `visibly`;

alter table gsuser_userprofile add COLUMN `has_joined_repo` int(11) NOT NULL after `unread_message`;
alter table gsuser_userprofile change `is_join_team` `has_joined_team` int(11) NOT NULL;
update gsuser_userprofile set has_joined_repo = 1 where id in  (select user_id from repo_repomember where visibly = 0);
update gsuser_userprofile set has_joined_team = 1 where id in  (select user_id from team_teammember where visibly = 0);
