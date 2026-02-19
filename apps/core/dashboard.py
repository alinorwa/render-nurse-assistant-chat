from django.views.generic import TemplateView
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.db.models import Count, Sum, Case, When, IntegerField
from django.db.models.functions import TruncDay
from django.utils import timezone
from datetime import timedelta
from django.utils.translation import gettext_lazy as _

# استيراد المودلز
# Import models
from apps.accounts.models import User
from apps.chat.models import ChatSession, EpidemicAlert

@method_decorator(staff_member_required, name='dispatch')
class MedicalDashboardView(TemplateView):
    template_name = "admin/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # إعدادات العناوين لقالب Unfold
        # Title settings for Unfold template
        context['title'] = "Medical Analytics"
        context['subtitle'] = "An overview of the camp's situation and daily activities"
        
        # 1. إحصائيات اللغات (Pie Chart)
        # 1. Language Statistics (Pie Chart)
        language_data = User.objects.filter(role='REFUGEE').values('native_language').annotate(total=Count('id'))
        
        lang_labels = []
        lang_counts = []
        lang_dict = dict(User.LANGUAGE_CHOICES)
        
        for item in language_data:
            code = item['native_language']
            label = lang_dict.get(code, code)
            lang_labels.append(label)
            lang_counts.append(item['total'])

        context['chart_languages'] = {
            "type": "doughnut",
            "data": {
                "labels": lang_labels,
                "datasets": [{
                    "data": lang_counts,
                    "backgroundColor": ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"],
                    "borderWidth": 0
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {"legend": {"position": "bottom"}}
            }
        }

        # 2. النشاط اليومي لآخر 7 أيام (Line Chart)
        # 2. Daily activity for last 7 days (Line Chart)
        last_week = timezone.now() - timedelta(days=7)
        daily_sessions = ChatSession.objects.filter(start_time__gte=last_week)\
            .annotate(date=TruncDay('start_time'))\
            .values('date')\
            .annotate(count=Count('id'))\
            .order_by('date')
            
        context['chart_activity'] = {
            "type": "line",
            "data": {
                "labels": [item['date'].strftime('%Y-%m-%d') for item in daily_sessions],
                "datasets": [{
                    "label": "New sessions",
                    "data": [item['count'] for item in daily_sessions],
                    "borderColor": "#0ea5e9",
                    "backgroundColor": "rgba(14, 165, 233, 0.1)",
                    "fill": True,
                    "tension": 0.4
                }]
            }
        }

        # 3. الإنذارات الوبائية (Stacked Bar Chart - Active vs Controlled)
        # 3. Epidemic Alerts (Stacked Bar Chart - Active vs Controlled)
        # نقوم بتجميع البيانات وفصلها حسب حقل is_acknowledged
        # Group data and separate by is_acknowledged field
        epidemic_stats = EpidemicAlert.objects.values('symptom_category').annotate(
            active_cases=Sum(
                Case(When(is_acknowledged=False, then='case_count'), default=0, output_field=IntegerField())
            ),
            controlled_cases=Sum(
                Case(When(is_acknowledged=True, then='case_count'), default=0, output_field=IntegerField())
            )
        ).order_by('-active_cases')

        context['chart_epidemics'] = {
            "type": "bar",
            "data": {
                "labels": [item['symptom_category'] for item in epidemic_stats],
                "datasets": [
                    {
                        "label": "Active (Urgent)",
                        "data": [item['active_cases'] for item in epidemic_stats],
                        "backgroundColor": "#dc2626", # أحمر للحالات النشطة / Red for active cases
                        "borderRadius": 4,
                    },
                    {
                        "label": "Controlled (Resolved)",
                        "data": [item['controlled_cases'] for item in epidemic_stats],
                        "backgroundColor": "#10b981", # أخضر للحالات المنتهية / Green for resolved cases
                        "borderRadius": 4,
                    }
                ]
            },
            # نمرر خيارات التكديس هنا ليدمجها ملف الـ HTML
            # Pass stacking options here for HTML file to merge
            "options": {
                "scales": {
                    "x": {"stacked": True},
                    "y": {"stacked": True}
                }
            }
        }
        
        # KPIs
        context['kpi'] = {
            "total_refugees": User.objects.filter(role='REFUGEE').count(),
            "urgent_sessions": ChatSession.objects.filter(priority=2, is_active=True).count(),
            "active_now": ChatSession.objects.filter(is_active=True).count()
        }

        return context