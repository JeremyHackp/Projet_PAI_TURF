"""
cache.py - Gestion des caches pour courses et participants
"""


class CourseCache:
    """Cache pour stocker les courses chargées"""
    def __init__(self):
        self.courses = {}  # {ui_id: course_dict}

    def clear(self):
        self.courses.clear()


class ParticipantsCache:
    """Cache pour stocker les participants chargés"""
    def __init__(self):
        self.participants = {}  # {ui_id: participant_dict}

    def clear(self):
        self.participants.clear()


# Instances globales des caches
course_cache = CourseCache()
participants_cache = ParticipantsCache()
meilleurs_chevaux = ParticipantsCache()
