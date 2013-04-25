'''
Check the performance counters from IIS
'''
from checks import AgentCheck

class IIS(AgentCheck):
    METRICS = [
        ('iis.uptime', 'gauge', 'ServiceUptime'),

        # Network
        ('iis.net.bytes_sent', 'rate', 'TotalBytesSent'),
        ('iis.net.bytes_rcvd', 'rate', 'TotalBytesReceived'),
        ('iis.net.bytes_total', 'rate', 'TotalBytesTransferred'),
        ('iis.net.num_connections', 'gauge', 'CurrentConnections'),
        ('iis.net.files_sent', 'rate', 'TotalFilesSent'),
        ('iis.net.files_rcvd', 'rate', 'TotalFilesReceived'),
        ('iis.net.connection_attempts', 'rate', 'TotalConnectionAttemptsAllInstances'),

        # HTTP Methods
        ('iis.httpd_request_method.get', 'rate', 'TotalGetRequests'),
        ('iis.httpd_request_method.post', 'rate', 'TotalPostRequests'),
        ('iis.httpd_request_method.head', 'rate', 'TotalHeadRequests'),
        ('iis.httpd_request_method.put', 'rate', 'TotalPutRequests'),
        ('iis.httpd_request_method.delete', 'rate', 'TotalDeleteRequests'),
        ('iis.httpd_request_method.options', 'rate', 'TotalOptionsRequests'),
        ('iis.httpd_request_method.trace', 'rate', 'TotalTraceRequests'),

        # Errors
        ('iis.errors.not_found', 'rate', 'TotalNotFoundErrors'),
        ('iis.errors.locked', 'rate', 'TotalLockedErrors'),

        # Users
        ('iis.users.anon', 'rate', 'TotalAnonymousUsers'),
        ('iis.users.nonanon', 'rate', 'TotalNonAnonymousUsers'),

        # Requests
        ('iis.requests.cgi', 'rate', 'TotalCGIRequests'),
        ('iis.requests.isapi', 'rate', 'TotalISAPIExtensionRequests'),
    ]

    def check(self, instance):
        try:
            import wmi
        except ImportError:
            self.log.error("Unable to import 'wmi' module")
            return

        # Connect to the WMI provider
        host = instance.get('host', None)
        user = instance.get('username', None)
        password = instance.get('password', None)
        instance_tags = instance.get('tags', [])
        w = wmi.WMI(host, user=user, password=password)

        try:
            wmi_cls = w.Win32_PerfFormattedData_W3SVC_WebService()
            if not wmi_cls:
                raise Exception('Missing data from Win32_PerfFormattedData_W3SVC_WebService')
        except Exception:
            self.log.exception('Unable to fetch Win32_PerfFormattedData_W3SVC_WebService class')
            return

        # Iterate over every IIS site
        for iis_site in wmi_cls:
            # Skip the aggregate value
            if iis_site.Name == '_Total':
                continue

            tags = instance_tags + ['site:%s' % iis_site.Name]
            for metric, mtype, wmi_val in self.METRICS:
                if not hasattr(iis_site, wmi_val):
                    self.log.error('Unable to fetch metric %s. Missing %s in Win32_PerfFormattedData_W3SVC_WebService' \
                        % (metric, wmi_val))
                    continue

                # Submit the metric value with the correct type
                value = float(getattr(iis_site, wmi_val))
                metric_func = getattr(self, mtype)
                metric_func(metric, value, tags=tags)
