from django.db import models
from core.models import ChildProfile


class Report(models.Model):
    REPORT_TYPES = (
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
    )

    child = models.ForeignKey(ChildProfile, on_delete=models.CASCADE)  # replace with your actual child model
    report_type = models.CharField(max_length=10, choices=REPORT_TYPES)
    generated_at = models.DateTimeField(auto_now_add=True)
    summary = models.TextField()
    suggestion = models.TextField()

    # JSON field for structured insights
    insight = models.JSONField()

    def __str__(self):
        return f"{self.report_type.title()} Report for Child {self.child_id} on {self.generated_at.date()}"
