import datetime
import time
import unittest

from aioprometheus import (
    Collector, Counter, Gauge, Summary, Registry)
from aioprometheus.formats import binary_format_available
if binary_format_available:
    from aioprometheus.formats import BinaryFormatter
    import prometheus_metrics_proto as pmp


@unittest.skipUnless(
    binary_format_available, "Binary formatter plugin is not available")
class TestProtobufFormat(unittest.TestCase):

    # Test Utils
    def _create_protobuf_object(self, data, metrics, metric_type,
                                const_labels={}, ts=False):
        pb_metrics = []
        for i in metrics:
            labels = [pmp.LabelPair(name=k, value=v) for k, v in i[0].items()]
            c_labels = [
                pmp.LabelPair(name=k, value=v) for k, v in const_labels.items()]
            labels.extend(c_labels)

            if metric_type == pmp.COUNTER:
                metric = pmp.Metric(
                    counter=pmp.Counter(value=i[1]),
                    label=labels)
            elif metric_type == pmp.GAUGE:
                metric = pmp.Metric(
                    gauge=pmp.Gauge(value=i[1]),
                    label=labels)
            elif metric_type == pmp.SUMMARY:
                quantiles = []

                for k, v in i[1].items():
                    if not isinstance(k, str):
                        q = pmp.Quantile(quantile=k, value=v)
                        quantiles.append(q)

                metric = pmp.Metric(
                    summary=pmp.Summary(quantile=quantiles,
                                        sample_sum=i[1]['sum'],
                                        sample_count=i[1]['count']),
                    label=labels)
            elif metric_type == pmp.HISTOGRAM:
                buckets = []

                for k, v in i[1].items():
                    if not isinstance(k, str):
                        bucket = pmp.Bucket(
                            cumulative_count=v, upper_bound=k)
                        buckets.append(bucket)

                metric = pmp.Metric(
                    summary=pmp.Histogram(buckets=buckets,
                                          histogram_sum=i[1]['sum'],
                                          histogram_count=i[1]['count']),
                    label=labels)

            else:
                raise TypeError("Not a valid metric")

            if ts:
                metric.timestamp_ms = int(
                    datetime.datetime.now(
                        tz=datetime.timezone.utc).timestamp() * 1000)

            pb_metrics.append(metric)

        valid_result = pmp.MetricFamily(
            name=data['name'],
            help=data['doc'],
            type=metric_type,
            metric=pb_metrics
        )

        return valid_result

    def _protobuf_metric_equal(self, ptb1, ptb2):
        if ptb1 is ptb2:
            return True

        if not ptb1 or not ptb2:
            return False

        # start all the filters
        # 1st level:  Metric Family
        if (ptb1.name != ptb2.name) or\
           (ptb1.help != ptb2.help) or\
           (ptb1.type != ptb2.type) or\
           (len(ptb1.metric) != len(ptb2.metric)):
            return False

        def sort_metric(v):
            """ Small function to order the lists of protobuf """
            x = sorted(v.label, key=lambda x: x.name + x.value)
            return("".join([i.name + i.value for i in x]))

        # Before continuing, sort stuff
        mts1 = sorted(ptb1.metric, key=sort_metric)
        mts2 = sorted(ptb2.metric, key=sort_metric)

        # Now that they are ordered we can compare each element with each
        for k, m1 in enumerate(mts1):
            m2 = mts2[k]

            # Check ts
            if m1.timestamp_ms != m2.timestamp_ms:
                return False

            # Check value
            if ptb1.type == pmp.COUNTER and ptb2.type == pmp.COUNTER:
                if m1.counter.value != m2.counter.value:
                    return False
            elif ptb1.type == pmp.GAUGE and ptb2.type == pmp.GAUGE:
                if m1.gauge.value != m2.gauge.value:
                    return False
            elif ptb1.type == pmp.SUMMARY and ptb2.type == pmp.SUMMARY:
                mm1, mm2 = m1.summary, m2.summary
                if ((mm1.sample_count != mm2.sample_count) or
                        (mm1.sample_sum != mm2.sample_sum)):
                    return False

                # order quantiles to test
                mm1_quantiles = sorted(
                    [(x.quantile, x.value) for x in mm1.quantile])
                mm2_quantiles = sorted(
                    [(x.quantile, x.value) for x in mm2.quantile])

                if mm1_quantiles != mm2_quantiles:
                    return False

            elif ptb1.type == pmp.HISTOGRAM and ptb2.type == pmp.HISTOGRAM:
                mm1, mm2 = m1.summary, m2.summary
                if ((mm1.sample_count != mm2.sample_count) or
                        (mm1.sample_sum != mm2.sample_sum)):
                    return False

                # order buckets to test
                # mm1_buckets = sorted(mm1.bucket, key=lambda x: x.bucket)
                mm1_buckets = sorted(
                    [(x.upper_bound, x.cumulative_count) for x in mm1.bucket])
                # mm2_buckets = sorted(mm2.bucket, key=lambda x: x.bucket)
                mm2_buckets = sorted(
                    [(x.upper_bound, x.cumulative_count) for x in mm2.bucket])

                if mm1_buckets != mm2_buckets:
                    return False

            else:
                return False

            # Check labels
            # Sort labels
            l1 = sorted(m1.label, key=lambda x: x.name + x.value)
            l2 = sorted(m2.label, key=lambda x: x.name + x.value)
            if not all([l.name == l2[k].name and l.value == l2[k].value for k, l in enumerate(l1)]):
                return False

        return True

    def test_create_protobuf_object_wrong(self):
        data = {
            'name': "logged_users_total",
            'doc': "Logged users in the application",
            'const_labels': None,
        }

        values = (
            ({'country': "sp", "device": "desktop"}, 520),
            ({'country': "us", "device": "mobile"}, 654),
        )

        with self.assertRaises(TypeError) as context:
            self._create_protobuf_object(data, values, 7)

        self.assertEqual("Not a valid metric", str(context.exception))

    def test_timestamp(self):
        data = {
            'name': "logged_users_total",
            'doc': "Logged users in the application",
            'const_labels': None,
        }

        values = (
            ({'country': "sp", "device": "desktop"}, 520),
            ({'country': "us", "device": "mobile"}, 654),
        )

        c = self._create_protobuf_object(data, values, pmp.COUNTER, {})
        for i in c.metric:
            self.assertEqual(0, i.timestamp_ms)

        c = self._create_protobuf_object(data, values, pmp.COUNTER, {}, True)
        for i in c.metric:
            self.assertIsNotNone(i.timestamp_ms)

        self.assertEqual(c, c)
        self.assertTrue(self._protobuf_metric_equal(c, c))
        time.sleep(0.5)
        c2 = self._create_protobuf_object(data, values, pmp.COUNTER, {}, True)
        self.assertFalse(self._protobuf_metric_equal(c, c2))

    def test_protobuf_metric_equal_not_metric(self):
        data = {
            'name': "logged_users_total",
            'doc': "Logged users in the application",
            'const_labels': None,
        }

        values = (({"device": "mobile", 'country': "us"}, 654),
                  ({'country': "sp", "device": "desktop"}, 520))
        pt1 = self._create_protobuf_object(data, values, pmp.COUNTER)

        self.assertFalse(self._protobuf_metric_equal(pt1, None))
        self.assertFalse(self._protobuf_metric_equal(None, pt1))

    def test_protobuf_metric_equal_not_basic_data(self):
        data = {
            'name': "logged_users_total",
            'doc': "Logged users in the application",
            'const_labels': None,
        }

        pt1 = self._create_protobuf_object(data, (), pmp.COUNTER)

        data2 = data.copy()
        data2['name'] = "other"
        pt2 = self._create_protobuf_object(data2, (), pmp.COUNTER)
        self.assertFalse(self._protobuf_metric_equal(pt1, pt2))

        data2 = data.copy()
        data2['doc'] = "other"
        pt2 = self._create_protobuf_object(data2, (), pmp.COUNTER)
        self.assertFalse(self._protobuf_metric_equal(pt1, pt2))

        pt2 = self._create_protobuf_object(data, (), pmp.SUMMARY)
        self.assertFalse(self._protobuf_metric_equal(pt1, pt2))

        pt3 = self._create_protobuf_object(data, (), pmp.HISTOGRAM)
        self.assertFalse(self._protobuf_metric_equal(pt2, pt3))

    def test_protobuf_metric_equal_not_labels(self):
        data = {
            'name': "logged_users_total",
            'doc': "Logged users in the application",
            'const_labels': None,
        }

        values = (({"device": "mobile", 'country': "us"}, 654),)
        pt1 = self._create_protobuf_object(data, values, pmp.COUNTER)

        values2 = (({"device": "mobile", 'country': "es"}, 654),)
        pt2 = self._create_protobuf_object(data, values2, pmp.COUNTER)

        self.assertFalse(self._protobuf_metric_equal(pt1, pt2))

    def test_protobuf_metric_equal_counter(self):
        data = {
            'name': "logged_users_total",
            'doc': "Logged users in the application",
            'const_labels': None,
        }

        counter_data = (
            {
                'pt1': (({'country': "sp", "device": "desktop"}, 520),
                        ({'country': "us", "device": "mobile"}, 654),),
                'pt2': (({'country': "sp", "device": "desktop"}, 520),
                        ({'country': "us", "device": "mobile"}, 654),),
                'ok': True
            },
            {
                'pt1': (({'country': "sp", "device": "desktop"}, 521),
                        ({'country': "us", "device": "mobile"}, 654),),
                'pt2': (({'country': "sp", "device": "desktop"}, 520),
                        ({'country': "us", "device": "mobile"}, 654),),
                'ok': False
            },
            {
                'pt1': (({'country': "sp", "device": "desktop"}, 520),
                        ({"device": "mobile", 'country': "us"}, 654),),
                'pt2': (({"device": "desktop", 'country': "sp"}, 520),
                        ({'country': "us", "device": "mobile"}, 654),),
                'ok': True
            },
            {
                'pt1': (({"device": "mobile", 'country': "us"}, 654),
                        ({'country': "sp", "device": "desktop"}, 520)),
                'pt2': (({"device": "desktop", 'country': "sp"}, 520),
                        ({'country': "us", "device": "mobile"}, 654),),
                'ok': True
            },
        )

        for i in counter_data:
            p1 = self._create_protobuf_object(data, i['pt1'], pmp.COUNTER)
            p2 = self._create_protobuf_object(data, i['pt2'], pmp.COUNTER)

            if i['ok']:
                self.assertTrue(self._protobuf_metric_equal(p1, p2))
            else:
                self.assertFalse(self._protobuf_metric_equal(p1, p2))

    def test_protobuf_metric_equal_gauge(self):
        data = {
            'name': "logged_users_total",
            'doc': "Logged users in the application",
            'const_labels': None,
        }

        gauge_data = (
            {
                'pt1': (({'country': "sp", "device": "desktop"}, 520),
                        ({'country': "us", "device": "mobile"}, 654),),
                'pt2': (({'country': "sp", "device": "desktop"}, 520),
                        ({'country': "us", "device": "mobile"}, 654),),
                'ok': True
            },
            {
                'pt1': (({'country': "sp", "device": "desktop"}, 521),
                        ({'country': "us", "device": "mobile"}, 654),),
                'pt2': (({'country': "sp", "device": "desktop"}, 520),
                        ({'country': "us", "device": "mobile"}, 654),),
                'ok': False
            },
            {
                'pt1': (({'country': "sp", "device": "desktop"}, 520),
                        ({"device": "mobile", 'country': "us"}, 654),),
                'pt2': (({"device": "desktop", 'country': "sp"}, 520),
                        ({'country': "us", "device": "mobile"}, 654),),
                'ok': True
            },
            {
                'pt1': (({"device": "mobile", 'country': "us"}, 654),
                        ({'country': "sp", "device": "desktop"}, 520)),
                'pt2': (({"device": "desktop", 'country': "sp"}, 520),
                        ({'country': "us", "device": "mobile"}, 654),),
                'ok': True
            },
        )

        for i in gauge_data:
            p1 = self._create_protobuf_object(data, i['pt1'], pmp.GAUGE)
            p2 = self._create_protobuf_object(data, i['pt2'], pmp.GAUGE)

            if i['ok']:
                self.assertTrue(self._protobuf_metric_equal(p1, p2))
            else:
                self.assertFalse(self._protobuf_metric_equal(p1, p2))

    def test_protobuf_metric_equal_summary(self):
        data = {
            'name': "logged_users_total",
            'doc': "Logged users in the application",
            'const_labels': None,
        }

        gauge_data = (
            {
                'pt1': (({'interval': "5s"}, {0.5: 4.0, 0.9: 5.2, 0.99: 5.2, "sum": 25.2, "count": 4}),
                        ({'interval': "10s"}, {0.5: 90, 0.9: 149, 0.99: 150, "sum": 385, "count": 10}),),
                'pt2': (({'interval': "10s"}, {0.5: 90, 0.9: 149, 0.99: 150, "sum": 385, "count": 10}),
                        ({'interval': "5s"}, {0.5: 4.0, 0.9: 5.2, 0.99: 5.2, "sum": 25.2, "count": 4})),
                'ok': True
            },
            {
                'pt1': (({'interval': "5s"}, {0.5: 4.0, 0.9: 5.2, 0.99: 5.2, "sum": 25.2, "count": 4}),
                        ({'interval': "10s"}, {0.5: 90, 0.9: 149, 0.99: 150, "sum": 385, "count": 10}),),
                'pt2': (({'interval': "5s"}, {0.5: 4.0, 0.9: 5.2, 0.99: 5.2, "sum": 25.2, "count": 4}),
                        ({'interval': "10s"}, {0.5: 90, 0.9: 150, 0.99: 150, "sum": 385, "count": 10}),),
                'ok': False
            },
            {
                'pt1': (({'interval': "5s"}, {0.5: 4.0, 0.9: 5.2, 0.99: 5.2, "sum": 25.2, "count": 4}),
                        ({'interval': "10s"}, {0.5: 90, 0.9: 149, 0.99: 150, "sum": 385, "count": 10}),),
                'pt2': (({'interval': "5s"}, {0.5: 4.0, 0.9: 5.2, 0.99: 5.2, "sum": 25.2, "count": 4}),
                        ({'interval': "10s"}, {0.5: 90, 0.9: 149, 0.99: 150, "sum": 385, "count": 11}),),
                'ok': False
            },
        )

        for i in gauge_data:
            p1 = self._create_protobuf_object(data, i['pt1'], pmp.SUMMARY)
            p2 = self._create_protobuf_object(data, i['pt2'], pmp.SUMMARY)

            if i['ok']:
                self.assertTrue(self._protobuf_metric_equal(p1, p2))
            else:
                self.assertFalse(self._protobuf_metric_equal(p1, p2))

#     # Finish Test Utils
#     # ######################################

    def test_headers(self):
        f = BinaryFormatter()
        result = {
            'Content-Type': 'application/vnd.google.protobuf; proto=io.prometheus.client.MetricFamily; encoding=delimited'
        }

        self.assertEqual(result, f.get_headers())

    def test_wrong_format(self):
        data = {
            'name': "logged_users_total",
            'doc': "Logged users in the application",
            'const_labels': {"app": "my_app"},
        }

        f = BinaryFormatter()

        c = Collector(**data)

        with self.assertRaises(TypeError) as context:
            f.marshall_collector(c)

        self.assertEqual('Not a valid object format', str(context.exception))

    def test_counter_format(self):

        data = {
            'name': "logged_users_total",
            'doc': "Logged users in the application",
            'const_labels': None,
        }
        c = Counter(**data)

        counter_data = (
            ({'country': "sp", "device": "desktop"}, 520),
            ({'country': "us", "device": "mobile"}, 654),
            ({'country': "uk", "device": "desktop"}, 1001),
            ({'country': "de", "device": "desktop"}, 995),
            ({'country': "zh", "device": "desktop"}, 520),
        )

        # Construct the result to compare
        valid_result = self._create_protobuf_object(
            data, counter_data, pmp.COUNTER)

        # Add data to the collector
        for i in counter_data:
            c.set_value(i[0], i[1])

        f = BinaryFormatter()

        result = f.marshall_collector(c)

        self.assertTrue(self._protobuf_metric_equal(valid_result, result))

    def test_counter_format_with_const_labels(self):
        data = {
            'name': "logged_users_total",
            'doc': "Logged users in the application",
            'const_labels': {"app": "my_app"},
        }
        c = Counter(**data)

        counter_data = (
            ({'country': "sp", "device": "desktop"}, 520),
            ({'country': "us", "device": "mobile"}, 654),
            ({'country': "uk", "device": "desktop"}, 1001),
            ({'country': "de", "device": "desktop"}, 995),
            ({'country': "zh", "device": "desktop"}, 520),
        )

        # Construct the result to compare
        valid_result = self._create_protobuf_object(
            data, counter_data, pmp.COUNTER, data['const_labels'])

        # Add data to the collector
        for i in counter_data:
            c.set_value(i[0], i[1])

        f = BinaryFormatter()

        result = f.marshall_collector(c)

        self.assertTrue(self._protobuf_metric_equal(valid_result, result))

    def test_gauge_format(self):

        data = {
            'name': "logged_users_total",
            'doc': "Logged users in the application",
            'const_labels': None,
        }
        g = Gauge(**data)

        gauge_data = (
            ({'country': "sp", "device": "desktop"}, 520),
            ({'country': "us", "device": "mobile"}, 654),
            ({'country': "uk", "device": "desktop"}, 1001),
            ({'country': "de", "device": "desktop"}, 995),
            ({'country': "zh", "device": "desktop"}, 520),
        )

        # Construct the result to compare
        valid_result = self._create_protobuf_object(
            data, gauge_data, pmp.GAUGE)

        # Add data to the collector
        for i in gauge_data:
            g.set_value(i[0], i[1])

        f = BinaryFormatter()

        result = f.marshall_collector(g)

        self.assertTrue(self._protobuf_metric_equal(valid_result, result))

    def test_gauge_format_with_const_labels(self):
        data = {
            'name': "logged_users_total",
            'doc': "Logged users in the application",
            'const_labels': {"app": "my_app"},
        }
        g = Gauge(**data)

        gauge_data = (
            ({'country': "sp", "device": "desktop"}, 520),
            ({'country': "us", "device": "mobile"}, 654),
            ({'country': "uk", "device": "desktop"}, 1001),
            ({'country': "de", "device": "desktop"}, 995),
            ({'country': "zh", "device": "desktop"}, 520),
        )

        # Construct the result to compare
        valid_result = self._create_protobuf_object(
            data, gauge_data, pmp.GAUGE, data['const_labels'])

        # Add data to the collector
        for i in gauge_data:
            g.set_value(i[0], i[1])

        f = BinaryFormatter()

        result = f.marshall_collector(g)

        self.assertTrue(self._protobuf_metric_equal(valid_result, result))

    def test_one_summary_format(self):
        data = {
            'name': "logged_users_total",
            'doc': "Logged users in the application",
            'const_labels': {},
        }

        labels = {'handler': '/static'}
        values = [3, 5.2, 13, 4]

        s = Summary(**data)

        for i in values:
            s.add(labels, i)

        tmp_valid_data = [
            (labels, {0.5: 4.0, 0.9: 5.2, 0.99: 5.2, "sum": 25.2, "count": 4}),
        ]
        valid_result = self._create_protobuf_object(data, tmp_valid_data,
                                                    pmp.SUMMARY)

        f = BinaryFormatter()

        result = f.marshall_collector(s)
        self.assertTrue(self._protobuf_metric_equal(valid_result, result))

    def test_one_summary_format_with_const_labels(self):
        data = {
            'name': "logged_users_total",
            'doc': "Logged users in the application",
            'const_labels': {"app": "my_app"},
        }

        labels = {'handler': '/static'}
        values = [3, 5.2, 13, 4]

        s = Summary(**data)

        for i in values:
            s.add(labels, i)

        tmp_valid_data = [
            (labels, {0.5: 4.0, 0.9: 5.2, 0.99: 5.2, "sum": 25.2, "count": 4}),
        ]
        valid_result = self._create_protobuf_object(data, tmp_valid_data,
                                                    pmp.SUMMARY,
                                                    data['const_labels'])

        f = BinaryFormatter()

        result = f.marshall_collector(s)
        self.assertTrue(self._protobuf_metric_equal(valid_result, result))

    def test_summary_format(self):
        data = {
            'name': "logged_users_total",
            'doc': "Logged users in the application",
            'const_labels': {},
        }

        summary_data = (
            ({'interval': "5s"}, [3, 5.2, 13, 4]),
            ({'interval': "10s"}, [1.3, 1.2, 32.1, 59.2, 109.46, 70.9]),
            ({'interval': "10s", 'method': "fast"}, [5, 9.8, 31, 9.7, 101.4]),
        )

        s = Summary(**data)

        for i in summary_data:
            for j in i[1]:
                s.add(i[0], j)

        tmp_valid_data = [
            ({'interval': "5s"}, {0.5: 4.0, 0.9: 5.2, 0.99: 5.2, "sum": 25.2, "count": 4}),
            ({'interval': "10s"}, {0.5: 32.1, 0.9: 59.2, 0.99: 59.2, "sum": 274.15999999999997, "count": 6}),
            ({'interval': "10s", 'method': "fast"}, {0.5: 9.7, 0.9: 9.8, 0.99: 9.8, "sum": 156.9, "count": 5}),
        ]
        valid_result = self._create_protobuf_object(data, tmp_valid_data,
                                                    pmp.SUMMARY)

        f = BinaryFormatter()

        result = f.marshall_collector(s)
        self.assertTrue(self._protobuf_metric_equal(valid_result, result))

    def test_registry_marshall_counter(self):

        format_times = 10

        counter_data = (
            ({'c_sample': '1', 'c_subsample': 'b'}, 400),
        )

        registry = Registry()
        counter = Counter("counter_test", "A counter.", {'type': "counter"})

        # Add data
        [counter.set(c[0], c[1]) for c in counter_data]

        registry.register(counter)

        valid_result = (b'[\n\x0ccounter_test\x12\nA counter.\x18\x00"=\n\r'
                        b'\n\x08c_sample\x12\x011\n\x10\n\x0bc_subsample\x12'
                        b'\x01b\n\x0f\n\x04type\x12\x07counter\x1a\t\t\x00\x00'
                        b'\x00\x00\x00\x00y@')
        f = BinaryFormatter()

        # Check multiple times to ensure multiple marshalling requests
        for i in range(format_times):
            self.assertEqual(valid_result, f.marshall(registry))

    def test_registry_marshall_gauge(self):
        format_times = 10

        gauge_data = (
            ({'g_sample': '1', 'g_subsample': 'b'}, 800),
        )

        registry = Registry()
        gauge = Gauge("gauge_test", "A gauge.", {'type': "gauge"})

        # Add data
        [gauge.set(g[0], g[1]) for g in gauge_data]

        registry.register(gauge)

        valid_result = (b'U\n\ngauge_test\x12\x08A gauge.\x18\x01";'
                        b'\n\r\n\x08g_sample\x12\x011\n\x10\n\x0bg_subsample'
                        b'\x12\x01b\n\r\n\x04type\x12\x05gauge\x12\t\t\x00'
                        b'\x00\x00\x00\x00\x00\x89@')

        f = BinaryFormatter()

        # Check multiple times to ensure multiple marshalling requests
        for i in range(format_times):
            self.assertEqual(valid_result, f.marshall(registry))

    def test_registry_marshall_summary(self):
        format_times = 10

        summary_data = (
            ({'s_sample': '1', 's_subsample': 'b'}, range(4000, 5000, 47)),
        )

        registry = Registry()
        summary = Summary("summary_test", "A summary.", {'type': "summary"})

        # Add data
        [summary.add(i[0], s) for i in summary_data for s in i[1]]

        registry.register(summary)

        valid_result = (b'\x99\x01\n\x0csummary_test\x12\nA summary.'
                        b'\x18\x02"{\n\r\n\x08s_sample\x12\x011\n\x10\n'
                        b'\x0bs_subsample\x12\x01b\n\x0f\n\x04type\x12\x07'
                        b'summary"G\x08\x16\x11\x00\x00\x00\x00\x90"\xf8@'
                        b'\x1a\x12\t\x00\x00\x00\x00\x00\x00\xe0?\x11\x00'
                        b'\x00\x00\x00\x00\x8b\xb0@\x1a\x12\t\xcd\xcc\xcc'
                        b'\xcc\xcc\xcc\xec?\x11\x00\x00\x00\x00\x00v\xb1@'
                        b'\x1a\x12\t\xaeG\xe1z\x14\xae\xef?\x11\x00\x00\x00'
                        b'\x00\x00\xa5\xb1@')

        f = BinaryFormatter()

        # Check multiple times to ensure multiple marshalling requests
        for i in range(format_times):
            self.assertEqual(valid_result, f.marshall(registry))
