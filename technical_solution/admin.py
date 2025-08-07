from django.contrib import admin

# Register your models here.
from technical_solution.models import TechnicalSolution, TechnicalSolutionRecommendation, TechnicalSolutionReview

admin.site.register(TechnicalSolution)
admin.site.register(TechnicalSolutionReview)