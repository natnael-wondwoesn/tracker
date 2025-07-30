from django.core.management.base import BaseCommand
from django.utils.timezone import now
from core.models import ChildProfile
from log.models import  HeartBeat, Behavior, Sleep, BloodPressure, Food, ScratchNotes
from report.models import Report
from gemini import summarize_dashboard_data

import json

class Command(BaseCommand):
    help = "Generate daily reports for all children using local DB data (not API)."

    def handle(self, *args, **options):
        today = now().date()
        children = ChildProfile.objects.all()

        for child in children:
            print("Child: ", child.full_name)
            # Manually collect all related log data
            dashboard_data = {
                "heartbeat": list(HeartBeat.objects.filter(child=child).values()),
                "behavior": list(Behavior.objects.filter(child=child).values()),
                "sleep": list(Sleep.objects.filter(child=child).values()),
                "bloodpressure": list(BloodPressure.objects.filter(child=child).values()),
                "food": list(Food.objects.filter(child=child).values()),
                "scratchnotes": list(ScratchNotes.objects.filter(child=child).values())
            }

            if not any(dashboard_data.values()):
                self.stdout.write(self.style.WARNING(f"No data found for child {child.full_name}"))
                continue

            # Call Gemini
            report = summarize_dashboard_data(dashboard_data)
            print(report["insight"])

            if "error" in report:
                self.stderr.write(f"⚠️ Failed to generate valid report for child {child.full_name}")
                continue

            # Save the report
            Report.objects.create(
                child=child,
                report_type="weekly",
                summary=report["summary"],
                suggestion=report["suggestion"],
                insight=report["insight"]  # assumes JSONField
            )

            self.stdout.write(self.style.SUCCESS(f"✅ Report saved for {child.full_name}"))
