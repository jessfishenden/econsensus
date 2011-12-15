from django.core.urlresolvers import reverse
from django.template import loader, Context
from publicweb.tests.decision_test_case import DecisionTestCase
import publicweb.views

class SVGChartTest(DecisionTestCase):
    feedback_stats = {
        'question': 3,
        'danger': 1,
        'concern': 2,
        'consensus': 0,
        'all': 9
        }

    def test_calculate_svg_bars(self):
        bar_heights = publicweb.views.calculate_svg_bars(self.feedback_stats, 36)

        self.assertEquals(bar_heights['question']['height'], 36)
        self.assertEquals(bar_heights['question']['left'], 0)
        self.assertEquals(bar_heights['danger']['height'], 12)
        self.assertEquals(bar_heights['danger']['left'], 24)
        self.assertEquals(bar_heights['concern']['height'], 24)
        self.assertEquals(bar_heights['concern']['left'], 12)
        self.assertEquals(bar_heights['consensus']['height'], 2)
        self.assertEquals(bar_heights['consensus']['left'], 34)

        self.assertEquals(bar_heights['max_height'], 36)

    def test_svg_chart(self):
        svg_bar_template = u'<rect width="9" height="%d" x="%d" y="%d" class="%s" />'

        bars = publicweb.views.calculate_svg_bars(self.feedback_stats, 36)
        svg_template = loader.get_template('feedback_infographic.svg')
        svg_snippet = svg_template.render(Context(dict(bars=bars)))

        self.assertTrue(svg_snippet.find(u'height="%d">' % bars['max_height']) >  0)
        indent = 0
        for fback in ['question', 'danger', 'concern', 'consensus']:
            self.assertTrue(svg_snippet.find(svg_bar_template % \
                                (bars[fback]['height'], indent, bars[fback]['left'], fback)) > 0)
            indent += 12
