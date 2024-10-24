from django.contrib import admin

from .models import AccessToken, Annotation, Lamning, LamningWikipediaLink, Comment, Feedback, CustomTag, KMRLamningType, UserDetails

class LamningAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'created_time', 'changed_time']
    list_filter = ['created_time', 'changed_time', 'user']
    search_fields = ['description', 'title']

class CommentAdmin(admin.ModelAdmin):
    list_display = ['content', 'user', 'created_time']
    list_filter = ['created_time', 'user']
    search_fields = ['content']

class LamningWikipediaLinkAdmin(admin.ModelAdmin):
    list_display = ['kmr_lamning', 'wikipedia', 'created_time']
    list_filter = ['kmr_lamning', 'wikipedia']
    search_fields = ['kmr_lamning', 'wikipedia']

class AnnotationAdmin(admin.ModelAdmin):
    list_display = ['title', 'target_type', 'author_name_string', 'publisher', 'created_time']
    list_filter = ['target_type', 'author_name_string', 'publisher']
    search_fields = ['title', 'author_name_string', 'subject']
    list_per_page = 500

class KMRLamningTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'raa_id', 'slug']
    list_filter = ['raa_id']
    search_fields = ['name', 'description']

class CustomTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_time']
    list_filter = ['created_time']
    search_fields = ['name', 'description']

class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_time']
    list_filter = ['user']
    search_fields = ['message']

class AccessTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_time']
    list_filter = ['user']
    search_fields = ['token']

class UserDetailsAdmin(admin.ModelAdmin):
    list_display = ['user', 'profile_privacy']
    list_filter = ['profile_privacy']
    search_fields = ['user']

admin.site.register(Lamning, LamningAdmin)
admin.site.register(LamningWikipediaLink, LamningWikipediaLinkAdmin)
admin.site.register(Annotation, AnnotationAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Feedback, FeedbackAdmin)
admin.site.register(CustomTag, CustomTagAdmin)
admin.site.register(KMRLamningType, KMRLamningTypeAdmin)
admin.site.register(AccessToken, AccessTokenAdmin)
admin.site.register(UserDetails, UserDetailsAdmin)
