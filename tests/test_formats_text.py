import re
import unittest

from aioprometheus import Collector, Counter, Gauge, Histogram, Summary, Registry
from aioprometheus.formats import TextFormatter, TEXT_CONTENT_TYPE


class TestTextFormat(unittest.TestCase):
    def test_headers(self):
        f = TextFormatter()
        expected_result = {"Content-Type": TEXT_CONTENT_TYPE}
        self.assertEqual(expected_result, f.get_headers())

    def test_wrong_format(self):
        self.data = {
            "name": "logged_users_total",
            "doc": "Logged users in the application",
            "const_labels": {"app": "my_app"},
        }

        f = TextFormatter()

        c = Collector(**self.data)

        with self.assertRaises(TypeError) as context:
            f.marshall_collector(c)

        self.assertEqual("Not a valid object format", str(context.exception))

    def test_counter_format(self):

        self.data = {
            "name": "logged_users_total",
            "doc": "Logged users in the application",
            "const_labels": None,
        }
        c = Counter(**self.data)

        counter_data = (
            ({"country": "sp", "device": "desktop"}, 520),
            ({"country": "us", "device": "mobile"}, 654),
            ({"country": "uk", "device": "desktop"}, 1001),
            ({"country": "de", "device": "desktop"}, 995),
            ({"country": "zh", "device": "desktop"}, 520),
            ({"country": "ch", "device": "mobile"}, 654),
            ({"country": "ca", "device": "desktop"}, 1001),
            ({"country": "jp", "device": "desktop"}, 995),
            ({"country": "au", "device": "desktop"}, 520),
            ({"country": "py", "device": "mobile"}, 654),
            ({"country": "ar", "device": "desktop"}, 1001),
            ({"country": "pt", "device": "desktop"}, 995),
        )

        valid_result = (
            "# HELP logged_users_total Logged users in the application",
            "# TYPE logged_users_total counter",
            'logged_users_total{country="ch",device="mobile"} 654',
            'logged_users_total{country="zh",device="desktop"} 520',
            'logged_users_total{country="jp",device="desktop"} 995',
            'logged_users_total{country="de",device="desktop"} 995',
            'logged_users_total{country="pt",device="desktop"} 995',
            'logged_users_total{country="ca",device="desktop"} 1001',
            'logged_users_total{country="sp",device="desktop"} 520',
            'logged_users_total{country="au",device="desktop"} 520',
            'logged_users_total{country="uk",device="desktop"} 1001',
            'logged_users_total{country="py",device="mobile"} 654',
            'logged_users_total{country="us",device="mobile"} 654',
            'logged_users_total{country="ar",device="desktop"} 1001',
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
            "name": "logged_users_total",
            "doc": "Logged users in the application",
            "const_labels": {"app": "my_app"},
        }
        c = Counter(**self.data)

        counter_data = (
            ({"country": "sp", "device": "desktop"}, 520),
            ({"country": "us", "device": "mobile"}, 654),
            ({"country": "uk", "device": "desktop"}, 1001),
            ({"country": "de", "device": "desktop"}, 995),
            ({"country": "zh", "device": "desktop"}, 520),
            ({"country": "ch", "device": "mobile"}, 654),
            ({"country": "ca", "device": "desktop"}, 1001),
            ({"country": "jp", "device": "desktop"}, 995),
            ({"country": "au", "device": "desktop"}, 520),
            ({"country": "py", "device": "mobile"}, 654),
            ({"country": "ar", "device": "desktop"}, 1001),
            ({"country": "pt", "device": "desktop"}, 995),
        )

        valid_result = (
            "# HELP logged_users_total Logged users in the application",
            "# TYPE logged_users_total counter",
            'logged_users_total{app="my_app",country="ch",device="mobile"} 654',
            'logged_users_total{app="my_app",country="zh",device="desktop"} 520',
            'logged_users_total{app="my_app",country="jp",device="desktop"} 995',
            'logged_users_total{app="my_app",country="de",device="desktop"} 995',
            'logged_users_total{app="my_app",country="pt",device="desktop"} 995',
            'logged_users_total{app="my_app",country="ca",device="desktop"} 1001',
            'logged_users_total{app="my_app",country="sp",device="desktop"} 520',
            'logged_users_total{app="my_app",country="au",device="desktop"} 520',
            'logged_users_total{app="my_app",country="uk",device="desktop"} 1001',
            'logged_users_total{app="my_app",country="py",device="mobile"} 654',
            'logged_users_total{app="my_app",country="us",device="mobile"} 654',
            'logged_users_total{app="my_app",country="ar",device="desktop"} 1001',
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
            (
                {
                    "id": "110863b5395f7f3476d44e7cb8799f2643abbd385dd544bcc379538ac6ffc5ca",
                    "name": "container-extractor",
                    "type": "kernel",
                },
                0,
            ),
            (
                {
                    "id": "110863b5395f7f3476d44e7cb8799f2643abbd385dd544bcc379538ac6ffc5ca",
                    "name": "container-extractor",
                    "type": "user",
                },
                0,
            ),
            (
                {
                    "id": "7c1ae8f404be413a6413d0792123092446f694887f52ae6403356215943d3c36",
                    "name": "calendall_db_1",
                    "type": "kernel",
                },
                0,
            ),
            (
                {
                    "id": "7c1ae8f404be413a6413d0792123092446f694887f52ae6403356215943d3c36",
                    "name": "calendall_db_1",
                    "type": "user",
                },
                0,
            ),
            (
                {
                    "id": "c863b092d1ecdc68f54a6a4ed0d24fe629696be2337ccafb44c279c7c2d1c172",
                    "name": "calendall_web_run_8",
                    "type": "kernel",
                },
                0,
            ),
            (
                {
                    "id": "c863b092d1ecdc68f54a6a4ed0d24fe629696be2337ccafb44c279c7c2d1c172",
                    "name": "calendall_web_run_8",
                    "type": "user",
                },
                0,
            ),
            (
                {
                    "id": "cefa0b389a634a0b2f3c2f52ade668d71de75e5775e91297bd65bebe745ba054",
                    "name": "prometheus",
                    "type": "kernel",
                },
                0,
            ),
            (
                {
                    "id": "cefa0b389a634a0b2f3c2f52ade668d71de75e5775e91297bd65bebe745ba054",
                    "name": "prometheus",
                    "type": "user",
                },
                0,
            ),
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
            "name": "logged_users_total",
            "doc": "Logged users in the application",
            "const_labels": {},
        }
        c = Counter(**self.data)

        counter_data = ({"country": "ch", "device": "mobile"}, 654)

        c.set_value(counter_data[0], counter_data[1])

        result_regex = r"""# HELP logged_users_total Logged users in the application
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

        data = ((None, 10),)

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
            "name": "logged_users_total",
            "doc": "Logged users in the application",
            "const_labels": {},
        }
        g = Gauge(**self.data)

        counter_data = (
            ({"country": "sp", "device": "desktop"}, 520),
            ({"country": "us", "device": "mobile"}, 654),
            ({"country": "uk", "device": "desktop"}, 1001),
            ({"country": "de", "device": "desktop"}, 995),
            ({"country": "zh", "device": "desktop"}, 520),
            ({"country": "ch", "device": "mobile"}, 654),
            ({"country": "ca", "device": "desktop"}, 1001),
            ({"country": "jp", "device": "desktop"}, 995),
            ({"country": "au", "device": "desktop"}, 520),
            ({"country": "py", "device": "mobile"}, 654),
            ({"country": "ar", "device": "desktop"}, 1001),
            ({"country": "pt", "device": "desktop"}, 995),
        )

        valid_result = (
            "# HELP logged_users_total Logged users in the application",
            "# TYPE logged_users_total gauge",
            'logged_users_total{country="ch",device="mobile"} 654',
            'logged_users_total{country="zh",device="desktop"} 520',
            'logged_users_total{country="jp",device="desktop"} 995',
            'logged_users_total{country="de",device="desktop"} 995',
            'logged_users_total{country="pt",device="desktop"} 995',
            'logged_users_total{country="ca",device="desktop"} 1001',
            'logged_users_total{country="sp",device="desktop"} 520',
            'logged_users_total{country="au",device="desktop"} 520',
            'logged_users_total{country="uk",device="desktop"} 1001',
            'logged_users_total{country="py",device="mobile"} 654',
            'logged_users_total{country="us",device="mobile"} 654',
            'logged_users_total{country="ar",device="desktop"} 1001',
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
            "name": "logged_users_total",
            "doc": "Logged users in the application",
            "const_labels": {"app": "my_app"},
        }
        g = Gauge(**self.data)

        counter_data = (
            ({"country": "sp", "device": "desktop"}, 520),
            ({"country": "us", "device": "mobile"}, 654),
            ({"country": "uk", "device": "desktop"}, 1001),
            ({"country": "de", "device": "desktop"}, 995),
            ({"country": "zh", "device": "desktop"}, 520),
            ({"country": "ch", "device": "mobile"}, 654),
            ({"country": "ca", "device": "desktop"}, 1001),
            ({"country": "jp", "device": "desktop"}, 995),
            ({"country": "au", "device": "desktop"}, 520),
            ({"country": "py", "device": "mobile"}, 654),
            ({"country": "ar", "device": "desktop"}, 1001),
            ({"country": "pt", "device": "desktop"}, 995),
        )

        valid_result = (
            "# HELP logged_users_total Logged users in the application",
            "# TYPE logged_users_total gauge",
            'logged_users_total{app="my_app",country="ch",device="mobile"} 654',
            'logged_users_total{app="my_app",country="zh",device="desktop"} 520',
            'logged_users_total{app="my_app",country="jp",device="desktop"} 995',
            'logged_users_total{app="my_app",country="de",device="desktop"} 995',
            'logged_users_total{app="my_app",country="pt",device="desktop"} 995',
            'logged_users_total{app="my_app",country="ca",device="desktop"} 1001',
            'logged_users_total{app="my_app",country="sp",device="desktop"} 520',
            'logged_users_total{app="my_app",country="au",device="desktop"} 520',
            'logged_users_total{app="my_app",country="uk",device="desktop"} 1001',
            'logged_users_total{app="my_app",country="py",device="mobile"} 654',
            'logged_users_total{app="my_app",country="us",device="mobile"} 654',
            'logged_users_total{app="my_app",country="ar",device="desktop"} 1001',
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
            (
                {
                    "id": "4f70875bb57986783064fe958f694c9e225643b0d18e9cde6bdee56d47b7ce76",
                    "name": "prometheus",
                },
                0,
            ),
            (
                {
                    "id": "89042838f24f0ec0aa2a6c93ff44fd3f3e43057d35cfd32de89558112ecb92a0",
                    "name": "calendall_web_run_3",
                },
                0,
            ),
            (
                {
                    "id": "d11c6bc95459822e995fac4d4ae527f6cac442a1896a771dbb307ba276beceb9",
                    "name": "db",
                },
                0,
            ),
            (
                {
                    "id": "e4260cc9dca3e4e50ad2bffb0ec7432442197f135023ab629fe3576485cc65dd",
                    "name": "container-extractor",
                },
                0,
            ),
            (
                {
                    "id": "f30d1caaa142b1688a0684ed744fcae6d202a36877617b985e20a5d33801b311",
                    "name": "calendall_db_1",
                },
                0,
            ),
            (
                {
                    "id": "f835d921ffaf332f8d88ef5231ba149e389a2f37276f081878d6f982ef89a981",
                    "name": "cocky_fermat",
                },
                0,
            ),
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
            "name": "logged_users_total",
            "doc": "Logged users in the application",
            "const_labels": {},
        }
        g = Gauge(**self.data)

        counter_data = ({"country": "ch", "device": "mobile"}, 654)

        g.set_value(counter_data[0], counter_data[1])

        result_regex = r"""# HELP logged_users_total Logged users in the application
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

        data = ((None, 16384),)

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
            "name": "logged_users_total",
            "doc": "Logged users in the application",
            "const_labels": {},
        }

        labels = {"handler": "/static"}
        values = [3, 5.2, 13, 4]

        valid_result = (
            "# HELP logged_users_total Logged users in the application",
            "# TYPE logged_users_total summary",
            'logged_users_total{handler="/static",quantile="0.5"} 4.0',
            'logged_users_total{handler="/static",quantile="0.9"} 5.2',
            'logged_users_total{handler="/static",quantile="0.99"} 5.2',
            'logged_users_total_count{handler="/static"} 4',
            'logged_users_total_sum{handler="/static"} 25.2',
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
            "name": "prometheus_target_interval_length_seconds",
            "doc": "Actual intervals between scrapes.",
            "const_labels": {},
        }

        labels = {"interval": "5s"}
        values = [3, 5.2, 13, 4]

        valid_result = """# HELP prometheus_target_interval_length_seconds Actual intervals between scrapes.
# TYPE prometheus_target_interval_length_seconds summary
prometheus_target_interval_length_seconds{interval="5s",quantile="0.5"} 4.0
prometheus_target_interval_length_seconds{interval="5s",quantile="0.9"} 5.2
prometheus_target_interval_length_seconds{interval="5s",quantile="0.99"} 5.2
prometheus_target_interval_length_seconds_count{interval="5s"} 4
prometheus_target_interval_length_seconds_sum{interval="5s"} 25.2"""

        s = Summary(**data)

        for i in values:
            s.add(labels, i)

        f = TextFormatter()
        result = f.marshall_collector(s)

        self.assertEqual(valid_result, result)

    def test_multiple_summary_format(self):
        data = {
            "name": "prometheus_target_interval_length_seconds",
            "doc": "Actual intervals between scrapes.",
            "const_labels": {},
        }

        summary_data = (
            ({"interval": "5s"}, [3, 5.2, 13, 4]),
            ({"interval": "10s"}, [1.3, 1.2, 32.1, 59.2, 109.46, 70.9]),
            ({"interval": "10s", "method": "fast"}, [5, 9.8, 31, 9.7, 101.4]),
        )

        valid_result = (
            "# HELP prometheus_target_interval_length_seconds Actual intervals between scrapes.",
            "# TYPE prometheus_target_interval_length_seconds summary",
            'prometheus_target_interval_length_seconds{interval="5s",quantile="0.5"} 4.0',
            'prometheus_target_interval_length_seconds{interval="5s",quantile="0.9"} 5.2',
            'prometheus_target_interval_length_seconds{interval="5s",quantile="0.99"} 5.2',
            'prometheus_target_interval_length_seconds_count{interval="5s"} 4',
            'prometheus_target_interval_length_seconds_sum{interval="5s"} 25.2',
            'prometheus_target_interval_length_seconds{interval="10s",quantile="0.5"} 32.1',
            'prometheus_target_interval_length_seconds{interval="10s",quantile="0.9"} 59.2',
            'prometheus_target_interval_length_seconds{interval="10s",quantile="0.99"} 59.2',
            'prometheus_target_interval_length_seconds_count{interval="10s"} 6',
            'prometheus_target_interval_length_seconds_sum{interval="10s"} 274.15999999999997',
            'prometheus_target_interval_length_seconds{interval="10s",method="fast",quantile="0.5"} 9.7',
            'prometheus_target_interval_length_seconds{interval="10s",method="fast",quantile="0.9"} 9.8',
            'prometheus_target_interval_length_seconds{interval="10s",method="fast",quantile="0.99"} 9.8',
            'prometheus_target_interval_length_seconds_count{interval="10s",method="fast"} 5',
            'prometheus_target_interval_length_seconds_sum{interval="10s",method="fast"} 156.9',
        )

        s = Summary(**data)

        for i in summary_data:
            for j in i[1]:
                s.add(i[0], j)

        f = TextFormatter()
        result = f.marshall_lines(s)

        self.assertEqual(sorted(valid_result), sorted(result))

    def test_single_summary_format(self):
        data = {
            "name": "logged_users_total",
            "doc": "Logged users in the application",
            "const_labels": {},
        }

        labels = {}  # This one hasn't got labels
        values = [3, 5.2, 13, 4]

        valid_result = (
            "# HELP logged_users_total Logged users in the application",
            "# TYPE logged_users_total summary",
            'logged_users_total{quantile="0.5"} 4.0',
            'logged_users_total{quantile="0.9"} 5.2',
            'logged_users_total{quantile="0.99"} 5.2',
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
            "name": "prometheus_target_interval_length_seconds",
            "doc": "Actual intervals between scrapes.",
            "const_labels": {},
        }

        labels = {"interval": "5s"}
        values = [3, 5.2, 13, 4]

        result_regex = r"""# HELP prometheus_target_interval_length_seconds Actual intervals between scrapes.
# TYPE prometheus_target_interval_length_seconds summary
prometheus_target_interval_length_seconds{interval="5s",quantile="0.5"} 4.0 \d*(?:.\d*)?
prometheus_target_interval_length_seconds{interval="5s",quantile="0.9"} 5.2 \d*(?:.\d*)?
prometheus_target_interval_length_seconds{interval="5s",quantile="0.99"} 5.2 \d*(?:.\d*)?
prometheus_target_interval_length_seconds_count{interval="5s"} 4 \d*(?:.\d*)?
prometheus_target_interval_length_seconds_sum{interval="5s"} 25.2 \d*(?:.\d*)?$"""

        s = Summary(**data)

        for i in values:
            s.add(labels, i)

        f = TextFormatter(True)
        result = f.marshall_collector(s)

        self.assertTrue(re.match(result_regex, result))

    def test_registry_marshall(self):

        format_times = 3

        counter_data = (
            ({"c_sample": "1"}, 100),
            ({"c_sample": "2"}, 200),
            ({"c_sample": "3"}, 300),
            ({"c_sample": "1", "c_subsample": "b"}, 400),
        )

        gauge_data = (
            ({"g_sample": "1"}, 500),
            ({"g_sample": "2"}, 600),
            ({"g_sample": "3"}, 700),
            ({"g_sample": "1", "g_subsample": "b"}, 800),
        )

        summary_data = (
            ({"s_sample": "1"}, range(1000, 2000, 4)),
            ({"s_sample": "2"}, range(2000, 3000, 20)),
            ({"s_sample": "3"}, range(3000, 4000, 13)),
            ({"s_sample": "1", "s_subsample": "b"}, range(4000, 5000, 47)),
        )

        registry = Registry()
        counter = Counter("counter_test", "A counter.", {"type": "counter"})
        gauge = Gauge("gauge_test", "A gauge.", {"type": "gauge"})
        summary = Summary("summary_test", "A summary.", {"type": "summary"})

        # Add data
        [counter.set(c[0], c[1]) for c in counter_data]
        [gauge.set(g[0], g[1]) for g in gauge_data]
        [summary.add(i[0], s) for i in summary_data for s in i[1]]

        registry.register(counter)
        registry.register(gauge)
        registry.register(summary)

        valid_regex = r"""# HELP counter_test A counter.
# TYPE counter_test counter
counter_test{c_sample="1",type="counter"} 100
counter_test{c_sample="2",type="counter"} 200
counter_test{c_sample="3",type="counter"} 300
counter_test{c_sample="1",c_subsample="b",type="counter"} 400
# HELP gauge_test A gauge.
# TYPE gauge_test gauge
gauge_test{g_sample="1",type="gauge"} 500
gauge_test{g_sample="2",type="gauge"} 600
gauge_test{g_sample="3",type="gauge"} 700
gauge_test{g_sample="1",g_subsample="b",type="gauge"} 800
# HELP summary_test A summary.
# TYPE summary_test summary
summary_test{quantile="0.5",s_sample="1",type="summary"} \d*(?:.\d*)?
summary_test{quantile="0.9",s_sample="1",type="summary"} \d*(?:.\d*)?
summary_test{quantile="0.99",s_sample="1",type="summary"} \d*(?:.\d*)?
summary_test_count{s_sample="1",type="summary"} \d*(?:.\d*)?
summary_test_sum{s_sample="1",type="summary"} \d*(?:.\d*)?
summary_test{quantile="0.5",s_sample="2",type="summary"} \d*(?:.\d*)?
summary_test{quantile="0.9",s_sample="2",type="summary"} 2\d*(?:.\d*)?
summary_test{quantile="0.99",s_sample="2",type="summary"} \d*(?:.\d*)?
summary_test_count{s_sample="2",type="summary"} \d*(?:.\d*)?
summary_test_sum{s_sample="2",type="summary"} \d*(?:.\d*)?
summary_test{quantile="0.5",s_sample="3",type="summary"} \d*(?:.\d*)?
summary_test{quantile="0.9",s_sample="3",type="summary"} \d*(?:.\d*)?
summary_test{quantile="0.99",s_sample="3",type="summary"} \d*(?:.\d*)?
summary_test_count{s_sample="3",type="summary"} \d*(?:.\d*)?
summary_test_sum{s_sample="3",type="summary"} \d*(?:.\d*)?
summary_test{quantile="0.5",s_sample="1",s_subsample="b",type="summary"} \d*(?:.\d*)?
summary_test{quantile="0.9",s_sample="1",s_subsample="b",type="summary"} \d*(?:.\d*)?
summary_test{quantile="0.99",s_sample="1",s_subsample="b",type="summary"} \d*(?:.\d*)?
summary_test_count{s_sample="1",s_subsample="b",type="summary"} \d*(?:.\d*)?
summary_test_sum{s_sample="1",s_subsample="b",type="summary"} \d*(?:.\d*)?
"""
        f = TextFormatter()
        self.maxDiff = None
        # Check multiple times to ensure multiple calls to marshalling
        # produce the same results
        for i in range(format_times):
            self.assertTrue(re.match(valid_regex, f.marshall(registry).decode()))
