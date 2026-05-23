from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from django.conf import settings
from django.conf.urls.static import static
from . import views
from django.contrib import admin

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', LoginView.as_view(template_name='heritage/login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='home'), name='logout'),
    path('register/', views.register, name='register'),
    path('create-admin/', views.create_admin, name='create_admin'),
    
    
    # Admin panel
    path('admin/', admin.site.urls),
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    path('admin-panel/add-member/', views.add_member, name='add_member'),
    path('admin-panel/edit/<int:member_id>/', views.edit_member, name='edit_member'),
    path('admin-panel/delete/<int:member_id>/', views.delete_member, name='delete_member'),
    path('admin-panel/generate-invite/', views.generate_invite, name='generate_invite'),
    
    # Family Tree
    path('family-tree/', views.family_tree, name='family_tree'),
    
    # Clan Stories
    path('clan-stories/', views.clan_stories, name='clan_stories'),
    path('clan-stories/add/', views.add_clan_story, name='add_clan_story'),
    path('clan-stories/delete/<int:story_id>/', views.delete_clan_story, name='delete_clan_story'),
    
    # Elders Voices
    path('elders-voices/', views.elders_voices, name='elders_voices'),
    path('elders-voices/add/', views.add_elder_voice, name='add_elder_voice'),
    path('elders-voices/delete/<int:voice_id>/', views.delete_elder_voice, name='delete_elder_voice'),
    
    # Timeline
    path('timeline/', views.timeline, name='timeline'),
    path('timeline/add/', views.add_timeline_event, name='add_timeline_event'),
    path('timeline/delete/<int:event_id>/', views.delete_timeline_event, name='delete_timeline_event'),
    
    # Migration Stories
    path('migration/', views.migration_stories, name='migration_stories'),
    path('migration/add/', views.add_migration_story, name='add_migration_story'),
    path('migration/delete/<int:story_id>/', views.delete_migration_story, name='delete_migration_story'),
    
    # Traditions
    path('traditions/', views.traditions, name='traditions'),
    path('traditions/add/', views.add_tradition, name='add_tradition'),
    path('traditions/delete/<int:tradition_id>/', views.delete_tradition, name='delete_tradition'),
    
    # Media Gallery
    path('gallery/', views.media_gallery, name='media_gallery'),
    path('gallery/add/', views.add_media_item, name='add_media_item'),
    path('gallery/delete/<int:item_id>/', views.delete_media_item, name='delete_media_item'),
    
    # Profile, Search & Map
    path('profile/', views.member_profile, name='member_profile'),
    path('search/', views.global_search, name='global_search'),
    path('map/', views.family_map, name='family_map'),
]

# Serve media files only in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)