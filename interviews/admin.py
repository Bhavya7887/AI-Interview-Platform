from django.contrib import admin
from .models import Interview, InterviewQuestion, InterviewResponse

class QuestionInline(admin.TabularInline):
    model = InterviewQuestion
    extra = 0

class ResponseInline(admin.TabularInline):
    model = InterviewResponse
    extra = 0
    readonly_fields = ("score", "topic", "submitted_at")

@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ("role", "level", "number_of_questions", "completed", "created_at")
    list_filter = ("level", "completed", "created_at")
    search_fields = ("role",)
    inlines = [QuestionInline]

@admin.register(InterviewQuestion)
class InterviewQuestionAdmin(admin.ModelAdmin):
    list_display = ("interview", "order", "question_type")
    list_filter = ("question_type",)

@admin.register(InterviewResponse)
class InterviewResponseAdmin(admin.ModelAdmin):
    list_display = ("interview", "question", "score", "overtime", "submitted_at")
    list_filter = ("score", "overtime")
