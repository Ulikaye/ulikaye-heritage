from django.contrib import admin
from .models import FamilyMember
from .models import ClanStory
from .models import InviteCode

admin.site.register(InviteCode)
admin.site.register(FamilyMember)
admin.site.register(ClanStory)