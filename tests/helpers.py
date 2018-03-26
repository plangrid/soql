from soql.utils import to_unicode


class SoqlAssertions(object):
    def assertSoqlEqual(self, node, soql):
        self.assertEqual(to_unicode(node), to_unicode(soql))
