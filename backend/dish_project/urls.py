from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView
from django.urls import path, re_path
from api.sitemaps import StaticViewSitemap, EnvironmentalImpactSitemap, FcsCalculatorSitemap, HENICalculatorSitemap, HSRCalculatorSitemap, NetHealthImpactSitemap

sitemaps = {
    'environmental_impact': EnvironmentalImpactSitemap,
    'fcs_calculator': FcsCalculatorSitemap,
    'heni_calculator': HENICalculatorSitemap,
    'hsr_calculator': HSRCalculatorSitemap,
    'net_health_impact': NetHealthImpactSitemap,
    'static': StaticViewSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    
    # Serve robots.txt
    path('robots.txt', TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
]

# Add debug toolbar URLs if in debug mode
if settings.DEBUG and 'debug_toolbar' in settings.INSTALLED_APPS:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
