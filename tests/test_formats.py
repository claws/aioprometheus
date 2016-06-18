import datetime
import re
import time
import unittest

from aioprometheus import (
    Collector, Counter, Gauge, Histogram, Summary,
    TextFormatter, BinaryFormatter,
    Registry)
import prometheus_metrics_proto as pmp


class TestTextFormat(unittest.TestCase):

    def test_headers(self):
        f = TextFormatter()
        result = {
            'Content-Type': 'text/plain; version=0.0.4; charset=utf-8'
        }

        self.assertEqual(result, f.get_headers())

    def test_wrong_format(self):
        self.data = {
            'name': "logged_users_total",
            'doc': "Logged users in the application",
            'const_labels': {"app": "my_app"},
        }

        f = TextFormatter()

        c = Collector(**self.data)

        with self.assertRaises(TypeError) as context:
            f.marshall_collector(c)

        self.assertEqual('Not a valid object format', str(context.exception))

    def test_counter_format(self):

        self.data = {
            'name': "logged_users_total",
            'doc': "Logged users in the application",
            'const_labels': None,
        }
        c = Counter(**self.data)

        counter_data = (
            ({'country': "sp", "device": "desktop"}, 520),
            ({'country': "us", "device": "mobile"}, 654),
            ({'country': "uk", "device": "desktop"}, 1001),
            ({'country': "de", "device": "desktop"}, 995),
            ({'country': "zh", "device": "desktop"}, 520),
            ({'country': "ch", "device": "mobile"}, 654),
            ({'country': "ca", "device": "desktop"}, 1001),
            ({'country': "jp", "device": "desktop"}, 995),
            ({'country': "au", "device": "desktop"}, 520),
            ({'country': "py", "device": "mobile"}, 654),
            ({'country': "ar", "device": "desktop"}, 1001),
            ({'country': "pt", "device": "desktop"}, 995),
        )

        valid_result = (
            "# HELP logged_users_total Logged users in the application",
            "# TYPE logged_users_total counter",
            "logged_users_total{country=\"ch\",device=\"mobile\"} 654",
            "logged_users_total{country=\"zh\",device=\"desktop\"} 520",
            "logged_users_total{country=\"jp\",device=\"desktop\"} 995",
            "logged_users_total{country=\"de\",device=\"desktop\"} 995",
            "logged_users_total{country=\"pt\",device=\"desktop\"} 995",
            "logged_users_total{country=\"ca\",device=\"desktop\"} 1001",
            "logged_users_total{country=\"sp\",device=\"desktop\"} 520",
            "logged_users_total{country=\"au\",device=\"desktop\"} 520",
            "logged_users_total{country=\"uk\",device=\"desktop\"} 1001",
            "logged_users_total{country=\"py\",device=\"mobile\"} 654",
            "logged_users_total{country=\"us\",device=\"mobile\"} 654",
            "logged_users_total{country=\"ar\",device=\"desktop\"} 1001",
        )

        # Add data to the collector
        for i in counter_data:
            c.set_value(i[0], i[1])

        # Select format
        f = TextFormatter()
        result = f.marshall_lines(c)

        result = sorted(result)
        valid_result = sorted(valid_result)

        self.assertEqual(valid_result, result)

    def test_counter_format_with_const_labels(self):

        self.data = {
            'name': "logged_users_total",
            'doc': "Logged users in the application",
            'const_labels': {"app": "my_app"},
        }
        c = Counter(**self.data)

        counter_data = (
            ({'country': "sp", "device": "desktop"}, 520),
            ({'country': "us", "device": "mobile"}, 654),
            ({'country': "uk", "device": "desktop"}, 1001),
            ({'country': "de", "device": "desktop"}, 995),
            ({'country': "zh", "device": "desktop"}, 520),
            ({'country': "ch", "device": "mobile"}, 654),
            ({'country': "ca", "device": "desktop"}, 1001),
            ({'country': "jp", "device": "desktop"}, 995),
            ({'country': "au", "device": "desktop"}, 520),
            ({'country': "py", "device": "mobile"}, 654),
            ({'country': "ar", "device": "desktop"}, 1001),
            ({'country': "pt", "device": "desktop"}, 995),
        )

        valid_result = (
            "# HELP logged_users_total Logged users in the application",
            "# TYPE logged_users_total counter",
            "logged_users_total{app=\"my_app\",country=\"ch\",device=\"mobile\"} 654",
            "logged_users_total{app=\"my_app\",country=\"zh\",device=\"desktop\"} 520",
            "logged_users_total{app=\"my_app\",country=\"jp\",device=\"desktop\"} 995",
            "logged_users_total{app=\"my_app\",country=\"de\",device=\"desktop\"} 995",
            "logged_users_total{app=\"my_app\",country=\"pt\",device=\"desktop\"} 995",
            "logged_users_total{app=\"my_app\",country=\"ca\",device=\"desktop\"} 1001",
            "logged_users_total{app=\"my_app\",country=\"sp\",device=\"desktop\"} 520",
            "logged_users_total{app=\"my_app\",country=\"au\",device=\"desktop\"} 520",
            "logged_users_total{app=\"my_app\",country=\"uk\",device=\"desktop\"} 1001",
            "logged_users_total{app=\"my_app\",country=\"py\",device=\"mobile\"} 654",
            "logged_users_total{app=\"my_app\",country=\"us\",device=\"mobile\"} 654",
            "logged_users_total{app=\"my_app\",country=\"ar\",device=\"desktop\"} 1001",
        )

        # Add data to the collector
        for i in counter_data:
            c.set_value(i[0], i[1])

        # Select format
        f = TextFormatter()
        result = f.marshall_lines(c)

        result = sorted(result)
        valid_result = sorted(valid_result)

        self.assertEqual(valid_result, result)

    def test_counter_format_text(self):

        name = "container_cpu_usage_seconds_total"
        doc = "Total seconds of cpu time consumed."

        valid_result = """# HELP container_cpu_usage_seconds_total Total seconds of cpu time consumed.
# TYPE container_cpu_usage_seconds_total counter
container_cpu_usage_seconds_total{id="110863b5395f7f3476d44e7cb8799f2643abbd385dd544bcc379538ac6ffc5ca",name="container-extractor",type="kernel"} 0
container_cpu_usage_seconds_total{id="110863b5395f7f3476d44e7cb8799f2643abbd385dd544bcc379538ac6ffc5ca",name="container-extractor",type="user"} 0
container_cpu_usage_seconds_total{id="7c1ae8f404be413a6413d0792123092446f694887f52ae6403356215943d3c36",name="calendall_db_1",type="kernel"} 0
container_cpu_usage_seconds_total{id="7c1ae8f404be413a6413d0792123092446f694887f52ae6403356215943d3c36",name="calendall_db_1",type="user"} 0
container_cpu_usage_seconds_total{id="c863b092d1ecdc68f54a6a4ed0d24fe629696be2337ccafb44c279c7c2d1c172",name="calendall_web_run_8",type="kernel"} 0
container_cpu_usage_seconds_total{id="c863b092d1ecdc68f54a6a4ed0d24fe629696be2337ccafb44c279c7c2d1c172",name="calendall_web_run_8",type="user"} 0
container_cpu_usage_seconds_total{id="cefa0b389a634a0b2f3c2f52ade668d71de75e5775e91297bd65bebe745ba054",name="prometheus",type="kernel"} 0
container_cpu_usage_seconds_total{id="cefa0b389a634a0b2f3c2f52ade668d71de75e5775e91297bd65bebe745ba054",name="prometheus",type="user"} 0"""

        data = (
            ({'id': "110863b5395f7f3476d44e7cb8799f2643abbd385dd544bcc379538ac6ffc5ca", 'name': "container-extractor", 'type': "kernel"}, 0),
            ({'id': "110863b5395f7f3476d44e7cb8799f2643abbd385dd544bcc379538ac6ffc5ca", 'name': "container-extractor", 'type': "user"}, 0),
            ({'id': "7c1ae8f404be413a6413d0792123092446f694887f52ae6403356215943d3c36", 'name': "calendall_db_1", 'type': "kernel"}, 0),
            ({'id': "7c1ae8f404be413a6413d0792123092446f694887f52ae6403356215943d3c36", 'name': "calendall_db_1", 'type': "user"}, 0),
            ({'id': "c863b092d1ecdc68f54a6a4ed0d24fe629696be2337ccafb44c279c7c2d1c172", 'name': "calendall_web_run_8", 'type': "kernel"}, 0),
            ({'id': "c863b092d1ecdc68f54a6a4ed0d24fe629696be2337ccafb44c279c7c2d1c172", 'name': "calendall_web_run_8", 'type': "user"}, 0),
            ({'id': "cefa0b389a634a0b2f3c2f52ade668d71de75e5775e91297bd65bebe745ba054", 'name': "prometheus", 'type': "kernel"}, 0),
            ({'id': "cefa0b389a634a0b2f3c2f52ade668d71de75e5775e91297bd65bebe745ba054", 'name': "prometheus", 'type': "user"}, 0),
        )

        # Create the counter
        c = Counter(name=name, doc=doc, const_labels={})

        for i in data:
            c.set_value(i[0], i[1])

        # Select format
        f = TextFormatter()

        result = f.marshall_collector(c)

        self.assertEqual(valid_result, result)

    def test_counter_format_with_timestamp(self):
        self.data = {
            'name': "logged_users_total",
            'doc': "Logged users in the application",
            'const_labels': {},
        }
        c = Counter(**self.data)

        counter_data = ({'country': "ch", "device": "mobile"}, 654)

        c.set_value(counter_data[0], counter_data[1])

        result_regex = """# HELP logged_users_total Logged users in the application
# TYPE logged_users_total counter
logged_users_total{country="ch",device="mobile"} 654 \d*(?:.\d*)?$"""

        f_with_ts = TextFormatter(True)
        result = f_with_ts.marshall_collector(c)

        self.assertTrue(re.match(result_regex, result))

    def test_single_counter_format_text(self):

        name = "prometheus_dns_sd_lookups_total"
        doc = "The number of DNS-SD lookups."

        valid_result = """# HELP prometheus_dns_sd_lookups_total The number of DNS-SD lookups.
# TYPE prometheus_dns_sd_lookups_total counter
prometheus_dns_sd_lookups_total 10"""

        data = (
            (None, 10),
        )

        # Create the counter
        c = Counter(name=name, doc=doc, const_labels={})

        for i in data:
            c.set_value(i[0], i[1])

        # Select format
        f = TextFormatter()

        result = f.marshall_collector(c)

        self.assertEqual(valid_result, result)

    def test_gauge_format(self):

        self.data = {
            'name': "logged_users_total",
            'doc': "Logged users in the application",
            'const_labels': {},
        }
        g = Gauge(**self.data)

        counter_data = (
            ({'country': "sp", "device": "desktop"}, 520),
            ({'country': "us", "device": "mobile"}, 654),
            ({'country': "uk", "device": "desktop"}, 1001),
            ({'country': "de", "device": "desktop"}, 995),
            ({'country': "zh", "device": "desktop"}, 520),
            ({'country': "ch", "device": "mobile"}, 654),
            ({'country': "ca", "device": "desktop"}, 1001),
            ({'country': "jp", "device": "desktop"}, 995),
            ({'country': "au", "device": "desktop"}, 520),
            ({'country': "py", "device": "mobile"}, 654),
            ({'country': "ar", "device": "desktop"}, 1001),
            ({'country': "pt", "device": "desktop"}, 995),
        )

        valid_result = (
            "# HELP logged_users_total Logged users in the application",
            "# TYPE logged_users_total gauge",
            "logged_users_total{country=\"ch\",device=\"mobile\"} 654",
            "logged_users_total{country=\"zh\",device=\"desktop\"} 520",
            "logged_users_total{country=\"jp\",device=\"desktop\"} 995",
            "logged_users_total{country=\"de\",device=\"desktop\"} 995",
            "logged_users_total{country=\"pt\",device=\"desktop\"} 995",
            "logged_users_total{country=\"ca\",device=\"desktop\"} 1001",
            "logged_users_total{country=\"sp\",device=\"desktop\"} 520",
            "logged_users_total{country=\"au\",device=\"desktop\"} 520",
            "logged_users_total{country=\"uk\",device=\"desktop\"} 1001",
            "logged_users_total{country=\"py\",device=\"mobile\"} 654",
            "logged_users_total{country=\"us\",device=\"mobile\"} 654",
            "logged_users_total{country=\"ar\",device=\"desktop\"} 1001",
        )

        # Add data to the collector
        for i in counter_data:
            g.set_value(i[0], i[1])

        # Select format
        f = TextFormatter()
        result = f.marshall_lines(g)

        result = sorted(result)
        valid_result = sorted(valid_result)

        self.assertEqual(valid_result, result)

    def test_gauge_format_with_const_labels(self):

        self.data = {
            'name': "logged_users_total",
            'doc': "Logged users in the application",
            'const_labels': {"app": "my_app"},
        }
        g = Gauge(**self.data)

        counter_data = (
            ({'country': "sp", "device": "desktop"}, 520),
            ({'country': "us", "device": "mobile"}, 654),
            ({'country': "uk", "device": "desktop"}, 1001),
            ({'country': "de", "device": "desktop"}, 995),
            ({'country': "zh", "device": "desktop"}, 520),
            ({'country': "ch", "device": "mobile"}, 654),
            ({'country': "ca", "device": "desktop"}, 1001),
            ({'country': "jp", "device": "desktop"}, 995),
            ({'country': "au", "device": "desktop"}, 520),
            ({'country': "py", "device": "mobile"}, 654),
            ({'country': "ar", "device": "desktop"}, 1001),
            ({'country': "pt", "device": "desktop"}, 995),
        )

        valid_result = (
            "# HELP logged_users_total Logged users in the application",
            "# TYPE logged_users_total gauge",
            "logged_users_total{app=\"my_app\",country=\"ch\",device=\"mobile\"} 654",
            "logged_users_total{app=\"my_app\",country=\"zh\",device=\"desktop\"} 520",
            "logged_users_total{app=\"my_app\",country=\"jp\",device=\"desktop\"} 995",
            "logged_users_total{app=\"my_app\",country=\"de\",device=\"desktop\"} 995",
            "logged_users_total{app=\"my_app\",country=\"pt\",device=\"desktop\"} 995",
            "logged_users_total{app=\"my_app\",country=\"ca\",device=\"desktop\"} 1001",
            "logged_users_total{app=\"my_app\",country=\"sp\",device=\"desktop\"} 520",
            "logged_users_total{app=\"my_app\",country=\"au\",device=\"desktop\"} 520",
            "logged_users_total{app=\"my_app\",country=\"uk\",device=\"desktop\"} 1001",
            "logged_users_total{app=\"my_app\",country=\"py\",device=\"mobile\"} 654",
            "logged_users_total{app=\"my_app\",country=\"us\",device=\"mobile\"} 654",
            "logged_users_total{app=\"my_app\",country=\"ar\",device=\"desktop\"} 1001",
        )

        # Add data to the collector
        for i in counter_data:
            g.set_value(i[0], i[1])

        # Select format
        f = TextFormatter()
        result = f.marshall_lines(g)

        result = sorted(result)
        valid_result = sorted(valid_result)

        self.assertEqual(valid_result, result)

    def test_gauge_format_text(self):

        name = "container_memory_max_usage_bytes"
        doc = "Maximum memory usage ever recorded in bytes."

        valid_result = """# HELP container_memory_max_usage_bytes Maximum memory usage ever recorded in bytes.
# TYPE container_memory_max_usage_bytes gauge
container_memory_max_usage_bytes{id="4f70875bb57986783064fe958f694c9e225643b0d18e9cde6bdee56d47b7ce76",name="prometheus"} 0
container_memory_max_usage_bytes{id="89042838f24f0ec0aa2a6c93ff44fd3f3e43057d35cfd32de89558112ecb92a0",name="calendall_web_run_3"} 0
container_memory_max_usage_bytes{id="d11c6bc95459822e995fac4d4ae527f6cac442a1896a771dbb307ba276beceb9",name="db"} 0
container_memory_max_usage_bytes{id="e4260cc9dca3e4e50ad2bffb0ec7432442197f135023ab629fe3576485cc65dd",name="container-extractor"} 0
container_memory_max_usage_bytes{id="f30d1caaa142b1688a0684ed744fcae6d202a36877617b985e20a5d33801b311",name="calendall_db_1"} 0
container_memory_max_usage_bytes{id="f835d921ffaf332f8d88ef5231ba149e389a2f37276f081878d6f982ef89a981",name="cocky_fermat"} 0"""

        data = (
            ({'id': "4f70875bb57986783064fe958f694c9e225643b0d18e9cde6bdee56d47b7ce76", 'name': "prometheus"}, 0),
            ({'id': "89042838f24f0ec0aa2a6c93ff44fd3f3e43057d35cfd32de89558112ecb92a0", 'name': "calendall_web_run_3"}, 0),
            ({'id': "d11c6bc95459822e995fac4d4ae527f6cac442a1896a771dbb307ba276beceb9", 'name': "db"}, 0),
            ({'id': "e4260cc9dca3e4e50ad2bffb0ec7432442197f135023ab629fe3576485cc65dd", 'name': "container-extractor"}, 0),
            ({'id': "f30d1caaa142b1688a0684ed744fcae6d202a36877617b985e20a5d33801b311", 'name': "calendall_db_1"}, 0),
            ({'id': "f835d921ffaf332f8d88ef5231ba149e389a2f37276f081878d6f982ef89a981", 'name': "cocky_fermat"}, 0),
        )

        # Create the counter
        g = Gauge(name=name, doc=doc, const_labels={})

        for i in data:
            g.set_value(i[0], i[1])

        # Select format
        f = TextFormatter()

        result = f.marshall_collector(g)

        self.assertEqual(valid_result, result)

    def test_gauge_format_with_timestamp(self):
        self.data = {
            'name': "logged_users_total",
            'doc': "Logged users in the application",
            'const_labels': {},
        }
        g = Gauge(**self.data)

        counter_data = ({'country': "ch", "device": "mobile"}, 654)

        g.set_value(counter_data[0], counter_data[1])

        result_regex = """# HELP logged_users_total Logged users in the application
# TYPE logged_users_total gauge
logged_users_total{country="ch",device="mobile"} 654 \d*(?:.\d*)?$"""

        f_with_ts = TextFormatter(True)
        result = f_with_ts.marshall_collector(g)

        self.assertTrue(re.match(result_regex, result))

    def test_single_gauge_format_text(self):

        name = "prometheus_local_storage_indexing_queue_capacity"
        doc = "The capacity of the indexing queue."

        valid_result = """# HELP prometheus_local_storage_indexing_queue_capacity The capacity of the indexing queue.
# TYPE prometheus_local_storage_indexing_queue_capacity gauge
prometheus_local_storage_indexing_queue_capacity 16384"""

        data = (
            (None, 16384),
        )

        # Create the counter
        g = Gauge(name=name, doc=doc, const_labels={})

        for i in data:
            g.set_value(i[0], i[1])

        # Select format
        f = TextFormatter()

        result = f.marshall_collector(g)

        self.assertEqual(valid_result, result)

    def test_one_summary_format(self):
        data = {
            'name': "logged_users_total",
            'doc': "Logged users in the application",
            'const_labels': {},
        }

        labels = {'handler': '/static'}
        values = [3, 5.2, 13, 4]

        valid_result = (
            "# HELP logged_users_total Logged users in the application",
            "# TYPE logged_users_total summary",
            "logged_users_total{handler=\"/static\",quantile=\"0.5\"} 4.0",
            "logged_users_total{handler=\"/static\",quantile=\"0.9\"} 5.2",
            "logged_users_total{handler=\"/static\",quantile=\"0.99\"} 5.2",
            "logged_users_total_count{handler=\"/static\"} 4",
            "logged_users_total_sum{handler=\"/static\"} 25.2",
        )

        s = Summary(**data)

        for i in values:
            s.add(labels, i)

        f = TextFormatter()
        result = f.marshall_lines(s)

        result = sorted(result)
        valid_result = sorted(valid_result)

        self.assertEqual(valid_result, result)

    def test_summary_format_text(self):
        data = {
            'name': "prometheus_target_interval_length_seconds",
            'doc': "Actual intervals between scrapes.",
            'const_labels': {},
        }

        labels = {'interval': '5s'}
        values = [3, 5.2, 13, 4]

        valid_result = """# HELP prometheus_target_interval_length_seconds Actual intervals between scrapes.
# TYPE prometheus_target_interval_length_seconds summary
prometheus_target_interval_length_seconds_count{interval="5s"} 4
prometheus_target_interval_length_seconds_sum{interval="5s"} 25.2
prometheus_target_interval_length_seconds{interval="5s",quantile="0.5"} 4.0
prometheus_target_interval_length_seconds{interval="5s",quantile="0.9"} 5.2
prometheus_target_interval_length_seconds{interval="5s",quantile="0.99"} 5.2"""

        s = Summary(**data)

        for i in values:
            s.add(labels, i)

        f = TextFormatter()
        result = f.marshall_collector(s)

        self.assertEqual(valid_result, result)

    def test_multiple_summary_format(self):
        data = {
            'name': "prometheus_target_interval_length_seconds",
            'doc': "Actual intervals between scrapes.",
            'const_labels': {},
        }

        summary_data = (
            ({'interval': "5s"}, [3, 5.2, 13, 4]),
            ({'interval': "10s"}, [1.3, 1.2, 32.1, 59.2, 109.46, 70.9]),
            ({'interval': "10s", 'method': "fast"}, [5, 9.8, 31, 9.7, 101.4]),
        )

        valid_result = (
            "# HELP prometheus_target_interval_length_seconds Actual intervals between scrapes.",
            "# TYPE prometheus_target_interval_length_seconds summary",
            "prometheus_target_interval_length_seconds{interval=\"5s\",quantile=\"0.5\"} 4.0",
            "prometheus_target_interval_length_seconds{interval=\"5s\",quantile=\"0.9\"} 5.2",
            "prometheus_target_interval_length_seconds{interval=\"5s\",quantile=\"0.99\"} 5.2",
            "prometheus_target_interval_length_seconds_count{interval=\"5s\"} 4",
            "prometheus_target_interval_length_seconds_sum{interval=\"5s\"} 25.2",
            "prometheus_target_interval_length_seconds{interval=\"10s\",quantile=\"0.5\"} 32.1",
            "prometheus_target_interval_length_seconds{interval=\"10s\",quantile=\"0.9\"} 59.2",
            "prometheus_target_interval_length_seconds{interval=\"10s\",quantile=\"0.99\"} 59.2",
            "prometheus_target_interval_length_seconds_count{interval=\"10s\"} 6",
            "prometheus_target_interval_length_seconds_sum{interval=\"10s\"} 274.15999999999997",
            "prometheus_target_interval_length_seconds{interval=\"10s\",method=\"fast\",quantile=\"0.5\"} 9.7",
            "prometheus_target_interval_length_seconds{interval=\"10s\",method=\"fast\",quantile=\"0.9\"} 9.8",
            "prometheus_target_interval_length_seconds{interval=\"10s\",method=\"fast\",quantile=\"0.99\"} 9.8",
            "prometheus_target_interval_length_seconds_count{interval=\"10s\",method=\"fast\"} 5",
            "prometheus_target_interval_length_seconds_sum{interval=\"10s\",method=\"fast\"} 156.9",
        )

        s = Summary(**data)

        for i in summary_data:
            for j in i[1]:
                s.add(i[0], j)

        f = TextFormatter()
        result = f.marshall_lines(s)

        self.assertEqual(sorted(valid_result), sorted(result))

#    # This one hans't got labels
    def test_single_summary_format(self):
        data = {
            'name': "logged_users_total",
            'doc': "Logged users in the application",
            'const_labels': {},
        }

        labels = {}
        values = [3, 5.2, 13, 4]

        valid_result = (
            "# HELP logged_users_total Logged users in the application",
            "# TYPE logged_users_total summary",
            "logged_users_total{quantile=\"0.5\"} 4.0",
            "logged_users_total{quantile=\"0.9\"} 5.2",
            "logged_users_total{quantile=\"0.99\"} 5.2",
            "logged_users_total_count 4",
            "logged_users_total_sum 25.2",
        )

        s = Summary(**data)

        for i in values:
            s.add(labels, i)

        f = TextFormatter()
        result = f.marshall_lines(s)

        result = sorted(result)
        valid_result = sorted(valid_result)

        self.assertEqual(valid_result, result)

    def test_summary_format_timestamp(self):
        data = {
            'name': "prometheus_target_interval_length_seconds",
            'doc': "Actual intervals between scrapes.",
            'const_labels': {},
        }

        labels = {'interval': '5s'}
        values = [3, 5.2, 13, 4]

        result_regex = """# HELP prometheus_target_interval_length_seconds Actual intervals between scrapes.
# TYPE prometheus_target_interval_length_seconds summary
prometheus_target_interval_length_seconds_count{interval="5s"} 4 \d*(?:.\d*)?
prometheus_target_interval_length_seconds_sum{interval="5s"} 25.2 \d*(?:.\d*)?
prometheus_target_interval_length_seconds{interval="5s",quantile="0.5"} 4.0 \d*(?:.\d*)?
prometheus_target_interval_length_seconds{interval="5s",quantile="0.9"} 5.2 \d*(?:.\d*)?
prometheus_target_interval_length_seconds{interval="5s",quantile="0.99"} 5.2 \d*(?:.\d*)?$"""

        s = Summary(**data)

        for i in values:
            s.add(labels, i)

        f = TextFormatter(True)
        result = f.marshall_collector(s)

        self.assertTrue(re.match(result_regex, result))

    def test_registry_marshall(self):

        format_times = 10

        counter_data = (
            ({'c_sample': '1'}, 100),
            ({'c_sample': '2'}, 200),
            ({'c_sample': '3'}, 300),
            ({'c_sample': '1', 'c_subsample': 'b'}, 400),
        )

        gauge_data = (
            ({'g_sample': '1'}, 500),
            ({'g_sample': '2'}, 600),
            ({'g_sample': '3'}, 700),
            ({'g_sample': '1', 'g_subsample': 'b'}, 800),
        )

        summary_data = (
            ({'s_sample': '1'}, range(1000, 2000, 4)),
            ({'s_sample': '2'}, range(2000, 3000, 20)),
            ({'s_sample': '3'}, range(3000, 4000, 13)),
            ({'s_sample': '1', 's_subsample': 'b'}, range(4000, 5000, 47)),
        )

        registry = Registry()
        counter = Counter("counter_test", "A counter.", {'type': "counter"})
        gauge = Gauge("gauge_test", "A gauge.", {'type': "gauge"})
        summary = Summary("summary_test", "A summary.", {'type': "summary"})

        # Add data
        [counter.set(c[0], c[1]) for c in counter_data]
        [gauge.set(g[0], g[1]) for g in gauge_data]
        [summary.add(i[0], s) for i in summary_data for s in i[1]]

        registry.register(counter)
        registry.register(gauge)
        registry.register(summary)

        valid_regex = """# HELP counter_test A counter.
# TYPE counter_test counter
counter_test{c_sample="1",c_subsample="b",type="counter"} 400
counter_test{c_sample="1",type="counter"} 100
counter_test{c_sample="2",type="counter"} 200
counter_test{c_sample="3",type="counter"} 300
# HELP gauge_test A gauge.
# TYPE gauge_test gauge
gauge_test{g_sample="1",g_subsample="b",type="gauge"} 800
gauge_test{g_sample="1",type="gauge"} 500
gauge_test{g_sample="2",type="gauge"} 600
gauge_test{g_sample="3",type="gauge"} 700
# HELP summary_test A summary.
# TYPE summary_test summary
summary_test_count{s_sample="1",s_subsample="b",type="summary"} \d*(?:.\d*)?
summary_test_count{s_sample="1",type="summary"} \d*(?:.\d*)?
summary_test_count{s_sample="2",type="summary"} \d*(?:.\d*)?
summary_test_count{s_sample="3",type="summary"} \d*(?:.\d*)?
summary_test_sum{s_sample="1",s_subsample="b",type="summary"} \d*(?:.\d*)?
summary_test_sum{s_sample="1",type="summary"} \d*(?:.\d*)?
summary_test_sum{s_sample="2",type="summary"} \d*(?:.\d*)?
summary_test_sum{s_sample="3",type="summary"} \d*(?:.\d*)?
summary_test{quantile="0.5",s_sample="1",s_subsample="b",type="summary"} \d*(?:.\d*)?
summary_test{quantile="0.5",s_sample="1",type="summary"} \d*(?:.\d*)?
summary_test{quantile="0.5",s_sample="2",type="summary"} \d*(?:.\d*)?
summary_test{quantile="0.5",s_sample="3",type="summary"} \d*(?:.\d*)?
summary_test{quantile="0.9",s_sample="1",s_subsample="b",type="summary"} \d*(?:.\d*)?
summary_test{quantile="0.9",s_sample="1",type="summary"} \d*(?:.\d*)?
summary_test{quantile="0.9",s_sample="2",type="summary"} 2\d*(?:.\d*)?
summary_test{quantile="0.9",s_sample="3",type="summary"} \d*(?:.\d*)?
summary_test{quantile="0.99",s_sample="1",s_subsample="b",type="summary"} \d*(?:.\d*)?
summary_test{quantile="0.99",s_sample="1",type="summary"} \d*(?:.\d*)?
summary_test{quantile="0.99",s_sample="2",type="summary"} \d*(?:.\d*)?
summary_test{quantile="0.99",s_sample="3",type="summary"} \d*(?:.\d*)?
"""
        f = TextFormatter()
        self.maxDiff = None
        # Check multiple times to ensure multiple marshalling requests
        for i in range(format_times):
            self.assertTrue(re.match(valid_regex, f.marshall(registry).decode()))


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

    def test_test_timestamp(self):
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

    def test_test_protobuf_metric_equal_not_metric(self):
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

    def test_test_protobuf_metric_equal_not_basic_data(self):
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

    def test_test_protobuf_metric_equal_not_labels(self):
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

    def test_test_protobuf_metric_equal_counter(self):
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

    def test_test_protobuf_metric_equal_gauge(self):
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

    def test_test_protobuf_metric_equal_summary(self):
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
