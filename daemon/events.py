
class CommitEvent:
    def __init__(self, username, reposname, refname, oldrev, newrev):
        self.username = username
        self.reposname = reposname
        self.refname = refname
        self.oldrev = oldrev
        self.newrev = newrev

class CommonEvent:
    def __init__(self, ctype, mid, sid, attach):
        self.ctype = ctype
        self.mid = mid
        self.sid = sid
        self.attach = attach
