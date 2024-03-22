import enum


class PublishTypes(enum.Enum):
    PUBLIC = 'Public'
    PRIVATE = 'Private'
    DATETIME = 'datetime'

class AddType(enum.Enum):
    IMPORTED = 'imported'
    CREATED = 'created'

class Status(enum.Enum):
    PUBLISHED = 'Published'
    UNPUBLISHED = 'Unpublished'

