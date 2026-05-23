from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import random
import string

from .models import (
    FamilyMember, ClanStory, ElderVoice, TimelineEvent,
    MigrationStory, Tradition, MediaItem, InviteCode, AuditLog
)

# Helper
def is_admin(user):
    return user.is_superuser or user.is_staff

# Home
def home(request):
    return render(request, 'heritage/home.html')

# Authentication views
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'heritage/login.html', {'form': form})

# Registration
def register(request):
    if request.method == 'POST':
        invite_code = request.POST.get('invite_code')
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')

        error = None
        if not all([invite_code, full_name, email, password]):
            error = "All fields are required."
        elif password != password_confirm:
            error = "Passwords do not match."
        elif User.objects.filter(username=email).exists():
            error = "A user with this email already exists."
        else:
            try:
                inv = InviteCode.objects.get(code=invite_code)
            except InviteCode.DoesNotExist:
                error = "Invalid invitation code."
            else:
                if not inv.is_valid():
                    error = "Invitation code is invalid or already used."
        
        if error:
            return render(request, 'heritage/register.html', {'error': error})

        user = User.objects.create_user(username=email, email=email, password=password)
        user.first_name = full_name
        user.save()

        inv.used = True
        inv.used_by = user
        inv.save()

        FamilyMember.objects.create(
            full_name=full_name,
            created_by=user,
            user=user
        )

        login(request, user)
        return redirect('home')

    return render(request, 'heritage/register.html')

# Admin panel (with invites and logs)
@login_required
@user_passes_test(is_admin)
def admin_panel(request):
    members = FamilyMember.objects.all().order_by('full_name')
    invites = InviteCode.objects.all().order_by('-created_at')
    # If you don't have AuditLog model yet, comment the next line and use empty list
    logs = AuditLog.objects.all().order_by('-timestamp')[:50] if hasattr(AuditLog, 'objects') else []
    return render(request, 'heritage/admin.html', {
        'members': members,
        'invites': invites,
        'logs': logs,
        'is_admin': True,
    })

# Member CRUD
@login_required
@user_passes_test(is_admin)
def add_member(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        birth_date = request.POST.get('birth_date') or None
        death_date = request.POST.get('death_date') or None
        bio = request.POST.get('bio', '')
        photo_url = request.POST.get('photo_url', '')
        parent_id = request.POST.get('parent_id') or None
        if full_name:
            FamilyMember.objects.create(
                full_name=full_name,
                birth_date=birth_date,
                death_date=death_date,
                bio=bio,
                photo_url=photo_url,
                created_by=request.user,
                parent_id=parent_id
            )
            messages.success(request, f"Member {full_name} added.")
        else:
            messages.error(request, "Name is required.")
    return redirect('admin_panel')

@login_required
@user_passes_test(is_admin)
def delete_member(request, member_id):
    member = get_object_or_404(FamilyMember, id=member_id)
    member.delete()
    messages.success(request, "Member deleted.")
    return redirect('admin_panel')

@login_required
@user_passes_test(is_admin)
def edit_member(request, member_id):
    member = get_object_or_404(FamilyMember, id=member_id)
    if request.method == 'POST':
        member.full_name = request.POST.get('full_name')
        member.birth_date = request.POST.get('birth_date') or None
        member.death_date = request.POST.get('death_date') or None
        member.bio = request.POST.get('bio')
        member.photo_url = request.POST.get('photo_url')
        member.parent_id = request.POST.get('parent_id') or None
        member.save()
        messages.success(request, "Member updated.")
        return redirect('admin_panel')
    return render(request, 'heritage/edit_member.html', {'member': member})

# Invite code generation
@login_required
@user_passes_test(is_admin)
def generate_invite(request):
    if request.method == 'POST':
        custom_code = request.POST.get('custom_code', '').strip()
        if custom_code:
            if InviteCode.objects.filter(code=custom_code).exists():
                messages.error(request, "Code already exists.")
                return redirect('admin_panel')
            code = custom_code
        else:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        InviteCode.objects.create(code=code)
        messages.success(request, f"Invite code generated: {code}")
    return redirect('admin_panel')

# Family Tree
def family_tree(request):
    root_id = request.GET.get('root')
    members = FamilyMember.objects.all()
    node_dict = {}
    for m in members:
        node_dict[m.id] = {
            'id': m.id,
            'name': m.full_name,
            'birth_date': m.birth_date,
            'death_date': m.death_date,
            'children': []
        }
    roots = []
    for m in members:
        if m.parent_id:
            if m.parent_id in node_dict:
                node_dict[m.parent_id]['children'].append(node_dict[m.id])
        else:
            roots.append(node_dict[m.id])
    current_root = None
    if root_id and root_id.isdigit():
        root_id = int(root_id)
        if root_id in node_dict:
            current_root = node_dict[root_id]
    if not current_root and roots:
        current_root = roots[0]
    member_choices = [(m.id, m.full_name) for m in members.order_by('full_name')]
    return render(request, 'heritage/family-tree.html', {
        'tree': current_root,
        'member_choices': member_choices,
        'selected_root': root_id or (roots[0]['id'] if roots else None)
    })

# Clan Stories
@login_required
def clan_stories(request):
    stories = ClanStory.objects.all().order_by('clan_name')
    is_admin = request.user.is_superuser or request.user.is_staff
    return render(request, 'heritage/clan-stories.html', {
        'stories': stories,
        'is_admin': is_admin
    })

@login_required
def add_clan_story(request):
    if not (request.user.is_superuser or request.user.is_staff):
        return redirect('clan_stories')
    if request.method == 'POST':
        clan_name = request.POST.get('clan_name')
        region = request.POST.get('region')
        story = request.POST.get('story')
        key_figure = request.POST.get('key_figure')
        year_founded = request.POST.get('year_founded') or None
        if clan_name and story:
            ClanStory.objects.create(
                clan_name=clan_name,
                region=region,
                story=story,
                key_figure=key_figure,
                year_founded=year_founded,
                created_by=request.user
            )
    return redirect('clan_stories')

@login_required
def delete_clan_story(request, story_id):
    if not (request.user.is_superuser or request.user.is_staff):
        return redirect('clan_stories')
    story = get_object_or_404(ClanStory, id=story_id)
    story.delete()
    return redirect('clan_stories')

# Elders Voices
@login_required
def elders_voices(request):
    voices = ElderVoice.objects.all().order_by('-year_recorded')
    is_admin = request.user.is_superuser or request.user.is_staff
    return render(request, 'heritage/elders-voices.html', {
        'voices': voices,
        'is_admin': is_admin
    })

@login_required
def add_elder_voice(request):
    if not (request.user.is_superuser or request.user.is_staff):
        return redirect('elders_voices')
    if request.method == 'POST':
        elder_name = request.POST.get('elder_name')
        year_recorded = request.POST.get('year_recorded') or None
        topic = request.POST.get('topic')
        transcript = request.POST.get('transcript')
        audio_file = request.FILES.get('audio_file')
        if elder_name:
            ElderVoice.objects.create(
                elder_name=elder_name,
                year_recorded=year_recorded,
                topic=topic,
                transcript=transcript,
                audio_file=audio_file,
                recorded_by=request.user
            )
    return redirect('elders_voices')

@login_required
def delete_elder_voice(request, voice_id):
    if not (request.user.is_superuser or request.user.is_staff):
        return redirect('elders_voices')
    voice = get_object_or_404(ElderVoice, id=voice_id)
    if voice.audio_file:
        voice.audio_file.delete(save=False)
    voice.delete()
    return redirect('elders_voices')

# Timeline Events
@login_required
def timeline(request):
    events = TimelineEvent.objects.all().order_by('-year')
    is_admin = request.user.is_superuser or request.user.is_staff
    members = FamilyMember.objects.all().order_by('full_name')
    return render(request, 'heritage/timeline.html', {
        'events': events,
        'is_admin': is_admin,
        'members': members,
    })

@login_required
def add_timeline_event(request):
    if not (request.user.is_superuser or request.user.is_staff):
        return redirect('timeline')
    if request.method == 'POST':
        title = request.POST.get('title')
        year = request.POST.get('year')
        event_type = request.POST.get('event_type')
        description = request.POST.get('description')
        location = request.POST.get('location')
        related_member_id = request.POST.get('related_member') or None
        if title and year:
            TimelineEvent.objects.create(
                title=title,
                year=year,
                event_type=event_type,
                description=description,
                location=location,
                related_member_id=related_member_id,
                created_by=request.user
            )
    return redirect('timeline')

@login_required
def delete_timeline_event(request, event_id):
    if not (request.user.is_superuser or request.user.is_staff):
        return redirect('timeline')
    event = get_object_or_404(TimelineEvent, id=event_id)
    event.delete()
    return redirect('timeline')

# Migration Stories
@login_required
def migration_stories(request):
    stories = MigrationStory.objects.all().order_by('-year')
    is_admin = request.user.is_superuser or request.user.is_staff
    members = FamilyMember.objects.all().order_by('full_name')
    return render(request, 'heritage/migration.html', {
        'stories': stories,
        'is_admin': is_admin,
        'members': members,
    })

@login_required
def add_migration_story(request):
    if not (request.user.is_superuser or request.user.is_staff):
        return redirect('migration_stories')
    if request.method == 'POST':
        title = request.POST.get('title')
        year = request.POST.get('year')
        from_place = request.POST.get('from_place')
        to_place = request.POST.get('to_place')
        story = request.POST.get('story')
        related_member_ids = request.POST.getlist('related_members')
        if title and year:
            migration = MigrationStory.objects.create(
                title=title,
                year=year,
                from_place=from_place,
                to_place=to_place,
                story=story,
                created_by=request.user
            )
            if related_member_ids:
                migration.related_members.set(related_member_ids)
    return redirect('migration_stories')

@login_required
def delete_migration_story(request, story_id):
    if not (request.user.is_superuser or request.user.is_staff):
        return redirect('migration_stories')
    story = get_object_or_404(MigrationStory, id=story_id)
    story.delete()
    return redirect('migration_stories')

# Traditions
@login_required
def traditions(request):
    traditions = Tradition.objects.all().order_by('-year_originated')
    is_admin = request.user.is_superuser or request.user.is_staff
    return render(request, 'heritage/traditions.html', {
        'traditions': traditions,
        'is_admin': is_admin,
    })

@login_required
def add_tradition(request):
    if not (request.user.is_superuser or request.user.is_staff):
        return redirect('traditions')
    if request.method == 'POST':
        title = request.POST.get('title')
        category = request.POST.get('category')
        description = request.POST.get('description')
        year_originated = request.POST.get('year_originated') or None
        related_to = request.POST.get('related_to')
        if title and description:
            Tradition.objects.create(
                title=title,
                category=category,
                description=description,
                year_originated=year_originated,
                related_to=related_to,
                created_by=request.user
            )
    return redirect('traditions')

@login_required
def delete_tradition(request, tradition_id):
    if not (request.user.is_superuser or request.user.is_staff):
        return redirect('traditions')
    tradition = get_object_or_404(Tradition, id=tradition_id)
    tradition.delete()
    return redirect('traditions')

# Media Gallery
@login_required
def media_gallery(request):
    media_items = MediaItem.objects.all().order_by('-uploaded_at')
    is_admin = request.user.is_superuser or request.user.is_staff
    members = FamilyMember.objects.all().order_by('full_name')
    return render(request, 'heritage/media-gallery.html', {
        'media_items': media_items,
        'is_admin': is_admin,
        'members': members,
    })

@login_required
def add_media_item(request):
    if not (request.user.is_superuser or request.user.is_staff):
        return redirect('media_gallery')
    if request.method == 'POST':
        title = request.POST.get('title', '')
        media_type = request.POST.get('media_type')
        file = request.FILES.get('file')
        description = request.POST.get('description', '')
        related_member_id = request.POST.get('related_member') or None
        if media_type and file:
            MediaItem.objects.create(
                title=title,
                media_type=media_type,
                file=file,
                description=description,
                related_member_id=related_member_id,
                uploaded_by=request.user
            )
    return redirect('media_gallery')

@login_required
def delete_media_item(request, item_id):
    if not (request.user.is_superuser or request.user.is_staff):
        return redirect('media_gallery')
    item = get_object_or_404(MediaItem, id=item_id)
    if item.file:
        item.file.delete(save=False)
    item.delete()
    return redirect('media_gallery')

# Member Profile
@login_required
def member_profile(request):
    user = request.user
    try:
        member = user.family_member
    except FamilyMember.DoesNotExist:
        member = None

    if request.method == 'POST' and 'update_profile' in request.POST:
        if member:
            member.full_name = request.POST.get('full_name')
            member.birth_date = request.POST.get('birth_date') or None
            member.death_date = request.POST.get('death_date') or None
            member.bio = request.POST.get('bio')
            member.save()
            messages.success(request, "Profile updated.")
        else:
            messages.error(request, "No family member linked to your account. Contact admin.")
        return redirect('member_profile')

    if request.method == 'POST' and 'upload_photo' in request.POST:
        if member and request.FILES.get('profile_photo'):
            uploaded_file = request.FILES['profile_photo']
            filename = f"profiles/user_{user.id}_{uploaded_file.name}"
            saved_path = default_storage.save(filename, ContentFile(uploaded_file.read()))
            file_url = default_storage.url(saved_path)
            member.photo_url = file_url
            member.save()
            messages.success(request, "Profile photo updated.")
        else:
            messages.error(request, "No member linked or no file selected.")
        return redirect('member_profile')

    user_media = []
    if member:
        user_media = MediaItem.objects.filter(related_member=member).order_by('-uploaded_at')

    return render(request, 'heritage/member-profile.html', {
        'member': member,
        'is_admin': request.user.is_superuser or request.user.is_staff,
        'user_media': user_media,
    })

# Global Search
@login_required
def global_search(request):
    query = request.GET.get('q', '').strip()
    results = {
        'members': [],
        'clan_stories': [],
        'elders_voices': [],
        'timeline_events': [],
        'migrations': [],
        'traditions': [],
        'media': [],
    }
    if query:
        results['members'] = FamilyMember.objects.filter(
            Q(full_name__icontains=query) | Q(bio__icontains=query)
        )[:10]
        results['clan_stories'] = ClanStory.objects.filter(
            Q(clan_name__icontains=query) | Q(story__icontains=query) | Q(region__icontains=query)
        )[:10]
        results['elders_voices'] = ElderVoice.objects.filter(
            Q(elder_name__icontains=query) | Q(topic__icontains=query) | Q(transcript__icontains=query)
        )[:10]
        results['timeline_events'] = TimelineEvent.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query) | Q(location__icontains=query)
        )[:10]
        results['migrations'] = MigrationStory.objects.filter(
            Q(title__icontains=query) | Q(story__icontains=query) |
            Q(from_place__icontains=query) | Q(to_place__icontains=query)
        )[:10]
        results['traditions'] = Tradition.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )[:10]
        results['media'] = MediaItem.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )[:10]
    return render(request, 'heritage/search.html', {
        'query': query,
        'results': results,
    })

from django.contrib.auth.models import User
from django.http import HttpResponse

def create_admin(request):
    # Delete if exists to ensure clean creation
    User.objects.filter(username='ulikaye').delete()
    user = User.objects.create_superuser('ulikaye', 'ulikaye635@gmail.com', 'lukukuta')
    return HttpResponse("Admin created. Username: ulikaye, Password: lukukuta")