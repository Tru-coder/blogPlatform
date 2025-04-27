import enum


@enum.unique
class Permission(enum.Enum):


    TAG_READ = "tag:read"
    TAG_CREATE = "tag:create"
    TAG_UPDATE = "tag:update"
    TAG_DELETE = "tag:delete"

    POST_READ = "post:read"
    POST_CREATE = "post:create"
    POST_UPDATE = "post:update"
    POST_DELETE = "post:delete"

    USER_READ = "user:read"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"

    COMMENT_READ = "comment:read"
    COMMENT_CREATE = "comment:create"
    COMMENT_UPDATE = "comment:update"
    COMMENT_DELETE = "comment:delete"
    COMMENT_MODERATE = "comment:moderate"
    COMMENT_TO_MODERATE = "comment:to_moderate"
    COMMENT_REACT = "comment:react"
    COMMENT_REACT_DELETE = "comment_react:delete"

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))

    @classmethod
    def all_permissions(cls):
        return set(map(lambda c: c, cls))

    @classmethod
    def admin_permissions(cls):
        return set(map(lambda c: c, cls))

    @classmethod
    def user_permissions(cls):
        return {
            Permission.TAG_READ,
            Permission.POST_READ,
            Permission.COMMENT_READ,
            Permission.COMMENT_CREATE,
            Permission.COMMENT_UPDATE,
            Permission.COMMENT_DELETE,
            Permission.COMMENT_REACT,
            Permission.COMMENT_REACT_DELETE,
        }

    @classmethod
    def author_permissions(cls):
        return {
            Permission.POST_READ,
            Permission.POST_CREATE,
            Permission.POST_UPDATE,
            Permission.POST_DELETE,
        } | Permission.user_permissions()

