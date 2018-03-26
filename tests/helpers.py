import six


class SoqlAssertions(object):
    def assertSoqlEqual(self, node, soql):
        self.assertEqual(six.u(str(node)), six.u(soql))
        self.assertEqual(six.b(str(node)), six.b(soql))
