from django.contrib import admin

from .models import ChatMessage, ChatSession, Scheme, TaxDocument


@admin.register(Scheme)
class SchemeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "ministry",
        "state",
        "category",
        "language",
        "is_active",
    )
    list_filter = (
        "ministry",
        "state",
        "category",
        "language",
        "is_active",
    )
    search_fields = (
        "name",
        "short_description",
        "full_description",
        "eligibility",
    )


@admin.register(TaxDocument)
class TaxDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "document_type",
        "financial_year",
        "language",
        "is_active",
    )
    list_filter = (
        "document_type",
        "financial_year",
        "language",
        "is_active",
    )
    search_fields = (
        "title",
        "description",
        "content",
    )


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = (
        "session_id",
        "user_identifier",
        "title",
        "detected_language",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "session_id",
        "user_identifier",
        "title",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
    )


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = (
        "session",
        "role",
        "detected_language",
        "created_at",
    )
    list_filter = (
        "role",
        "detected_language",
    )
    search_fields = (
        "content",
        "session__session_id",
    )
    readonly_fields = ("created_at",)