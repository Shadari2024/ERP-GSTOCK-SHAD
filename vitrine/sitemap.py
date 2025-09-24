from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import DemandeDemo

class StaticViewSitemap(Sitemap):
    priority = 1.0
    changefreq = 'weekly'

    def items(self):
        return ['vitrine:accueil', 'vitrine:features', 'vitrine:pricing', 'vitrine:contact', 'vitrine:demo']

    def location(self, item):
        return reverse(item)

class DemoRequestsSitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.8

    def items(self):
        return DemandeDemo.objects.filter(est_traite=False)

    def lastmod(self, obj):
        return obj.date_creation

sitemaps = {
    'static': StaticViewSitemap,
    'demo': DemoRequestsSitemap,
}