from django.contrib.sitemaps import Sitemap
from django.urls import reverse

class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'daily'

    def items(self):
        return ['home', ]

    def location(self, item):
        return f'/{item}/' if item != 'home' else '/'

class NetHealthImpactSitemap(Sitemap):
    priority = 0.7
    changefreq = 'weekly'

    def items(self):
        return ['calculate-net-health-impact']

    def location(self, item):
        return reverse(item)
   
class HSRCalculatorSitemap(Sitemap):
    priority = 0.7
    changefreq = 'weekly'

    def items(self):
        return ['hsr-calculate']

    def location(self, item):
        return reverse(item)
    
class HENICalculatorSitemap(Sitemap):
    priority = 0.7
    changefreq = 'weekly'

    def items(self):
        return ['heni-calculate']

    def location(self, item):
        return reverse(item)

class EnvironmentalImpactSitemap(Sitemap):
    priority = 0.7
    changefreq = 'weekly'

    def items(self):
        return ['environmental-impact']

    def location(self, item):
        return reverse(item)

class FcsCalculatorSitemap(Sitemap):
    priority = 0.7
    changefreq = 'weekly'

    def items(self):
        return ['fcs-calculate']

    def location(self, item):
        return reverse(item)